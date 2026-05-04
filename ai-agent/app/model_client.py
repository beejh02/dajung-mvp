from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from config import AgentSettings


ALLOWED_ACTIONS = {
    "get_menu",
    "get_user_context",
    "create_order_draft",
    "confirm_order",
    "get_receipt",
    "get_points_balance",
    "ask_clarification",
    "unavailable_menu",
}


class IntentValidationError(ValueError):
    pass


class ProviderConfigurationError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMIntent:
    action: str
    payload: dict[str, Any]
    message: str


class LLMProvider(ABC):
    provider_name: str

    def __init__(self, target_model_id: str) -> None:
        self.target_model_id = target_model_id

    @abstractmethod
    def generate_response(self, user_message: str, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


def validate_intent(raw_intent: Any) -> LLMIntent:
    if not isinstance(raw_intent, dict):
        raise IntentValidationError("intent JSON은 객체여야 합니다.")

    action = raw_intent.get("action")
    payload = raw_intent.get("payload", {})
    message = raw_intent.get("message", "")

    if not isinstance(action, str) or action not in ALLOWED_ACTIONS:
        raise IntentValidationError("지원하지 않는 intent action입니다.")
    if not isinstance(payload, dict):
        raise IntentValidationError("intent payload는 객체여야 합니다.")
    if not isinstance(message, str):
        raise IntentValidationError("intent message는 문자열이어야 합니다.")

    return LLMIntent(action=action, payload=payload, message=message)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value.lower())


def _extract_quantity(message: str) -> int | None:
    match = re.search(r"(\d+)\s*(개|세트|잔|)", message)
    if match:
        return max(int(match.group(1)), 1)

    korean_numbers = {
        "한": 1,
        "하나": 1,
        "두": 2,
        "둘": 2,
        "세": 3,
        "셋": 3,
        "네": 4,
        "넷": 4,
    }
    for token, value in korean_numbers.items():
        if token in message:
            return value
    return None


def _available_menu_items(menu_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in menu_items if item.get("is_available", True)]


def _find_requested_menu(message: str, menu_items: list[dict[str, Any]]) -> dict[str, Any] | None:
    normalized_message = _normalize(message)
    for item in sorted(menu_items, key=lambda entry: len(str(entry.get("name", ""))), reverse=True):
        name = str(item.get("name", ""))
        if name and _normalize(name) in normalized_message:
            return item
    return None


def _menu_by_id(menu_items: list[dict[str, Any]], menu_item_id: str | None) -> dict[str, Any] | None:
    if not menu_item_id:
        return None
    for item in menu_items:
        if str(item.get("id")) == str(menu_item_id):
            return item
    return None


def _selected_option_map(selected_options: list[dict[str, Any]]) -> dict[str, list[str]]:
    selected: dict[str, list[str]] = {}
    for group_selection in selected_options:
        group_id = group_selection.get("group_id")
        choice_ids = group_selection.get("choice_ids", [])
        if isinstance(group_id, str) and isinstance(choice_ids, list):
            selected[group_id] = [str(choice_id) for choice_id in choice_ids]
    return selected


def _option_group_payload(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "group_id": group.get("id"),
            "name": group.get("name"),
            "min_select": group.get("min_select", 1),
            "max_select": group.get("max_select", 1),
            "choices": [
                {
                    "id": choice.get("id"),
                    "name": choice.get("name"),
                    "price_delta": choice.get("price_delta", 0),
                    "is_available": choice.get("is_available", True),
                }
                for choice in group.get("choices", [])
                if choice.get("is_available", True)
            ],
        }
        for group in groups
    ]


def _pending_order_item_payload(
    menu_item: dict[str, Any],
    quantity: int | None,
    selected_options: list[dict[str, Any]],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "menu_item_id": menu_item.get("id"),
        "menu_name": menu_item.get("name"),
        "selected_options": selected_options,
    }
    if quantity is not None:
        payload["quantity"] = quantity
    return payload


def _selected_options_for_message(
    message: str,
    menu_item: dict[str, Any],
    existing_options: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
    normalized_message = _normalize(message)
    selected = _selected_option_map(existing_options or [])
    missing_required_groups: list[dict[str, Any]] = []

    for group in menu_item.get("options", []):
        group_id = str(group["id"])
        max_select = int(group.get("max_select", 1) or 1)
        choices = sorted(
            list(group.get("choices", [])),
            key=lambda choice: len(str(choice.get("name", ""))),
            reverse=True,
        )
        matched_choice_ids: list[str] = []

        for choice in choices:
            choice_name = str(choice.get("name", ""))
            if choice_name and _normalize(choice_name) in normalized_message:
                if not choice.get("is_available", True):
                    return [], [], choice_name
                matched_choice_ids.append(str(choice["id"]))
                if max_select == 1:
                    break

        if matched_choice_ids:
            existing_choice_ids = [] if max_select == 1 else selected.get(group_id, [])
            merged_choice_ids = list(dict.fromkeys([*existing_choice_ids, *matched_choice_ids]))
            selected[group_id] = merged_choice_ids[:max_select]

        choice_count = len(selected.get(group_id, []))
        min_select = int(group.get("min_select", 0) or 0)
        if group.get("required", False) and choice_count < max(min_select, 1):
            missing_required_groups.append(group)

    selected_options = [
        {"group_id": group_id, "choice_ids": choice_ids}
        for group_id, choice_ids in selected.items()
        if choice_ids
    ]
    return selected_options, missing_required_groups, None


def _suggestion_payload(menu_items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "alternatives": [
            {"id": item.get("id"), "name": item.get("name"), "price": item.get("price")}
            for item in _available_menu_items(menu_items)[:3]
        ]
    }


class StubLLMProvider(LLMProvider):
    provider_name = "StubLLMProvider"

    def _clarify_quantity_intent(
        self,
        menu_item: dict[str, Any],
        selected_options: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "action": "ask_clarification",
            "payload": {
                "reason": "missing_quantity",
                "menu_name": menu_item.get("name"),
                "pending_order_item": _pending_order_item_payload(menu_item, None, selected_options or []),
            },
            "message": "수량을 확인해야 합니다.",
        }

    def _clarify_options_intent(
        self,
        menu_item: dict[str, Any],
        quantity: int,
        selected_options: list[dict[str, Any]],
        missing_groups: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "action": "ask_clarification",
            "payload": {
                "reason": "missing_options",
                "menu_name": menu_item.get("name"),
                "pending_order_item": _pending_order_item_payload(menu_item, quantity, selected_options),
                "missing_option_groups": _option_group_payload(missing_groups),
            },
            "message": "필수 옵션을 확인해야 합니다.",
        }

    def _draft_or_clarification_intent(
        self,
        message: str,
        menu_item: dict[str, Any],
        quantity: int | None,
        selected_options: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if quantity is None:
            return self._clarify_quantity_intent(menu_item, selected_options)

        selected_options, missing_groups, unavailable_option_name = _selected_options_for_message(
            message,
            menu_item,
            selected_options,
        )
        if unavailable_option_name:
            return {
                "action": "unavailable_menu",
                "payload": {
                    "requested_name": f"{menu_item.get('name')}의 {unavailable_option_name}",
                    **_suggestion_payload([menu_item]),
                },
                "message": "비활성 옵션이 요청되었습니다.",
            }

        if missing_groups:
            return self._clarify_options_intent(menu_item, quantity, selected_options, missing_groups)

        return {
            "action": "create_order_draft",
            "payload": {
                "items": [
                    {
                        "menu_item_id": menu_item["id"],
                        "quantity": quantity,
                        "selected_options": selected_options,
                    }
                ]
            },
            "message": "주문 초안을 생성합니다.",
        }

    def _intent_from_pending_order(
        self,
        message: str,
        pending_order_request: dict[str, Any],
        menu_items: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        menu_item = _menu_by_id(menu_items, str(pending_order_request.get("menu_item_id", "")))
        if menu_item is None:
            return None

        quantity = pending_order_request.get("quantity")
        if not isinstance(quantity, int):
            quantity = None

        parsed_quantity = _extract_quantity(message)
        if parsed_quantity is not None:
            quantity = parsed_quantity

        selected_options = list(pending_order_request.get("selected_options", []))
        return self._draft_or_clarification_intent(message, menu_item, quantity, selected_options)

    def generate_response(self, user_message: str, context: dict[str, Any]) -> dict[str, Any]:
        message = user_message.strip()
        menu_items = list(context.get("menu_items", []))

        if "깨진" in message or "잘못된 json" in message.lower() or "invalid" in message.lower():
            return {"payload": {"raw": message}}

        if any(token in message for token in ["확정", "결제", "진행", "좋아요", "좋아"]):
            if context.get("has_pending_draft"):
                return {
                    "action": "confirm_order",
                    "payload": {},
                    "message": "사용자가 결제 전 주문 확인을 완료했습니다.",
                }
            return {
                "action": "ask_clarification",
                "payload": {},
                "message": "확정할 주문 초안이 없습니다.",
            }

        if any(token in message for token in ["포인트", "적립", "잔액"]):
            return {"action": "get_points_balance", "payload": {}, "message": "포인트 잔액을 조회합니다."}

        if "영수증" in message:
            order_id_match = re.search(r"(\d+)", message)
            return {
                "action": "get_receipt",
                "payload": {"order_id": int(order_id_match.group(1))} if order_id_match else {},
                "message": "영수증을 조회합니다.",
            }

        if any(token in message for token in ["내 정보", "내 주문", "사용자", "컨텍스트", "추천"]):
            return {"action": "get_user_context", "payload": {}, "message": "사용자 컨텍스트를 조회합니다."}

        if any(token in message for token in ["메뉴", "목록", "뭐 있어", "뭐있어"]):
            return {"action": "get_menu", "payload": {}, "message": "메뉴를 조회합니다."}

        requested_menu = _find_requested_menu(message, menu_items)
        pending_order_request = context.get("pending_order_request")
        if requested_menu is None and isinstance(pending_order_request, dict):
            pending_intent = self._intent_from_pending_order(message, pending_order_request, menu_items)
            if pending_intent is not None:
                return pending_intent

        if requested_menu is None:
            if any(token in message for token in ["주문", "주세요", "줘", "먹고", "버거", "세트"]):
                return {
                    "action": "ask_clarification",
                    "payload": _suggestion_payload(menu_items),
                    "message": "메뉴명을 특정하지 못했습니다.",
                }
            return {
                "action": "ask_clarification",
                "payload": {},
                "message": "주문 의도를 더 구체적으로 확인해야 합니다.",
            }

        if not requested_menu.get("is_available", True):
            return {
                "action": "unavailable_menu",
                "payload": {
                    "requested_name": requested_menu.get("name"),
                    **_suggestion_payload(menu_items),
                },
                "message": "비활성 메뉴가 요청되었습니다.",
            }

        return self._draft_or_clarification_intent(message, requested_menu, _extract_quantity(message))


class GoogleGeminiProvider(LLMProvider):
    provider_name = "GoogleGeminiProvider"

    def __init__(self, target_model_id: str, api_key: str | None) -> None:
        super().__init__(target_model_id)
        if not api_key:
            raise ProviderConfigurationError("Google Gemini API Key가 설정되지 않았습니다.")
        self.api_key = api_key

    def generate_response(self, user_message: str, context: dict[str, Any]) -> dict[str, Any]:
        model_id = self.target_model_id
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"{quote(model_id, safe='/')}:generateContent?key={quote(self.api_key)}"
        )
        prompt = {
            "instruction": (
                "너는 햄버거 주문 Agent의 intent JSON 생성기다. "
                "반드시 JSON 객체만 반환한다. 지원 action은 get_menu, get_user_context, "
                "create_order_draft, confirm_order, get_receipt, get_points_balance, "
                "ask_clarification, unavailable_menu 중 하나다. 주문 저장과 결제는 하지 않는다."
            ),
            "user_message": user_message,
            "context": {
                "menu_items": context.get("menu_items", []),
                "has_pending_draft": context.get("has_pending_draft", False),
                "pending_order_request": context.get("pending_order_request"),
                "last_order_id": context.get("last_order_id"),
            },
            "schema_hint": {
                "action": "create_order_draft",
                "payload": {
                    "items": [
                        {
                            "menu_item_id": "메뉴 id",
                            "quantity": 1,
                            "selected_options": [{"group_id": "옵션 그룹 id", "choice_ids": ["옵션 id"]}],
                        }
                    ]
                },
                "message": "한국어 처리 설명",
            },
        }
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": json.dumps(prompt, ensure_ascii=False)}],
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        request = Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise LLMProviderError(f"Gemini API 오류가 발생했습니다. 상태 코드: {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise LLMProviderError("Gemini API에 연결할 수 없습니다.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise LLMProviderError("Gemini API 응답을 해석하지 못했습니다.") from exc

        try:
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Gemini API 응답에 intent JSON이 없습니다.") from exc

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match is None:
                raise LLMProviderError("Gemini API가 JSON이 아닌 응답을 반환했습니다.")
            return json.loads(match.group(0))


class CloudflareWorkersAIProvider(LLMProvider):
    provider_name = "CloudflareWorkersAIProvider"

    def __init__(
        self,
        target_model_id: str,
        account_id: str | None,
        api_token: str | None,
        model_id: str | None,
    ) -> None:
        super().__init__(target_model_id)
        if not account_id or not api_token:
            raise ProviderConfigurationError("Cloudflare Workers AI 계정 또는 토큰이 설정되지 않았습니다.")
        self.account_id = account_id
        self.api_token = api_token
        self.model_id = model_id or target_model_id

    def generate_response(self, user_message: str, context: dict[str, Any]) -> dict[str, Any]:
        raise ProviderConfigurationError("Cloudflare Workers AI Provider는 교체 지점만 준비되어 있습니다.")


def create_llm_provider(settings: AgentSettings) -> tuple[LLMProvider, str | None]:
    if settings.llm_provider in {"stub", "demo", "placeholder"}:
        return StubLLMProvider(settings.target_model_id), None

    try:
        if settings.llm_provider in {"google", "gemini", "google_gemini"}:
            return GoogleGeminiProvider(settings.target_model_id, settings.google_gemini_api_key), None
        if settings.llm_provider in {"cloudflare", "workers_ai", "cloudflare_workers_ai"}:
            return CloudflareWorkersAIProvider(
                settings.target_model_id,
                settings.cloudflare_account_id,
                settings.cloudflare_api_token,
                settings.cloudflare_model_id,
            ), None
    except ProviderConfigurationError as exc:
        if settings.demo_mode:
            return StubLLMProvider(settings.target_model_id), f"{exc} demo mode로 StubLLMProvider를 사용합니다."
        raise

    if settings.demo_mode:
        return StubLLMProvider(settings.target_model_id), "알 수 없는 provider 설정이라 demo mode로 StubLLMProvider를 사용합니다."
    raise ProviderConfigurationError(f"지원하지 않는 LLM_PROVIDER입니다: {settings.llm_provider}")

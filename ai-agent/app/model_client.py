from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from typing import Any

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


def _extract_quantity(message: str) -> int:
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
    return 1


def _available_menu_items(menu_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in menu_items if item.get("is_available", True)]


def _find_requested_menu(message: str, menu_items: list[dict[str, Any]]) -> dict[str, Any] | None:
    normalized_message = _normalize(message)
    for item in sorted(menu_items, key=lambda entry: len(str(entry.get("name", ""))), reverse=True):
        name = str(item.get("name", ""))
        if name and _normalize(name) in normalized_message:
            return item
    return None


def _first_available_choice(choices: list[dict[str, Any]]) -> dict[str, Any] | None:
    for choice in choices:
        if choice.get("is_available", True):
            return choice
    return None


def _selected_options_for_message(message: str, menu_item: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    normalized_message = _normalize(message)
    selected_options: list[dict[str, Any]] = []

    for group in menu_item.get("options", []):
        choices = list(group.get("choices", []))
        selected_choice_ids: list[str] = []

        for choice in choices:
            choice_name = str(choice.get("name", ""))
            if choice_name and _normalize(choice_name) in normalized_message:
                if not choice.get("is_available", True):
                    return [], choice_name
                selected_choice_ids.append(str(choice["id"]))

        if not selected_choice_ids and group.get("required", False):
            choice = _first_available_choice(choices)
            if choice is not None:
                selected_choice_ids.append(str(choice["id"]))
            else:
                return [], str(group.get("name", "필수 옵션"))

        if selected_choice_ids:
            selected_options.append(
                {
                    "group_id": str(group["id"]),
                    "choice_ids": selected_choice_ids[: int(group.get("max_select", 1) or 1)],
                }
            )

    return selected_options, None


def _suggestion_payload(menu_items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "alternatives": [
            {"id": item.get("id"), "name": item.get("name"), "price": item.get("price")}
            for item in _available_menu_items(menu_items)[:3]
        ]
    }


class StubLLMProvider(LLMProvider):
    provider_name = "StubLLMProvider"

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

        selected_options, unavailable_option_name = _selected_options_for_message(message, requested_menu)
        if unavailable_option_name:
            return {
                "action": "unavailable_menu",
                "payload": {
                    "requested_name": f"{requested_menu.get('name')}의 {unavailable_option_name}",
                    **_suggestion_payload(menu_items),
                },
                "message": "비활성 옵션이 요청되었습니다.",
            }

        return {
            "action": "create_order_draft",
            "payload": {
                "items": [
                    {
                        "menu_item_id": requested_menu["id"],
                        "quantity": _extract_quantity(message),
                        "selected_options": selected_options,
                    }
                ]
            },
            "message": "주문 초안을 생성합니다.",
        }


class GoogleGeminiProvider(LLMProvider):
    provider_name = "GoogleGeminiProvider"

    def __init__(self, target_model_id: str, api_key: str | None) -> None:
        super().__init__(target_model_id)
        if not api_key:
            raise ProviderConfigurationError("Google Gemini API Key가 설정되지 않았습니다.")
        self.api_key = api_key

    def generate_response(self, user_message: str, context: dict[str, Any]) -> dict[str, Any]:
        raise ProviderConfigurationError("Google Gemini Provider는 교체 지점만 준비되어 있습니다.")


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

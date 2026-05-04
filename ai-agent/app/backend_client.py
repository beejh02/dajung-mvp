from dataclasses import dataclass
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class BackendApiError(RuntimeError):
    def __init__(self, status_code: int | None, detail: Any, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class AgentSession:
    access_token: str
    token_type: str
    expires_in: int
    token_use: str
    user: dict[str, Any]


def _extract_detail_message(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        messages = [entry.get("msg") for entry in detail if isinstance(entry, dict) and isinstance(entry.get("msg"), str)]
        if messages:
            return ", ".join(messages)
    if isinstance(detail, dict):
        message = detail.get("message")
        if isinstance(message, str):
            return message
    return "백엔드 요청을 처리하지 못했습니다."


class BackendClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> JsonValue:
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload = response.read()
                if not payload:
                    return None
                return json.loads(payload.decode("utf-8"))
        except HTTPError as exc:
            detail: Any
            try:
                problem = json.loads(exc.read().decode("utf-8"))
                detail = problem.get("detail", problem) if isinstance(problem, dict) else problem
            except (json.JSONDecodeError, UnicodeDecodeError):
                detail = exc.reason
            raise BackendApiError(exc.code, detail, _extract_detail_message(detail)) from exc
        except URLError as exc:
            raise BackendApiError(None, str(exc.reason), "백엔드 서버에 연결할 수 없습니다.") from exc

    def exchange_agent_session(self, handoff_token: str) -> AgentSession:
        payload = self._request("POST", "/auth/agent-session", body={"handoff_token": handoff_token})
        if not isinstance(payload, dict):
            raise BackendApiError(None, payload, "Agent 세션 응답이 올바르지 않습니다.")
        return AgentSession(
            access_token=str(payload["access_token"]),
            token_type=str(payload["token_type"]),
            expires_in=int(payload["expires_in"]),
            token_use=str(payload["token_use"]),
            user=dict(payload["user"]),
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        payload = self._request("POST", "/auth/login", body={"email": email, "password": password})
        if not isinstance(payload, dict):
            raise BackendApiError(None, payload, "로그인 응답이 올바르지 않습니다.")
        return payload

    def create_agent_handoff(self, access_token: str) -> str:
        payload = self._request("POST", "/auth/agent-handoff", access_token=access_token)
        if not isinstance(payload, dict) or not payload.get("handoff_token"):
            raise BackendApiError(None, payload, "handoff token 응답이 올바르지 않습니다.")
        return str(payload["handoff_token"])

    def create_agent_session_from_access_token(self, access_token: str) -> AgentSession:
        handoff_token = self.create_agent_handoff(access_token)
        return self.exchange_agent_session(handoff_token)

    def get_me(self, access_token: str) -> dict[str, Any]:
        payload = self._request("GET", "/auth/me", access_token=access_token)
        return dict(payload) if isinstance(payload, dict) else {}

    def session_from_bearer_token(self, access_token: str) -> AgentSession:
        try:
            return self.create_agent_session_from_access_token(access_token)
        except BackendApiError:
            user = self.get_me(access_token)
            return AgentSession(
                access_token=access_token,
                token_type="bearer",
                expires_in=0,
                token_use="manual",
                user=user,
            )

    def get_agent_menu(self, access_token: str) -> dict[str, Any]:
        payload = self._request("GET", "/agent/menu", access_token=access_token)
        return dict(payload) if isinstance(payload, dict) else {"items": []}

    def get_user_context(self, access_token: str) -> dict[str, Any]:
        payload = self._request("GET", "/agent/user-context", access_token=access_token)
        return dict(payload) if isinstance(payload, dict) else {}

    def create_order_draft(self, access_token: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        payload = self._request("POST", "/agent/orders/draft", access_token=access_token, body={"items": items})
        return dict(payload) if isinstance(payload, dict) else {}

    def confirm_order(self, access_token: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        payload = self._request("POST", "/agent/orders/confirm", access_token=access_token, body={"items": items})
        return dict(payload) if isinstance(payload, dict) else {}

    def approve_dummy_payment(self, access_token: str, order_id: int, idempotency_key: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            "/agent/payments/dummy/approve",
            access_token=access_token,
            body={"order_id": order_id, "idempotency_key": idempotency_key},
        )
        return dict(payload) if isinstance(payload, dict) else {}

    def get_order_receipt(self, access_token: str, order_id: int) -> dict[str, Any]:
        payload = self._request("GET", f"/orders/{order_id}/receipt", access_token=access_token)
        return dict(payload) if isinstance(payload, dict) else {}

    def get_points_balance(self, access_token: str) -> dict[str, Any]:
        payload = self._request("GET", "/points/me", access_token=access_token)
        return dict(payload) if isinstance(payload, dict) else {}

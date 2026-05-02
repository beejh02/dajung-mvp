import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BackendApiError(RuntimeError):
    def __init__(self, status_code: int | None, detail: Any, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


def _detail_to_message(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        messages = [item.get("msg") for item in detail if isinstance(item, dict) and isinstance(item.get("msg"), str)]
        if messages:
            return ", ".join(messages)
    if isinstance(detail, dict):
        message = detail.get("message")
        if isinstance(message, str):
            return message
    return "백엔드 API 요청을 처리하지 못했습니다."


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
        query: dict[str, Any] | None = None,
    ) -> Any:
        request_path = path
        if query:
            request_path = f"{path}?{urlencode(query)}"

        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        request = Request(
            f"{self.base_url}{request_path}",
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
            try:
                problem = json.loads(exc.read().decode("utf-8"))
                detail = problem.get("detail", problem) if isinstance(problem, dict) else problem
            except (json.JSONDecodeError, UnicodeDecodeError):
                detail = exc.reason
            raise BackendApiError(exc.code, detail, _detail_to_message(detail)) from exc
        except URLError as exc:
            raise BackendApiError(None, str(exc.reason), "백엔드 서버에 연결할 수 없습니다.") from exc

    def get_menu(self) -> Any:
        return self._request("GET", "/menu")

    def submit_order(self, access_token: str | None, payload: dict[str, Any]) -> Any:
        return self._request("POST", "/orders", access_token=access_token, body=payload)

    def approve_dummy_payment(self, access_token: str | None, payload: dict[str, Any]) -> Any:
        return self._request("POST", "/payments/dummy/approve", access_token=access_token, body=payload)

    def get_receipt(self, access_token: str | None, order_id: int) -> Any:
        return self._request("GET", f"/orders/{order_id}/receipt", access_token=access_token)

    def list_recent_orders(self, access_token: str | None, limit: int) -> Any:
        return self._request("GET", "/admin/orders", access_token=access_token, query={"limit": limit})

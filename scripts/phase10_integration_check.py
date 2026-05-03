from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BACKEND_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
MCP_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://127.0.0.1:8010").rstrip("/")
ADMIN_EMAIL = os.getenv("DAJUNG_ADMIN_EMAIL", "admin@example.test")
ADMIN_PASSWORD = os.getenv("DAJUNG_ADMIN_PASSWORD", "demo-admin-001!")

ORDER_ITEM = {
    "menu_item_id": "menu_dajung_teriyaki_set",
    "quantity": 1,
    "selected_options": [
        {
            "group_id": "og_dajung_teriyaki_drink",
            "choice_ids": ["opt_dajung_teriyaki_drink_cola"],
        },
        {
            "group_id": "og_dajung_teriyaki_side",
            "choice_ids": ["opt_dajung_teriyaki_side_fries"],
        },
    ],
}


class CheckFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: Any


def _decode_body(raw_body: bytes) -> Any:
    if not raw_body:
        return None
    return json.loads(raw_body.decode("utf-8"))


def request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
    expected_status: set[int] | None = None,
) -> HttpResult:
    expected = expected_status or set(range(200, 300))
    headers = {"Accept": "application/json"}
    payload = None
    if body is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(f"{base_url}{path}", data=payload, headers=headers, method=method)
    try:
        with urlopen(req, timeout=10) as response:
            result = HttpResult(response.status, _decode_body(response.read()))
    except HTTPError as exc:
        result = HttpResult(exc.code, _decode_body(exc.read()))
    except URLError as exc:
        raise CheckFailure(f"{base_url}{path} 연결 실패: {exc.reason}") from exc

    if result.status not in expected:
        raise CheckFailure(
            f"{method} {path} 예상 상태 {sorted(expected)}와 다릅니다. "
            f"실제 상태={result.status}, 응답={result.body}"
        )
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def pass_check(message: str) -> None:
    print(f"[통과] {message}")


def login(email: str, password: str) -> dict[str, Any]:
    return request(
        BACKEND_BASE_URL,
        "POST",
        "/auth/login",
        body={"email": email, "password": password},
    ).body


def mcp_call(name: str, arguments: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    return request(
        MCP_BASE_URL,
        "POST",
        "/mcp/tools/call",
        body={"name": name, "arguments": arguments},
        token=token,
    ).body


def main() -> int:
    run_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    user_email = f"phase10.{run_id}@example.test"
    user_password = "Phase10-demo-001!"

    try:
        request(BACKEND_BASE_URL, "GET", "/health")
        request(MCP_BASE_URL, "GET", "/health")
        pass_check("백엔드와 Fake MCP HTTP 서버 상태 확인")

        request(
            BACKEND_BASE_URL,
            "POST",
            "/orders",
            body={"source": "kiosk_premium", "items": [ORDER_ITEM]},
            expected_status={401, 403},
        )
        pass_check("비로그인 사용자의 주문 생성 제한 확인")

        signup = request(
            BACKEND_BASE_URL,
            "POST",
            "/auth/signup",
            body={
                "email": user_email,
                "password": user_password,
                "name": "통합 검증 사용자",
                "phone": "000-0000-1910",
            },
            expected_status={201},
        ).body
        access_token = signup["access_token"]
        login_result = login(user_email, user_password)
        access_token = login_result["access_token"]
        pass_check("회원가입과 로그인 확인")

        kiosk_order = request(
            BACKEND_BASE_URL,
            "POST",
            "/orders",
            body={"source": "kiosk_premium", "items": [ORDER_ITEM]},
            token=access_token,
        ).body
        first_payment = request(
            BACKEND_BASE_URL,
            "POST",
            "/payments/dummy/approve",
            body={"order_id": kiosk_order["id"], "idempotency_key": f"phase10-kiosk-{run_id}"},
            token=access_token,
        ).body
        second_payment = request(
            BACKEND_BASE_URL,
            "POST",
            "/payments/dummy/approve",
            body={"order_id": kiosk_order["id"], "idempotency_key": f"phase10-kiosk-{run_id}"},
            token=access_token,
        ).body
        require(first_payment["id"] == second_payment["id"], "더미 결제 재시도 시 같은 결제 ID가 반환되어야 합니다.")

        kiosk_receipt = request(
            BACKEND_BASE_URL,
            "GET",
            f"/orders/{kiosk_order['id']}/receipt",
            token=access_token,
        ).body
        point_balance = request(BACKEND_BASE_URL, "GET", "/points/me", token=access_token).body
        point_ledger = request(BACKEND_BASE_URL, "GET", "/points/ledger", token=access_token).body
        kiosk_ledger = [entry for entry in point_ledger if entry.get("order_id") == kiosk_order["id"]]
        require(len(kiosk_ledger) == 1, "키오스크 주문 포인트 적립 내역이 1건이어야 합니다.")
        require(kiosk_receipt["order_id"] == kiosk_order["id"], "키오스크 주문 영수증이 생성되어야 합니다.")
        require(point_balance["points_balance"] >= kiosk_ledger[0]["amount"], "포인트 잔액이 적립 금액을 반영해야 합니다.")
        pass_check("Dajung Premium 키오스크 주문, 더미 결제, 포인트, 영수증 확인")

        handoff = request(BACKEND_BASE_URL, "POST", "/auth/agent-handoff", token=access_token).body
        agent_session = request(
            BACKEND_BASE_URL,
            "POST",
            "/auth/agent-session",
            body={"handoff_token": handoff["handoff_token"]},
        ).body
        request(
            BACKEND_BASE_URL,
            "POST",
            "/auth/agent-session",
            body={"handoff_token": handoff["handoff_token"]},
            expected_status={401},
        )
        agent_token = agent_session["access_token"]
        pass_check("AI Agent handoff token 교환과 재사용 방지 확인")

        agent_menu = request(BACKEND_BASE_URL, "GET", "/agent/menu", token=agent_token).body
        require(len(agent_menu["items"]) > 0, "Agent 메뉴 조회 결과가 비어 있습니다.")
        draft = request(
            BACKEND_BASE_URL,
            "POST",
            "/agent/orders/draft",
            body={"items": [ORDER_ITEM]},
            token=agent_token,
        ).body
        require(draft["source"] == "ai_agent", "Agent 주문 초안 source가 ai_agent여야 합니다.")
        agent_order = request(
            BACKEND_BASE_URL,
            "POST",
            "/agent/orders/confirm",
            body={"items": [ORDER_ITEM]},
            token=agent_token,
        ).body
        agent_payment = request(
            BACKEND_BASE_URL,
            "POST",
            "/agent/payments/dummy/approve",
            body={"order_id": agent_order["id"], "idempotency_key": f"phase10-agent-{run_id}"},
            token=agent_token,
        ).body
        require(agent_order["source"] == "ai_agent", "AI Agent 주문 source가 ai_agent여야 합니다.")
        require(agent_payment["payment"]["status"] == "approved", "AI Agent 더미 결제가 승인되어야 합니다.")
        require(agent_payment["receipt"]["order_id"] == agent_order["id"], "AI Agent 주문 영수증이 생성되어야 합니다.")
        pass_check("AI 채팅 주문 완료, 더미 결제, 포인트, 영수증 확인")

        admin_login = login(ADMIN_EMAIL, ADMIN_PASSWORD)
        admin_token = admin_login["access_token"]
        request(BACKEND_BASE_URL, "GET", "/admin/overview", token=access_token, expected_status={403})
        overview = request(BACKEND_BASE_URL, "GET", "/admin/overview", token=admin_token).body
        recent_orders = request(BACKEND_BASE_URL, "GET", "/admin/orders?limit=20", token=admin_token).body
        recent_by_id = {order["id"]: order for order in recent_orders}
        require(kiosk_order["id"] in recent_by_id, "관리자 최근 주문에 키오스크 주문이 없습니다.")
        require(agent_order["id"] in recent_by_id, "관리자 최근 주문에 AI Agent 주문이 없습니다.")
        require(recent_by_id[kiosk_order["id"]]["receipt"] is not None, "관리자 주문 목록에 키오스크 영수증 상태가 없습니다.")
        require(recent_by_id[agent_order["id"]]["payment"] is not None, "관리자 주문 목록에 Agent 결제 상태가 없습니다.")
        sources = {stat["source"] for stat in overview["source_stats"]}
        require({"kiosk_premium", "ai_agent"}.issubset(sources), "관리자 개요 source 통계에 키오스크와 Agent가 함께 있어야 합니다.")
        pass_check("관리자 대시보드 반영과 일반 사용자 접근 거부 확인")

        tools = request(MCP_BASE_URL, "GET", "/mcp/tools").body
        tool_names = {tool["name"] for tool in tools}
        expected_tools = {
            "dajung.get_menu",
            "dajung.submit_order",
            "dajung.approve_dummy_payment",
            "dajung.get_receipt",
            "dajung.list_recent_orders",
        }
        require(expected_tools.issubset(tool_names), "MCP 필수 tool 목록이 부족합니다.")
        require(
            all("input_schema" in tool and "output_schema" in tool for tool in tools),
            "MCP tool 스키마가 누락되었습니다.",
        )
        mcp_menu = mcp_call("dajung.get_menu", {})
        require(mcp_menu["ok"] is True and len(mcp_menu["content"]["items"]) > 0, "MCP 메뉴 조회가 실패했습니다.")
        mcp_order = mcp_call(
            "dajung.submit_order",
            {"source": "mcp", "items": [ORDER_ITEM]},
            token=access_token,
        )
        require(mcp_order["ok"] is True, "MCP 주문 제출이 실패했습니다.")
        require(mcp_order["content"]["source"] == "mcp", "MCP 주문 source가 mcp여야 합니다.")
        mcp_payment = mcp_call(
            "dajung.approve_dummy_payment",
            {"order_id": mcp_order["content"]["id"], "idempotency_key": f"phase10-mcp-{run_id}"},
            token=access_token,
        )
        require(mcp_payment["ok"] is True, "MCP 더미 결제 승인이 실패했습니다.")
        require(mcp_payment["content"]["status"] == "approved", "MCP 더미 결제가 승인되어야 합니다.")
        mcp_receipt = mcp_call(
            "dajung.get_receipt",
            {"order_id": mcp_order["content"]["id"]},
            token=access_token,
        )
        require(mcp_receipt["ok"] is True, "MCP 영수증 조회가 실패했습니다.")
        require(
            mcp_receipt["content"]["order_id"] == mcp_order["content"]["id"],
            "MCP 영수증이 MCP 주문과 연결되어야 합니다.",
        )
        mcp_recent_orders = mcp_call("dajung.list_recent_orders", {"limit": 20}, token=admin_token)
        require(mcp_recent_orders["ok"] is True, "관리자 권한 MCP 최근 주문 조회가 실패했습니다.")
        require(
            any(order["id"] == mcp_order["content"]["id"] for order in mcp_recent_orders["content"]["orders"]),
            "MCP 최근 주문 목록에 MCP 주문이 없습니다.",
        )
        mcp_forbidden = mcp_call("dajung.list_recent_orders", {"limit": 3}, token=access_token)
        require(mcp_forbidden["ok"] is False, "일반 사용자 MCP 관리자 tool 호출은 실패해야 합니다.")
        require(mcp_forbidden["error"]["backend_status"] == 403, "MCP 실패 응답은 백엔드 403을 전달해야 합니다.")
        pass_check("MCP tool 메뉴, 주문, 결제, 영수증, 최근 주문, 실패 응답 확인")

        print("[완료] Phase 10 통합 검증 스크립트가 모두 통과했습니다.")
        return 0
    except (CheckFailure, KeyError, TypeError, ValueError) as exc:
        print(f"[실패] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

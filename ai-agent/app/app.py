from dataclasses import asdict
from pathlib import Path
from typing import Any

import streamlit as st

from backend_client import AgentSession, BackendApiError, BackendClient
from config import get_settings
from model_client import (
    IntentValidationError,
    LLMProviderError,
    ProviderConfigurationError,
    create_llm_provider,
    validate_intent,
)
from session_handoff import exchange_handoff_token, get_handoff_token_from_query_params
from tools.menu_tools import available_menu_summaries, get_menu
from tools.order_tools import confirm_order, create_order_draft
from tools.payment_tools import approve_dummy_payment
from tools.receipt_tools import get_receipt
from tools.user_tools import get_points_balance, get_user_context


def format_krw(amount: int) -> str:
    return f"{amount:,}원"


def format_points(points: int) -> str:
    return f"{points:,} P"


def read_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "system_prompt.md"
    return prompt_path.read_text(encoding="utf-8")


def init_state() -> None:
    st.session_state.setdefault(
        "messages",
        [
            {
                "role": "assistant",
                "content": "안녕하세요. 다정 AI Agent입니다. handoff token으로 세션을 연결한 뒤 메뉴 조회와 주문을 도와드릴게요.",
            }
        ],
    )
    st.session_state.setdefault("agent_session", None)
    st.session_state.setdefault("handled_handoff_token", None)
    st.session_state.setdefault("pending_order_request", None)
    st.session_state.setdefault("pending_order_items", None)
    st.session_state.setdefault("pending_draft", None)
    st.session_state.setdefault("last_order_id", None)


def current_session() -> AgentSession | None:
    payload = st.session_state.get("agent_session")
    if not isinstance(payload, dict):
        return None
    return AgentSession(**payload)


def save_session(session: AgentSession) -> None:
    st.session_state.agent_session = asdict(session)


def append_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})


def render_messages() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def menu_text(menu_items: list[dict[str, Any]]) -> str:
    if not menu_items:
        return "현재 표시할 메뉴가 없습니다."

    lines = ["현재 주문 가능한 메뉴입니다."]
    for item in menu_items:
        availability = "주문 가능" if item.get("is_available", True) else "주문 불가"
        lines.append(f"- {item.get('name')} · {format_krw(int(item.get('price', 0)))} · {availability}")
    return "\n".join(lines)


def draft_text(draft: dict[str, Any]) -> str:
    lines = ["주문 초안을 만들었습니다. 결제 전 확인해 주세요."]
    for item in draft.get("items", []):
        lines.append(
            f"- {item.get('name_snapshot')} {item.get('quantity')}개: {format_krw(int(item.get('line_total', 0)))}"
        )
        selected_options = item.get("selected_options", [])
        for option_group in selected_options:
            choices = ", ".join(choice.get("name", "") for choice in option_group.get("choices", []))
            lines.append(f"  - {option_group.get('group_name')}: {choices}")
    lines.append(f"총액: {format_krw(int(draft.get('total_amount', 0)))}")
    lines.append("진행하려면 '확정' 또는 '결제'라고 입력해 주세요. 실제 결제가 아닌 더미 결제로 처리됩니다.")
    return "\n".join(lines)


def order_complete_text(order: dict[str, Any], payment_result: dict[str, Any]) -> str:
    payment = payment_result.get("payment", {})
    points = payment_result.get("points", {})
    receipt = payment_result.get("receipt")
    lines = [
        "주문을 확정하고 더미 결제를 완료했습니다.",
        f"- 주문 번호: #{order.get('id')}",
        f"- 결제 금액: {format_krw(int(payment.get('approved_amount', 0)))}",
        f"- 결제 상태: {payment.get('status')}",
        f"- 현재 포인트: {format_points(int(points.get('points_balance', 0)))}",
    ]
    if isinstance(receipt, dict):
        lines.append(f"- 영수증 번호: {receipt.get('receipt_number')}")
    else:
        lines.append("- 영수증은 아직 확인되지 않았습니다.")
    return "\n".join(lines)


def user_context_text(context: dict[str, Any]) -> str:
    user = context.get("user", {})
    points = context.get("points", {})
    recent_orders = context.get("recent_orders", [])
    lines = [
        f"{user.get('name', '사용자')}님의 현재 정보입니다.",
        f"- 이메일: {user.get('email', '-')}",
        f"- 포인트: {format_points(int(points.get('points_balance', 0)))}",
    ]
    if recent_orders:
        lines.append("최근 주문:")
        for order in recent_orders:
            lines.append(f"- #{order.get('id')} · {order.get('status')} · {format_krw(int(order.get('total_amount', 0)))}")
    else:
        lines.append("최근 주문이 없습니다.")
    return "\n".join(lines)


def receipt_text(receipt: dict[str, Any]) -> str:
    content = receipt.get("content", {})
    return "\n".join(
        [
            "영수증을 확인했습니다.",
            f"- 영수증 번호: {receipt.get('receipt_number')}",
            f"- 주문 번호: #{receipt.get('order_id')}",
            f"- 총액: {format_krw(int(content.get('total_amount', 0)))}",
            f"- 발급 시각: {receipt.get('issued_at')}",
        ]
    )


def alternatives_text(alternatives: list[dict[str, Any]]) -> str:
    if not alternatives:
        return "현재 제안할 수 있는 대체 메뉴가 없습니다."
    items = [f"- {item.get('name')} ({format_krw(int(item.get('price', 0)))})" for item in alternatives]
    return "대신 주문 가능한 메뉴를 제안드립니다.\n" + "\n".join(items)


def clarification_text(payload: dict[str, Any]) -> str:
    reason = payload.get("reason")
    menu_name = payload.get("menu_name") or "선택하신 메뉴"
    pending_item = payload.get("pending_order_item", {})

    if reason == "missing_quantity":
        return f"{menu_name}을 몇 개 주문할까요? 예: '1개 주문할게요'"

    if reason == "missing_options":
        quantity = pending_item.get("quantity", 1) if isinstance(pending_item, dict) else 1
        lines = [f"{menu_name} {quantity}개 주문을 위해 필수 옵션을 골라주세요."]
        for group in payload.get("missing_option_groups", []):
            choices = []
            for choice in group.get("choices", []):
                price_delta = int(choice.get("price_delta", 0))
                suffix = f" (+{format_krw(price_delta)})" if price_delta else ""
                choices.append(f"{choice.get('name')}{suffix}")
            choice_text = ", ".join(choices) if choices else "선택 가능한 옵션 없음"
            lines.append(f"- {group.get('name')}: {choice_text}")
        return "\n".join(lines)

    alternatives = payload.get("alternatives", [])
    if alternatives:
        return "주문 정보를 조금 더 확인해야 합니다.\n" + alternatives_text(alternatives)
    return "메뉴명, 수량, 필요한 옵션을 함께 알려주세요. 예: '불고기버거 1개 주문할게요'"


def connect_with_handoff(client: BackendClient, handoff_token: str) -> None:
    with st.spinner("Agent 세션을 연결하는 중입니다."):
        session = exchange_handoff_token(client, handoff_token)
    save_session(session)
    st.session_state.handled_handoff_token = handoff_token
    append_message("assistant", f"{session.user.get('name', '사용자')}님 세션이 연결되었습니다.")


def connect_with_login(client: BackendClient, email: str, password: str) -> None:
    with st.spinner("로그인 후 Agent 세션을 준비하는 중입니다."):
        login_result = client.login(email, password)
        session = client.create_agent_session_from_access_token(str(login_result["access_token"]))
    save_session(session)
    append_message("assistant", f"{session.user.get('name', '사용자')}님 Agent 세션이 연결되었습니다.")


def connect_with_bearer_token(client: BackendClient, access_token: str) -> None:
    with st.spinner("입력한 토큰으로 세션을 확인하는 중입니다."):
        session = client.session_from_bearer_token(access_token.strip())
    save_session(session)
    append_message("assistant", f"{session.user.get('name', '사용자')}님 토큰 세션이 연결되었습니다.")


def execute_intent(client: BackendClient, session: AgentSession, user_message: str) -> str:
    menu_items = get_menu(client, session)
    provider = st.session_state.provider
    raw_intent = provider.generate_response(
        user_message,
        {
            "system_prompt": st.session_state.system_prompt,
            "menu_items": menu_items,
            "has_pending_draft": bool(st.session_state.pending_draft),
            "pending_order_request": st.session_state.pending_order_request,
            "last_order_id": st.session_state.last_order_id,
        },
    )

    try:
        intent = validate_intent(raw_intent)
    except IntentValidationError:
        st.session_state.pending_order_request = None
        st.session_state.pending_order_items = None
        st.session_state.pending_draft = None
        return "주문 intent JSON을 이해하지 못했습니다. 메뉴명과 수량을 다시 입력해 주세요."

    if intent.action == "get_menu":
        return menu_text(menu_items)

    if intent.action == "get_user_context":
        return user_context_text(get_user_context(client, session))

    if intent.action == "get_points_balance":
        points = get_points_balance(client, session)
        return f"현재 포인트는 {format_points(int(points.get('points_balance', 0)))}입니다."

    if intent.action == "get_receipt":
        order_id = intent.payload.get("order_id") or st.session_state.last_order_id
        if not order_id:
            return "조회할 주문 번호가 필요합니다. 예: '1번 주문 영수증 보여줘'"
        return receipt_text(get_receipt(client, session, int(order_id)))

    if intent.action == "unavailable_menu":
        requested_name = intent.payload.get("requested_name", "요청한 메뉴")
        return f"{requested_name}은 현재 주문할 수 없습니다.\n{alternatives_text(intent.payload.get('alternatives', []))}"

    if intent.action == "ask_clarification":
        pending_order_item = intent.payload.get("pending_order_item")
        if isinstance(pending_order_item, dict):
            st.session_state.pending_order_request = pending_order_item
            st.session_state.pending_order_items = None
            st.session_state.pending_draft = None
            return clarification_text(intent.payload)

        alternatives = intent.payload.get("alternatives", [])
        if alternatives:
            return "주문할 메뉴를 정확히 확인하지 못했습니다.\n" + alternatives_text(alternatives)
        summaries = available_menu_summaries(menu_items, limit=3)
        if summaries:
            return "메뉴명과 수량을 함께 입력해 주세요. 예: '데리버거 세트 1개 주문해줘'\n추천: " + ", ".join(summaries)
        return "메뉴명과 수량을 다시 입력해 주세요."

    if intent.action == "create_order_draft":
        items = list(intent.payload.get("items", []))
        if not items:
            return "주문 항목을 만들지 못했습니다. 메뉴명을 다시 입력해 주세요."
        draft = create_order_draft(client, session, items)
        st.session_state.pending_order_request = None
        st.session_state.pending_order_items = items
        st.session_state.pending_draft = draft
        return draft_text(draft)

    if intent.action == "confirm_order":
        items = st.session_state.pending_order_items
        if not items:
            return "확정할 주문 초안이 없습니다. 먼저 메뉴와 수량을 입력해 주세요."
        order = confirm_order(client, session, items)
        payment_result = approve_dummy_payment(client, session, int(order["id"]))
        payment_result["points"] = get_points_balance(client, session)
        payment_result["receipt"] = get_receipt(client, session, int(order["id"]))
        st.session_state.pending_order_request = None
        st.session_state.pending_order_items = None
        st.session_state.pending_draft = None
        st.session_state.last_order_id = int(order["id"])
        return order_complete_text(order, payment_result)

    return "요청을 처리하지 못했습니다. 다시 입력해 주세요."


def main() -> None:
    settings = get_settings()
    client = BackendClient(settings.backend_api_base_url)

    st.set_page_config(page_title="다정 AI Agent", page_icon="D", layout="wide")
    init_state()

    try:
        provider, provider_warning = create_llm_provider(settings)
    except ProviderConfigurationError as exc:
        provider = None
        provider_warning = str(exc)

    st.session_state.provider = provider
    st.session_state.system_prompt = read_system_prompt()

    st.title("다정 AI Agent")
    st.caption("백엔드 API만 호출하는 demo mode 텍스트 주문 Agent입니다.")

    with st.sidebar:
        st.subheader("세션")
        session = current_session()
        if session:
            st.success(f"{session.user.get('name', '사용자')}님 연결됨")
            st.caption(f"토큰 종류: {session.token_use}")
            if st.button("세션 해제", type="secondary"):
                st.session_state.agent_session = None
                st.session_state.pending_order_request = None
                st.session_state.pending_order_items = None
                st.session_state.pending_draft = None
                st.rerun()
        else:
            st.info("handoff token이 없으면 데모 사용자 또는 직접 로그인으로 Agent 세션을 만들 수 있습니다.")

            if settings.demo_mode:
                if st.button("데모 사용자로 시작", type="primary"):
                    try:
                        connect_with_login(client, "demo.user1@example.test", "demo-user-001!")
                        st.rerun()
                    except BackendApiError as exc:
                        st.error(f"데모 로그인 실패: {exc}")

            with st.expander("handoff token 연결", expanded=True):
                manual_token = st.text_input("handoff token", type="password", placeholder="React 앱에서 받은 token")
                if st.button("handoff token으로 연결", disabled=not manual_token):
                    try:
                        connect_with_handoff(client, manual_token)
                        st.rerun()
                    except BackendApiError as exc:
                        st.error(f"세션 연결 실패: {exc}")

            with st.expander("이메일로 로그인", expanded=False):
                login_email = st.text_input("이메일", placeholder="demo.user1@example.test")
                login_password = st.text_input("비밀번호", type="password")
                if st.button("로그인 후 Agent 세션 만들기", disabled=not login_email or not login_password):
                    try:
                        connect_with_login(client, login_email, login_password)
                        st.rerun()
                    except BackendApiError as exc:
                        st.error(f"로그인 실패: {exc}")

            with st.expander("JWT 토큰 직접 입력", expanded=False):
                bearer_token = st.text_input("Bearer JWT", type="password", placeholder="access 또는 agent token")
                if st.button("JWT로 연결", disabled=not bearer_token):
                    try:
                        connect_with_bearer_token(client, bearer_token)
                        st.rerun()
                    except BackendApiError as exc:
                        st.error(f"토큰 확인 실패: {exc}")

            st.caption("데모 계정은 seed 데이터의 일반 사용자 계정으로 로그인합니다.")

        st.subheader("모델")
        st.write(f"Provider: `{provider.provider_name if provider else '설정 오류'}`")
        st.write(f"목표 모델: `{settings.target_model_id}`")
        st.write(f"demo mode: `{'켜짐' if settings.demo_mode else '꺼짐'}`")
        if provider_warning:
            st.warning(provider_warning)

        if st.button("대화 초기화"):
            st.session_state.messages = []
            st.session_state.pending_order_request = None
            st.session_state.pending_order_items = None
            st.session_state.pending_draft = None
            append_message("assistant", "대화를 초기화했습니다. 다시 주문을 시작해 주세요.")
            st.rerun()

    handoff_token = get_handoff_token_from_query_params(st.query_params)
    if handoff_token and handoff_token != st.session_state.handled_handoff_token and current_session() is None:
        try:
            connect_with_handoff(client, handoff_token)
            st.rerun()
        except BackendApiError as exc:
            st.error(f"handoff token 교환 실패: {exc}")

    pending_draft = st.session_state.get("pending_draft")
    if pending_draft:
        st.info("결제 전 확인 대기 중인 주문 초안이 있습니다. 채팅에 '확정' 또는 '결제'라고 입력하면 더미 결제가 진행됩니다.")
    elif st.session_state.get("pending_order_request"):
        st.info("주문 초안을 만들기 전에 추가 정보 확인이 필요합니다. 채팅으로 수량이나 옵션을 이어서 입력해 주세요.")

    render_messages()

    user_input = st.chat_input("예: 데리버거 세트 1개 주문해줘")
    if not user_input:
        return

    append_message("user", user_input)
    session = current_session()
    if session is None:
        append_message("assistant", "세션이 연결되지 않았습니다. 사이드바에서 handoff token, 데모 사용자, 이메일 로그인, 또는 JWT 입력으로 Agent 세션을 연결해 주세요.")
        st.rerun()

    if provider is None:
        append_message("assistant", "LLM Provider 설정이 올바르지 않아 요청을 처리할 수 없습니다.")
        st.rerun()

    try:
        with st.spinner("요청을 처리하는 중입니다."):
            response = execute_intent(client, session, user_input)
    except BackendApiError as exc:
        response = f"백엔드 API 오류가 발생했습니다: {exc}"
    except LLMProviderError as exc:
        response = f"모델 응답을 처리하지 못했습니다: {exc}"
    except Exception:
        response = "알 수 없는 오류가 발생했습니다. 입력을 다시 확인해 주세요."

    append_message("assistant", response)
    st.rerun()


if __name__ == "__main__":
    main()

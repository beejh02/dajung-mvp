from typing import Any

from backend_client import AgentSession, BackendClient


def create_order_draft(
    client: BackendClient,
    session: AgentSession,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return client.create_order_draft(session.access_token, items)


def confirm_order(
    client: BackendClient,
    session: AgentSession,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return client.confirm_order(session.access_token, items)

from typing import Any

from backend_client import AgentSession, BackendClient


TOKEN_QUERY_KEYS = ("handoff_token", "token")


def get_handoff_token_from_query_params(query_params: Any) -> str | None:
    for key in TOKEN_QUERY_KEYS:
        if key not in query_params:
            continue
        value = query_params[key]
        if isinstance(value, list):
            value = value[0] if value else None
        if value:
            return str(value).strip()
    return None


def exchange_handoff_token(client: BackendClient, handoff_token: str) -> AgentSession:
    return client.exchange_agent_session(handoff_token.strip())

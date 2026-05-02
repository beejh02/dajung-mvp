from typing import Any

from backend_client import AgentSession, BackendClient


def get_menu(client: BackendClient, session: AgentSession) -> list[dict[str, Any]]:
    return list(client.get_agent_menu(session.access_token).get("items", []))


def available_menu_summaries(menu_items: list[dict[str, Any]], limit: int = 5) -> list[str]:
    summaries: list[str] = []
    for item in menu_items:
        if not item.get("is_available", True):
            continue
        summaries.append(f"{item.get('name')} ({int(item.get('price', 0)):,}원)")
        if len(summaries) >= limit:
            break
    return summaries

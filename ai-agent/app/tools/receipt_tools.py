from backend_client import AgentSession, BackendClient


def get_receipt(client: BackendClient, session: AgentSession, order_id: int) -> dict:
    return client.get_order_receipt(session.access_token, order_id)

from backend_client import AgentSession, BackendClient


def approve_dummy_payment(client: BackendClient, session: AgentSession, order_id: int) -> dict:
    return client.approve_dummy_payment(
        session.access_token,
        order_id,
        idempotency_key=f"agent-dummy-payment:order:{order_id}",
    )

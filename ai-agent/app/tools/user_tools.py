from backend_client import AgentSession, BackendClient


def get_user_context(client: BackendClient, session: AgentSession) -> dict:
    return client.get_user_context(session.access_token)


def get_points_balance(client: BackendClient, session: AgentSession) -> dict:
    return client.get_points_balance(session.access_token)

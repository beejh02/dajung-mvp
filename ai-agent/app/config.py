import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AgentSettings:
    app_env: str
    backend_api_base_url: str
    llm_provider: str
    demo_mode: bool
    target_model_id: str
    google_gemini_api_key: str | None
    cloudflare_account_id: str | None
    cloudflare_api_token: str | None
    cloudflare_model_id: str | None


def get_settings() -> AgentSettings:
    return AgentSettings(
        app_env=os.getenv("APP_ENV", "local"),
        backend_api_base_url=os.getenv("BACKEND_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        llm_provider=os.getenv("LLM_PROVIDER", "stub").strip().lower(),
        demo_mode=_env_bool("AGENT_DEMO_MODE", True),
        target_model_id=os.getenv("TARGET_MODEL_ID", "models/gemma-4-26b-a4b-it"),
        google_gemini_api_key=os.getenv("GOOGLE_GEMINI_API_KEY") or None,
        cloudflare_account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID") or None,
        cloudflare_api_token=os.getenv("CLOUDFLARE_API_TOKEN") or None,
        cloudflare_model_id=os.getenv("CLOUDFLARE_MODEL_ID") or None,
    )

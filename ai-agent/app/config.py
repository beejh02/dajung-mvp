import os
from dataclasses import dataclass


def _env_text(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return default


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
        app_env=_env_text("APP_ENV", default="local") or "local",
        backend_api_base_url=(_env_text("BACKEND_API_BASE_URL", default="http://127.0.0.1:8000") or "").rstrip("/"),
        llm_provider=(_env_text("LLM_PROVIDER", default="stub") or "stub").lower(),
        demo_mode=_env_bool("AGENT_DEMO_MODE", True),
        target_model_id=_env_text("LLM_MODEL", "TARGET_MODEL_ID", default="models/gemma-4-26b-a4b-it")
        or "models/gemma-4-26b-a4b-it",
        google_gemini_api_key=_env_text("GEMINI_API_KEY", "GOOGLE_GEMINI_API_KEY"),
        cloudflare_account_id=_env_text("CLOUDFLARE_ACCOUNT_ID"),
        cloudflare_api_token=_env_text("CLOUDFLARE_API_TOKEN"),
        cloudflare_model_id=_env_text("CLOUDFLARE_MODEL_ID"),
    )

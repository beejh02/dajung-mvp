import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    backend_api_base_url: str


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        backend_api_base_url=os.getenv("BACKEND_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
    )

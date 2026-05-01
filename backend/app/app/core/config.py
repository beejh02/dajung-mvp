import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _default_seed_data_dir() -> Path:
    return _project_root() / "shared" / "dummy-data"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Dajung Backend API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    app_env: str = os.getenv("APP_ENV", "local")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./dajung.db")
    database_echo: bool = _env_bool("DATABASE_ECHO", False)
    seed_on_startup: bool = _env_bool("SEED_ON_STARTUP", True)
    seed_data_dir: Path = Path(os.getenv("SEED_DATA_DIR", str(_default_seed_data_dir())))


@lru_cache
def get_settings() -> Settings:
    return Settings()

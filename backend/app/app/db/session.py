from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.models import *  # noqa: F403


def _connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings = get_settings()
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    connect_args=_connect_args(settings.database_url),
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db(seed: bool = True) -> None:
    create_db_and_tables()
    if not seed:
        return

    from app.db.seed import seed_database

    with Session(engine) as session:
        seed_database(session)

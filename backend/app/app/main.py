from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.session import init_db
from app.routers.agent import router as agent_router
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.menu import router as menu_router
from app.routers.orders import router as orders_router
from app.routers.payments import router as payments_router
from app.routers.points import router as points_router
from app.routers.receipts import router as receipts_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_db(seed=settings.seed_on_startup)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(auth_router)
    app.include_router(menu_router)
    app.include_router(orders_router)
    app.include_router(payments_router)
    app.include_router(points_router)
    app.include_router(receipts_router)
    app.include_router(admin_router)
    app.include_router(agent_router)
    app.include_router(health_router)
    return app


app = create_app()

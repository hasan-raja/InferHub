from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.models import router as models_router
from app.core.config import get_settings
from app.core.middleware import RequestContextMiddleware
from app.db.clients import close_dependencies, open_dependencies
from app.observability.tracing import configure_tracing


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("gateway_starting", app=settings.app_name, env=settings.app_env)
    app.state.dependencies = await open_dependencies(settings)
    yield
    await close_dependencies(app.state.dependencies)
    logger.info("gateway_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "prod" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    configure_tracing(app, settings)
    app.add_middleware(RequestContextMiddleware, settings=settings)

    app.include_router(health_router, tags=["health"])
    app.include_router(auth_router)
    app.include_router(models_router)
    app.mount("/metrics", make_asgi_app())

    return app


app = create_app()

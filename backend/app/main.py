from uuid import uuid4
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.errors import install_error_handlers
from app.api.routers.health import router
from app.core.config import AppSettings, configuration, model_settings


def create_app() -> FastAPI:
    settings = AppSettings(**configuration())
    mode = model_settings()
    @asynccontextmanager
    async def lifespan(application):
        yield
        if hasattr(application.state,'database_engine'):application.state.database_engine.dispose()
    application = FastAPI(title="财税 Harness", version="0.2.0",lifespan=lifespan)
    application.state.app_env = settings.app_env
    application.state.model_mode = mode.model_mode

    @application.middleware("http")
    async def request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    install_error_handlers(application)
    application.include_router(router)
    from app.api.routers.identity import router as identity
    from app.api.routers.ledger import router as ledger
    application.include_router(identity)
    application.include_router(ledger)
    return application


app = create_app()

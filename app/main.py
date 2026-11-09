from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import configure_logging
from app.core.redis import redis_client
from app.db.session import engine
from app.middleware.request_context import RequestContextMiddleware

settings = get_settings()
configure_logging(settings.log_level)

INSECURE_SECRET_KEYS = {
    "dev-only-change-me",
    "cambia-esta-clave-por-una-larga-y-aleatoria",
}

if settings.is_production and (
    settings.secret_key in INSECURE_SECRET_KEYS or len(settings.secret_key) < 32
):
    raise RuntimeError("Configura una SECRET_KEY segura antes de desplegar")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    engine.dispose()
    redis_client.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API REST profesional con FastAPI",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

register_error_handlers(app)
app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")

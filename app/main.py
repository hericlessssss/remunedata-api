from contextlib import asynccontextmanager

import redis.asyncio as redis
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Configuração do Sentry se DSN existir
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=1.0 if settings.is_development else 0.1,
    )
    logger.info("Sentry inicializado com sucesso.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lógica executada no ciclo de vida da aplicação."""
    # Inicializar Rate Limiter (Redis) — falha não deve derrubar o app
    r = None
    try:
        r = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(r)
        logger.info("Rate Limiter (FastAPI-Limiter) inicializado.")
    except Exception as e:
        logger.warning(
            f"Rate Limiter não pôde ser inicializado (Redis): {e}. Funcionando sem rate limit."
        )
    yield
    # Limpeza se necessário
    if r:
        await r.aclose()


app = FastAPI(
    title="DF Remuneration Collector API",
    description="API para coleta e consulta de remuneração dos servidores do DF",
    version="0.2.0",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Endpoint de health check para monitoramento."""
    return {
        "status": "ok",
        "env": settings.app_env,
        "version": app.version,
        "deployment_id": "FINAL_DEPLOY_V012",
    }


@app.get("/debug-routes")
async def debug_routes():
    """Lista todas as rotas registradas no app (Apenas para debug)."""
    from starlette.routing import Mount, Route

    routes = []
    for route in app.routes:
        if isinstance(route, Route):
            routes.append({"path": route.path, "name": route.name, "methods": list(route.methods)})
        elif isinstance(route, Mount):
            routes.append({"path": route.path, "name": route.name, "methods": ["MOUNT"]})
    return routes


# Registrar Rotas
app.include_router(api_router, prefix="/api/v1")

# Servir Dashboard Estático
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="static")

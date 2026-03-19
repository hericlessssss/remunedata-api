"""
app/main.py
Ponto de entrada da aplicação FastAPI.
Configura logging, registra routers e expõe o endpoint de health check.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(level=settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerencia o ciclo de vida da aplicação (startup / shutdown)."""
    logger.info(
        "Iniciando df-remuneration-collector",
        extra={"env": settings.app_env, "version": "0.1.0"},
    )
    yield
    logger.info("Encerrando df-remuneration-collector")


app = FastAPI(
    title="DF Remuneration Collector",
    description=(
        "RPA para coleta de dados de remuneração dos servidores públicos "
        "do Distrito Federal a partir do Portal da Transparência do DF."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.get(
    "/health",
    summary="Health check",
    description="Verifica se a aplicação está em execução.",
    tags=["infra"],
)
async def health_check() -> JSONResponse:
    """
    Endpoint de health check.

    Retorna status da aplicação.
    Não verifica dependências (banco, redis) — apenas se o processo está vivo.
    """
    return JSONResponse(
        content={"status": "ok", "env": settings.app_env},
        status_code=200,
    )

"""
app/main.py
Ponto de entrada da aplicação FastAPI.
"""

from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import get_logger
from app.api.router import api_router

logger = get_logger(__name__)

app = FastAPI(
    title="DF Remuneration Collector API",
    description="API para coleta e consulta de remuneração dos servidores do DF",
    version="0.1.0"
)

from fastapi.staticfiles import StaticFiles

# Registrar Rotas
app.include_router(api_router, prefix="/api/v1")

# Servir Dashboard Estático
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/health")
async def health_check():
    """Endpoint de health check para monitoramento."""
    return {
        "status": "ok",
        "timestamp": settings.model_dump(),
        "env": settings.app_env
    }

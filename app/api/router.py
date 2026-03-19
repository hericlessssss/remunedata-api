"""
app/api/router.py
Centralização das rotas da API.
"""

from fastapi import APIRouter
from app.api.endpoints import executions, remuneration

api_router = APIRouter()

api_router.include_router(executions.router, prefix="/executions", tags=["Executions"])
api_router.include_router(remuneration.router, prefix="/remuneration", tags=["Remunerations"])

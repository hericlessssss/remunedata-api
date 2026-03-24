"""
app/api/router.py
Centralização das rotas da API.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.endpoints import executions, remuneration

api_router = APIRouter()

# Rotas protegidas (apenas para gestão interna e disparos)
api_router.include_router(
    executions.router,
    prefix="/executions",
    tags=["Executions"],
    dependencies=[Depends(get_current_user)],
)

# Rotas públicas (consulta de remuneração)
api_router.include_router(remuneration.router, prefix="/remuneration", tags=["Remunerations"])

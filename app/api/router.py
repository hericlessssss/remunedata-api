"""
app/api/router.py
Centralização das rotas da API.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.endpoints import executions, remuneration, subscriptions

api_router = APIRouter()

# Rotas de execuções (proteção individual por endpoint)
api_router.include_router(
    executions.router,
    prefix="/executions",
    tags=["Executions"],
)

# Rotas de remuneração — busca exige assinatura ativa, summary é público
api_router.include_router(remuneration.router, prefix="/remuneration", tags=["Remunerations"])

# Rotas de assinatura (plans: público | checkout+me: JWT | webhook: secret)
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])

"""
app/api/router.py
Centralização das rotas da API.
"""

from fastapi import APIRouter

from app.api.endpoints import admin, executions, remuneration, subscriptions
from app.core.config import settings

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

# Rotas Administrativas — Prefixo secreto e proteção por e-mail
api_router.include_router(
    admin.router,
    prefix=f"/{settings.admin_path_prefix}",
    tags=["Admin"],
)

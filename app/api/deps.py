"""
app/api/deps.py
Dependências do FastAPI para injeção de repositórios e sessão de banco.
"""

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_token
from app.persistence.models import UserSubscription
from app.persistence.repositories import ExecutionRepository, RemunerationRepository
from app.persistence.session import get_session

security = HTTPBearer()


def get_execution_repository(session: AsyncSession = Depends(get_session)) -> ExecutionRepository:
    """Dependency for ExecutionRepository."""
    return ExecutionRepository(session)


def get_remuneration_repository(
    session: AsyncSession = Depends(get_session),
) -> RemunerationRepository:
    """Dependency for RemunerationRepository."""
    return RemunerationRepository(session)


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependência que valida o token JWT do Supabase e retorna o payload do usuário.
    """
    return verify_token(token.credentials)


async def require_active_subscription(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Dependência que valida se o usuário possui assinatura ativa.
    Deve ser usada nos endpoints de consulta de remuneração pagos.
    """
    user_id: str = user.get("sub", "")
    now = datetime.now(timezone.utc)
    stmt = select(UserSubscription).where(
        UserSubscription.user_id == user_id,
        UserSubscription.status == "active",
        UserSubscription.expires_at > now,
    )
    result = await session.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assinatura ativa necessária para acessar este recurso. Assine em /planos.",
        )
    return user

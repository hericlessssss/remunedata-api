"""
app/api/deps.py
Dependências do FastAPI para injeção de repositórios e sessão de banco.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_token
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

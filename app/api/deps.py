"""
app/api/deps.py
Dependências do FastAPI para injeção de repositórios e sessão de banco.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.session import get_session
from app.persistence.repositories import ExecutionRepository, RemunerationRepository


def get_execution_repository(session: AsyncSession = Depends(get_session)) -> ExecutionRepository:
    """Dependency for ExecutionRepository."""
    return ExecutionRepository(session)


def get_remuneration_repository(session: AsyncSession = Depends(get_session)) -> RemunerationRepository:
    """Dependency for RemunerationRepository."""
    return RemunerationRepository(session)

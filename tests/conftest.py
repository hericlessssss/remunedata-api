"""
tests/conftest.py
Fixtures compartilhadas pelos testes da aplicação.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """
    Garante variáveis de ambiente mínimas para testes.
    Aplicada automaticamente a todos os testes (autouse=True).

    Isso evita erros de ValidationError do Settings em testes
    que não importam config diretamente.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@postgres:5432/df_remuneration",
    )
    monkeypatch.setenv(
        "DATABASE_URL_SYNC",
        "postgresql+psycopg2://postgres:postgres@postgres:5432/df_remuneration",
    )
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")


@pytest.fixture(scope="function")
def db_engine():
    """Cria a engine assíncrona para a duração da sessão de testes."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.core.config import get_settings
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)
    yield engine
    # Cleanup opcional
    

@pytest.fixture
async def db_session(db_engine):
    """Fixture para fornecer uma sessão de banco de dados isolada para cada teste."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


"""
tests/conftest.py
Fixtures compartilhadas pelos testes da aplicação.
"""

from unittest.mock import AsyncMock

import pytest
from circuitbreaker import CircuitBreakerMonitor


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """
    Garante variáveis de ambiente básicas para testes se não estiverem definidas.
    """
    import os

    if not os.getenv("DATABASE_URL"):
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/df_remuneration_test",
        )
    if not os.getenv("DATABASE_URL_SYNC"):
        monkeypatch.setenv(
            "DATABASE_URL_SYNC",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/df_remuneration_test",
        )
    if not os.getenv("APP_ENV"):
        monkeypatch.setenv("APP_ENV", "testing")
    if not os.getenv("LOG_LEVEL"):
        monkeypatch.setenv("LOG_LEVEL", "WARNING")


@pytest.fixture(autouse=True)
async def init_test_limiter(request):
    """
    Inicializa o FastAPILimiter com um Mock de Redis para evitar erros de loop
    e dependência de serviço externo em testes unitários/integração.
    """
    if "test_resilience.py" in request.node.fspath.strpath:
        yield
        return

    from fastapi_limiter import FastAPILimiter

    mock_redis = AsyncMock()
    # FastAPILimiter v0.1.6 usa evalsha para checar o rate limit
    mock_redis.evalsha = AsyncMock(return_value=0)
    mock_redis.script_load = AsyncMock(return_value="mock_sha")

    await FastAPILimiter.init(mock_redis)
    yield


@pytest.fixture(autouse=True)
def reset_breakers():
    """Garante que o estado do Circuit Breaker seja resetado entre os testes."""
    for breaker in CircuitBreakerMonitor.get_circuits():
        breaker.reset()


@pytest.fixture(autouse=True)
def override_auth(request):
    """
    Mocka a autenticação globalmente para todos os testes,
    EXCETO para os testes de autenticação propriamente ditos.
    """
    from app.api.deps import get_current_user
    from app.main import app

    # Se o teste estiver em test_auth.py, não mockamos para validar a lógica real
    if "test_auth.py" in request.node.fspath.strpath:
        yield
        return

    async def _get_current_user_override():
        return {"email": "test@example.com", "sub": "test-uuid", "aud": "authenticated"}

    app.dependency_overrides[get_current_user] = _get_current_user_override
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="function")
def db_engine():
    """Cria a engine assíncrona para a duração da sessão de testes."""
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)
    yield engine


@pytest.fixture
async def db_session(db_engine):
    """Fixture para fornecer uma sessão de banco de dados isolada para cada teste."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        from sqlalchemy import text

        await session.execute(
            text("TRUNCATE execution_annual, execution_monthly, remuneration_collected CASCADE")
        )
        await session.commit()

        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def override_get_session(db_session):
    """Override the get_session dependency with the test db_session."""
    from app.api.deps import get_session
    from app.main import app

    async def _get_session_override():
        yield db_session

    app.dependency_overrides[get_session] = _get_session_override
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def client():
    """Fixture para fornecer um cliente HTTP assíncrono para os testes da API."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

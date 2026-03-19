"""
tests/conftest.py
Fixtures compartilhadas pelos testes da aplicação.
"""

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
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        # Limpar o banco antes de cada teste para garantir isolamento (Doc item 15)
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

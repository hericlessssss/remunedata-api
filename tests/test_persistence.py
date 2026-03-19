"""
tests/test_persistence.py
Testes unitários para os modelos de banco de dados e configuração de sessão.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models import ExecutionAnnual, ExecutionMonthly, RemunerationCollected
from app.persistence.session import async_session_maker


@pytest.mark.asyncio
async def test_model_instantiation():
    """Verifica se os modelos podem ser instanciados com campos básicos."""
    annual = ExecutionAnnual(ano_exercicio=2025, status="success")
    assert annual.ano_exercicio == 2025
    assert annual.status == "success"

    monthly = ExecutionMonthly(mes_referencia="01", status="running")
    assert monthly.mes_referencia == "01"
    assert monthly.status == "running"

    remuneration = RemunerationCollected(
        ano_exercicio=2025,
        mes_referencia="01",
        codigo_identificacao="ID123",
        codigo_matricula="MAT123",
        nome_servidor="TESTE",
        raw_payload_json="{}",
    )
    assert remuneration.codigo_identificacao == "ID123"
    assert remuneration.nome_servidor == "TESTE"


@pytest.mark.asyncio
async def test_database_connection():
    """
    Teste de integração básico: verifica se consegue conectar ao banco
    e executar uma query simples.
    """
    async with async_session_maker() as session:
        assert isinstance(session, AsyncSession)
        # Executa uma query simples que não depende de dados
        result = await session.execute(select(1))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_create_and_retrieve_execution(db_session: AsyncSession):
    """
    Verifica se consegue salvar e recuperar uma execução anual.
    Depende da fixture db_session (que será definida no conftest ou aqui).
    """
    new_exec = ExecutionAnnual(ano_exercicio=2024, status="completed")
    db_session.add(new_exec)
    await db_session.commit()
    await db_session.refresh(new_exec)

    assert new_exec.id is not None

    # Recupera do banco
    stmt = select(ExecutionAnnual).where(ExecutionAnnual.id == new_exec.id)
    result = await db_session.execute(stmt)
    retrieved = result.scalar_one()

    assert retrieved.status == "completed"

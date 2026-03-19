import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models import ExecutionAnnual, ExecutionMonthly, RemunerationCollected
from app.persistence.repositories import ExecutionRepository, RemunerationRepository


@pytest.mark.asyncio
async def test_execution_repo_list_and_get(db_session: AsyncSession):
    repo = ExecutionRepository(db_session)
    # Test list_annual branches
    await repo.get_or_create_annual(2024)
    list_res = await repo.list_annual(limit=10)
    assert len(list_res) >= 1

    # Test get_annual branches
    annual = await repo.get_or_create_annual(2025)
    detail = await repo.get_annual(annual.id)
    assert detail.id == annual.id

    # Non-existent annual
    assert await repo.get_annual(99999) is None


@pytest.mark.asyncio
async def test_remuneration_repo_search_filters(db_session: AsyncSession):
    repo = RemunerationRepository(db_session)
    exec_an = ExecutionAnnual(ano_exercicio=2025, status="success")
    db_session.add(exec_an)
    await db_session.flush()

    monthly = ExecutionMonthly(execution_id=exec_an.id, mes_referencia="01", status="success")
    db_session.add(monthly)
    await db_session.flush()

    r1 = RemunerationCollected(
        execution_id=exec_an.id,
        monthly_execution_id=monthly.id,
        nome_servidor="TEST_USER",
        cpf_servidor="123",
        ano_exercicio=2025,
        mes_referencia="01",
        valor_bruto=100,
        codigo_identificacao="ID_COV",
        codigo_matricula="M_COV",
        raw_payload_json="{}",
    )
    db_session.add(r1)
    await db_session.commit()

    # Test cpf filter
    items, total = await repo.search(cpf="123")
    assert total == 1

    # Test ano filter
    items, total = await repo.search(ano=2025)
    assert total == 1

    # Test mes filter
    items, total = await repo.search(mes="01")
    assert total == 1

    # Test empty save_batch
    await repo.save_batch([])


@pytest.mark.asyncio
async def test_remuneration_repo_get_all_by_execution(db_session: AsyncSession):
    repo = RemunerationRepository(db_session)
    res = await repo.get_all_by_execution(1, limit=5)
    assert isinstance(res, list)


@pytest.mark.asyncio
async def test_remuneration_repo_summary_no_ano(db_session: AsyncSession):
    repo = RemunerationRepository(db_session)
    summary = await repo.get_summary(ano=None)
    assert "total_servidores" in summary


@pytest.mark.asyncio
async def test_logging_setup():
    from app.core.logging import get_logger

    logger = get_logger("test")
    logger.info("Test log coverage")


@pytest.mark.asyncio
async def test_session_rollback_coverage(db_engine):
    from app.persistence.session import get_session

    # Trigger exception in get_session
    try:
        async for session in get_session():
            raise Exception("Force Rollback")
    except Exception as e:
        assert str(e) == "Force Rollback"

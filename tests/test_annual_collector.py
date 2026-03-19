"""
tests/test_annual_collector.py
Testes para o AnnualCollector refatorado.
"""

from unittest.mock import AsyncMock

import pytest

from app.collector.annual import AnnualCollector
from app.persistence.repositories import ExecutionRepository


@pytest.fixture
def mock_monthly_collector():
    return AsyncMock()


@pytest.mark.asyncio
async def test_annual_run_all_success(db_session, mock_monthly_collector):
    exec_repo = ExecutionRepository(db_session)
    annual_mock_returns = [AsyncMock(status="success") for _ in range(12)]
    mock_monthly_collector.collect.side_effect = annual_mock_returns

    orchestrator = AnnualCollector(mock_monthly_collector, exec_repo)
    result = await orchestrator.run(ano=2025)

    assert result.status == "success"
    assert mock_monthly_collector.collect.call_count == 12


@pytest.mark.asyncio
async def test_annual_run_partial_success(db_session, mock_monthly_collector):
    exec_repo = ExecutionRepository(db_session)
    # Mes 1 sucesso, Mes 2 erro, outros sucesso
    returns = []
    for i in range(1, 13):
        if i == 2:
            returns.append(Exception("Fail"))
        else:
            returns.append(AsyncMock(status="success"))

    mock_monthly_collector.collect.side_effect = returns

    orchestrator = AnnualCollector(mock_monthly_collector, exec_repo)
    result = await orchestrator.run(ano=2025)

    assert result.status == "partial_success"
    assert mock_monthly_collector.collect.call_count == 12

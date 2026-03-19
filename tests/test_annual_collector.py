"""
tests/test_annual_collector.py
Testes unitários para o AnnualCollector.
Mocks do MonthlyCollector para validar a orquestração e loop.
"""

from unittest.mock import AsyncMock
import pytest
from datetime import datetime, timezone

from app.collector.annual import AnnualCollector
from app.persistence.models import ExecutionAnnual, ExecutionMonthly


@pytest.fixture
def mock_monthly_collector():
    collector = AsyncMock()
    return collector


@pytest.mark.asyncio
async def test_annual_run_all_success(db_session, mock_monthly_collector):
    """
    Testa sucesso total (12 meses OK).
    """
    # Setup: Simular 12 retornos de sucesso
    mock_monthly_collector.collect.side_effect = [
        ExecutionMonthly(mes_referencia=f"{i:02d}", status="success") for i in range(1, 13)
    ]
    
    orchestrator = AnnualCollector(mock_monthly_collector, db_session)
    result = await orchestrator.run(ano=2025)
    
    assert result.status == "success"
    assert mock_monthly_collector.collect.call_count == 12


@pytest.mark.asyncio
async def test_annual_run_partial_success(db_session, mock_monthly_collector):
    """
    Testa sucesso parcial (um mês falha, outros passam).
    """
    # Setup: Mes 1 sucesso, Mes 2 levanta exceção, Mes 3-12 sucesso
    returns = []
    for i in range(1, 13):
        if i == 2:
            returns.append(Exception("Network error on Feb"))
        else:
            returns.append(ExecutionMonthly(mes_referencia=f"{i:02d}", status="success"))
    
    mock_monthly_collector.collect.side_effect = returns
    
    orchestrator = AnnualCollector(mock_monthly_collector, db_session)
    result = await orchestrator.run(ano=2025)
    
    assert result.status == "partial_success"
    # Note: total_meses_processados é incrementado pelo monthly_collector.collect() interno. 
    # No nosso mock manual de 12 meses, seriam 11 sucessos. 
    # Na implementação real, o contador do BD seria atualizado pelos meses que não deram exception.
    assert mock_monthly_collector.collect.call_count == 12


@pytest.mark.asyncio
async def test_annual_run_total_error(db_session, mock_monthly_collector):
    """
    Testa erro total (todos 12 meses falham).
    """
    mock_monthly_collector.collect.side_effect = Exception("Global API Down")
    
    orchestrator = AnnualCollector(mock_monthly_collector, db_session)
    result = await orchestrator.run(ano=2025)
    
    assert result.status == "error"
    assert mock_monthly_collector.collect.call_count == 12

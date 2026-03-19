"""
tests/test_monthly_collector.py
Testes para o MonthlyCollector refatorado para usar repositórios.
"""

import json
import pytest
from unittest.mock import AsyncMock
from app.collector.monthly import MonthlyCollector
from app.persistence.models import ExecutionAnnual
from app.persistence.repositories import ExecutionRepository, RemunerationRepository


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.mark.asyncio
async def test_monthly_collect_success(db_session, mock_client):
    """Testa o fluxo de sucesso de coleta mensal com repositórios."""
    # Setup
    exec_repo = ExecutionRepository(db_session)
    rem_repo = RemunerationRepository(db_session)
    
    annual = await exec_repo.get_or_create_annual(2025)
    
    # Mock data
    with open("tests/mocks/remuneracao_page_0.json", "r", encoding="utf-8") as f:
        mock_response = json.load(f)
    
    # Simula uma única página
    mock_client.get_remuneracao.return_value = mock_response
    
    collector = MonthlyCollector(mock_client, exec_repo, rem_repo)
    result = await collector.collect(ano=2025, mes="01", annual_execution_id=annual.id)
    
    assert result.status == "success"
    assert result.registros_coletados > 0
    # Verifica se a annual_exec foi atualizada via repo (precisa de refresh)
    # Re-adicionamos a sessão pois o coletor chama expunge_all()
    db_session.add(annual)
    await db_session.refresh(annual)
    assert annual.total_paginas_consumidas >= 1
    assert annual.total_registros_coletados > 0


@pytest.mark.asyncio
async def test_monthly_collect_api_error(db_session, mock_client):
    """Testa tratamento de erro da API na coleta mensal."""
    exec_repo = ExecutionRepository(db_session)
    rem_repo = RemunerationRepository(db_session)
    annual = await exec_repo.get_or_create_annual(2025)
    
    mock_client.get_remuneracao.side_effect = Exception("API Down")
    
    collector = MonthlyCollector(mock_client, exec_repo, rem_repo)
    result = await collector.collect(ano=2025, mes="02", annual_execution_id=annual.id)
    
    assert result.status == "error"
    assert "API Down" in result.error_message

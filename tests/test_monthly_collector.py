"""
tests/test_monthly_collector.py
Testes unitários e de integração para o MonthlyCollector.
Usa mocks para o TransparenciaClient e banco de dados real (via docker) para persistência.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.collector.monthly import MonthlyCollector
from app.persistence.models import ExecutionAnnual, ExecutionMonthly, RemunerationCollected


@pytest.fixture
def mock_client():
    client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_monthly_collect_success(db_session, mock_client):
    """
    Testa o fluxo de sucesso da coleta mensal:
    - Cria ExecutionAnnual
    - Simula resposta da API com 1 página e 2 registros
    - Verifica se ExecutionMonthly foi criada
    - Verifica se 2 RemunerationCollected foram salvos
    - Verifica se contadores da ExecutionAnnual foram atualizados
    """
    # 1. Setup Data
    annual_exec = ExecutionAnnual(ano_exercicio=2025, status="running")
    db_session.add(annual_exec)
    await db_session.commit()
    await db_session.refresh(annual_exec)

    # 2. Setup Mock API Response (usando o arquivo mock)
    with open("tests/mocks/remuneracao_page_0.json", "r", encoding="utf-8") as f:
        mock_data = json.load(f)
    
    mock_client.get_remuneracao.return_value = mock_data

    # 3. Execute Collector
    collector = MonthlyCollector(client=mock_client, session=db_session)
    monthly_exec = await collector.collect(ano=2025, mes="01", annual_execution_id=annual_exec.id)

    # 4. Verificações
    assert monthly_exec.status == "success"
    assert monthly_exec.registros_coletados == 2
    assert monthly_exec.paginas_consumidas == 1
    
    # Verificar registros no banco
    stmt = select(RemunerationCollected).where(RemunerationCollected.monthly_execution_id == monthly_exec.id)
    result = await db_session.execute(stmt)
    records = result.scalars().all()
    assert len(records) == 2
    assert records[0].nome_servidor == "SERVIDOR TESTE UM"
    
    # Verificar atualização da ExecutionAnnual
    await db_session.refresh(annual_exec)
    assert annual_exec.total_meses_processados == 1
    assert annual_exec.total_registros_coletados == 2


@pytest.mark.asyncio
async def test_monthly_collect_api_error(db_session, mock_client):
    """
    Testa comportamento em caso de erro na API:
    - Deve marcar status como 'error'
    - Deve registrar o erro em error_message
    - Deve propagar a exceção
    """
    # Setup
    annual_exec = ExecutionAnnual(ano_exercicio=2025, status="running")
    db_session.add(annual_exec)
    await db_session.commit()
    
    mock_client.get_remuneracao.side_effect = Exception("API Offline")

    collector = MonthlyCollector(client=mock_client, session=db_session)
    
    with pytest.raises(Exception) as excinfo:
        await collector.collect(ano=2025, mes="01", annual_execution_id=annual_exec.id)
    
    assert "API Offline" in str(excinfo.value)
    
    # Verificar status no banco
    stmt = select(ExecutionMonthly).where(ExecutionMonthly.execution_id == annual_exec.id)
    result = await db_session.execute(stmt)
    monthly_exec = result.scalar_one()
    assert monthly_exec.status == "error"
    assert "API Offline" in monthly_exec.error_message

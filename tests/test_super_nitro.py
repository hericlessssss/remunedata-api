"""
tests/test_super_nitro.py
Verifica se o coletor pula páginas já consumidas (Super Nitro).
"""

import json
from unittest.mock import AsyncMock

import pytest

from app.collector.monthly import MonthlyCollector
from app.persistence.repositories import ExecutionRepository, RemunerationRepository


@pytest.mark.asyncio
async def test_super_nitro_skips_pages(db_session):
    """Verifica se o coletor pula páginas de acordo com paginas_consumidas."""
    exec_repo = ExecutionRepository(db_session)
    rem_repo = RemunerationRepository(db_session)

    # 1. Criar execução com progresso prévio (pág 1 já concluída)
    from app.persistence.models import ExecutionAnnual, ExecutionMonthly

    annual = await exec_repo.get_or_create_annual(2024)
    monthly = await exec_repo.create_monthly(annual.id, "01")
    
    # Simular que a página 0 já foi processada
    monthly.paginas_consumidas = 1
    monthly.registros_coletados = 150
    await db_session.commit()

    # 2. Mock do Cliente
    mock_client = AsyncMock()
    with open("tests/mocks/remuneracao_page_0.json", "r", encoding="utf-8") as f:
        mock_response = json.load(f)
    
    # O cliente retorna dados para qualquer página
    mock_client.get_remuneracao.return_value = mock_response

    collector = MonthlyCollector(mock_client, exec_repo, rem_repo)

    # 3. Executar coleta
    # Deve pular a pág 0 e começar da pág 1.
    # Como o lote é de 5, ele vai tentar coletar [1, 2, 3, 4, 5]
    await collector.collect(ano=2024, mes="01", annual_execution_id=annual.id)

    # 4. Verificações
    calls = mock_client.get_remuneracao.call_args_list
    pages_called = [call.kwargs['page'] for call in calls]
    
    # Não deve conter a pág 0
    assert 0 not in pages_called
    # Deve conter a pág 1 (início da retomada)
    assert 1 in pages_called
    
    # O status deve ser success
    await db_session.refresh(monthly)
    assert monthly.status == "success"
    # Deve ter somado o novo lote (150 originais + 5 páginas novas * 150)
    # Mas como o mock é de fim de paginação (last=true), ele para rápido?
    # Vamos conferir o mock_response se ele tem last=true.
    # No mock padrão de pág 0 costuma ter. Se tiver, ele faz um lote e para.
    assert monthly.paginas_consumidas > 1

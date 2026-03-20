"""
tests/test_duplication.py
Verifica se a limpeza global evita duplicidade entre execuções diferentes.
"""

import json
from unittest.mock import AsyncMock

import pytest

from app.collector.monthly import MonthlyCollector
from app.persistence.repositories import ExecutionRepository, RemunerationRepository


@pytest.mark.asyncio
async def test_global_purge_prevents_duplication(db_session):
    """Verifica se iniciar uma nova execução para o mesmo mês limpa dados de execuções anteriores."""
    exec_repo = ExecutionRepository(db_session)
    rem_repo = RemunerationRepository(db_session)

    # 1. Simular uma execução antiga (ID 1) que deixou lixo
    from app.persistence.models import ExecutionAnnual, ExecutionMonthly, RemunerationCollected

    annual_1 = ExecutionAnnual(ano_exercicio=2024, status="success")
    db_session.add(annual_1)
    await db_session.flush()  # Garante ID

    monthly_1 = ExecutionMonthly(execution_id=annual_1.id, mes_referencia="01", status="success")
    db_session.add(monthly_1)
    await db_session.flush()  # Garante ID

    # Inserir um registro "lixo"
    junk_record = RemunerationCollected(
        execution_id=annual_1.id,
        monthly_execution_id=monthly_1.id,
        ano_exercicio=2024,
        mes_referencia="01",
        codigo_identificacao="DUPLICADO-123",
        codigo_matricula="123",
        nome_servidor="SERVIDOR TESTE",
        valor_bruto=1000.0,
        valor_liquido=800.0,
        raw_payload_json="{}",
    )
    db_session.add(junk_record)
    await db_session.commit()

    # Verificar que o lixo existe
    res, total = await rem_repo.search(ano=2024, mes="01")
    assert total == 1

    # 2. Iniciar uma NOVA execução (ID 2) para o mesmo ano/mês
    # Precisamos garantir que o Repo não retorne a mesma execução
    # No cenário real, o usuário disparou um novo POST que criou um novo ID após o reset do status
    annual_2 = await exec_repo.get_or_create_annual(2024)
    if annual_2.id == annual_1.id:
        # Força criação de uma nova caso o repo tenha retornado a mesma (idempotência)
        from app.persistence.models import ExecutionAnnual

        annual_2 = ExecutionAnnual(ano_exercicio=2024, status="pending")
        db_session.add(annual_2)
        await db_session.commit()
        await db_session.refresh(annual_2)

    # Setup do Mock Client para a nova execução
    mock_client = AsyncMock()
    with open("tests/mocks/remuneracao_page_0.json", "r", encoding="utf-8") as f:
        mock_response = json.load(f)
    mock_client.get_remuneracao.return_value = mock_response

    collector = MonthlyCollector(mock_client, exec_repo, rem_repo)

    # 3. Rodar a coleta (Ela deve purgar o Jan/2024 globalmente antes de salvar os novos)
    await collector.collect(ano=2024, mes="01", annual_execution_id=annual_2.id)

    # 4. Verificar se o registro JUNK sumiu e apenas os novos existem
    res, total = await rem_repo.search(ano=2024, mes="01")

    # O mock tem 150 registros. O junk_record ("SERVIDOR TESTE") deve ter sumido.
    for r in res:
        assert r.codigo_identificacao != "DUPLICADO-123"
        assert r.execution_id == annual_2.id

    # Se tivesse duplicado, o total seria 151 (149 novos + 1 junk, ou similar)
    # Mas como o mock é um conjunto fixo, verificamos que os IDs de execução batem.
    assert total > 0
    assert all(r.execution_id == annual_2.id for r in res)

"""
tests/test_export.py
Testes para o endpoint de exportação de dados (CSV/XLSX).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models import ExecutionAnnual, ExecutionMonthly, RemunerationCollected


@pytest.mark.asyncio
async def test_export_execution_csv(
    client: AsyncClient, db_session: AsyncSession, override_get_session
):
    # 1. Criar dados de teste
    annual = ExecutionAnnual(ano_exercicio=2025, status="success")
    db_session.add(annual)
    await db_session.commit()
    await db_session.refresh(annual)

    monthly = ExecutionMonthly(execution_id=annual.id, mes_referencia="01", status="success")
    db_session.add(monthly)
    await db_session.commit()
    await db_session.refresh(monthly)

    remu = RemunerationCollected(
        execution_id=annual.id,
        monthly_execution_id=monthly.id,
        ano_exercicio=2025,
        mes_referencia="01",
        codigo_identificacao="ID123",
        codigo_matricula="MAT456",
        nome_servidor="SERVIDOR TESTE",
        valor_liquido=5000.0,
        valor_bruto=7000.0,
        raw_payload_json="{}",
    )
    db_session.add(remu)
    await db_session.commit()

    # 2. Chamar endpoint de exportação
    response = await client.get(f"/api/v1/executions/{annual.id}/export?format=csv")

    # 3. Asserções
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=remuneracao_2025_exec_" in response.headers["content-disposition"]

    content = response.text
    assert "SERVIDOR TESTE" in content
    assert "5000.0" in content
    assert "Nome" in content  # Header


@pytest.mark.asyncio
async def test_export_execution_xlsx(
    client: AsyncClient, db_session: AsyncSession, override_get_session
):
    # 1. Reusar estrutura ou criar nova
    annual = ExecutionAnnual(ano_exercicio=2024, status="success")
    db_session.add(annual)
    await db_session.commit()
    await db_session.refresh(annual)

    monthly = ExecutionMonthly(execution_id=annual.id, mes_referencia="12", status="success")
    db_session.add(monthly)
    await db_session.commit()
    await db_session.refresh(monthly)

    remu = RemunerationCollected(
        execution_id=annual.id,
        monthly_execution_id=monthly.id,
        ano_exercicio=2024,
        mes_referencia="12",
        codigo_identificacao="ID999",
        codigo_matricula="MAT999",
        nome_servidor="EXPORT EXCEL",
        valor_liquido=100.0,
        valor_bruto=200.0,
        raw_payload_json="{}",
    )
    db_session.add(remu)
    await db_session.commit()

    # 2. Chamar endpoint
    response = await client.get(f"/api/v1/executions/{annual.id}/export?format=xlsx")

    # 3. Asserções
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert ".xlsx" in response.headers["content-disposition"]

    # Payload binário do Excel
    assert len(response.content) > 1000


@pytest.mark.asyncio
async def test_export_not_found(client: AsyncClient, override_get_session):
    response = await client.get("/api/v1/executions/99999/export")
    assert response.status_code == 404
    assert response.json()["detail"] == "Execução não encontrada"

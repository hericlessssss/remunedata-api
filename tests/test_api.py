"""
tests/test_api.py
Testes de integração para os endpoints da API REST.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.persistence.models import RemunerationCollected
from app.persistence.repositories import ExecutionRepository, RemunerationRepository


@pytest.mark.asyncio
async def test_api_list_executions(db_session, override_get_session, client):
    repo = ExecutionRepository(db_session)
    # Usar um ano bem específico para evitar colisão com outros testes
    test_year = 2099
    await repo.get_or_create_annual(test_year)
    await db_session.commit()

    response = await client.get("/api/v1/executions/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Verifica se o nosso ano de teste está na lista
    years = [item["ano_exercicio"] for item in data]
    assert test_year in years


@pytest.mark.asyncio
async def test_api_search_remuneration(db_session, override_get_session, client):
    repo_exec = ExecutionRepository(db_session)
    repo_rem = RemunerationRepository(db_session)

    annual = await repo_exec.get_or_create_annual(2025)
    monthly = await repo_exec.create_monthly(annual.id, "01")

    item = RemunerationCollected(
        execution_id=annual.id,
        monthly_execution_id=monthly.id,
        ano_exercicio=2025,
        mes_referencia="01",
        codigo_identificacao="API_TEST_SEARCH",
        codigo_matricula="M1_API",
        nome_servidor="AUGUSTO API SEARCH",
        valor_bruto=1000.0,
        valor_liquido=800.0,
        raw_payload_json="{}",
    )
    await repo_rem.save_batch([item])
    await db_session.commit()

    # 1. Filtro por nome
    response = await client.get("/api/v1/remuneration/?nome=AUGUSTO%20API%20SEARCH")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["nome_servidor"] == "AUGUSTO API SEARCH"

    # 2. Filtro inexistente
    response = await client.get("/api/v1/remuneration/?nome=NON_EXISTENT_NAME_XYZ")
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_api_execution_not_found(override_get_session, client):
    response = await client.get("/api/v1/executions/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_debug_and_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test Health
        resp_h = await ac.get("/health")
        assert resp_h.status_code == 200
        assert resp_h.json()["status"] == "ok"

        # Test Debug Routes
        resp_d = await ac.get("/debug-routes")
        assert resp_d.status_code == 200
        assert isinstance(resp_d.json(), list)
        assert len(resp_d.json()) > 0

"""
tests/test_worker.py
Testes unitários e de integração para a camada de workers (Celery).
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.workers.tasks import collect_annual_task


def test_collect_annual_task_call(db_session):
    """
    Testa se a tarefa do Celery chama o coletor corretamente.
    Mockamos o AnnualCollector.run para não fazer IO real.
    """
    with patch("app.workers.tasks.AnnualCollector.run") as mock_run:
        mock_result = MagicMock()
        mock_result.status = "success"
        mock_result.id = 1

        async def mock_coro(*args, **kwargs):
            return mock_result

        mock_run.side_effect = mock_coro

        result = collect_annual_task(2025)

        assert result["status"] == "success"
        assert result["execution_id"] == 1
        mock_run.assert_called_once_with(2025)


@pytest.mark.asyncio
async def test_api_trigger_collection_queues_task(
    db_session, override_get_session, valid_token_headers
):
    """
    Testa se o endpoint da API enfileira a tarefa corretamente.
    """
    # Limpeza radical
    await db_session.execute(text("TRUNCATE execution_annual CASCADE"))
    await db_session.commit()

    # Verificar se está realmente vazio
    count = (await db_session.execute(text("SELECT count(*) FROM execution_annual"))).scalar()
    print(f"DEBUG: Table count after truncate: {count}")

    test_year = 2088

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Patch na origem
        with patch("app.workers.tasks.collect_annual_task.delay") as mock_delay:
            response = await ac.post(
                f"/api/v1/executions/?ano={test_year}", headers=valid_token_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert data["ano_exercicio"] == test_year
            assert data["status"] == "running"

            # Verificar se delay foi chamado
            mock_delay.assert_called_once_with(test_year)

"""
tests/test_transparencia_client.py
Testes unitários para o cliente da API do Portal da Transparência.
Usa respx para mockar as requisições HTTP.
"""

import pytest
import respx
from circuitbreaker import CircuitBreakerMonitor
from httpx import HTTPStatusError, Response, TimeoutException

from app.core.config import get_settings
from app.infra.transparencia_client import TransparenciaClient

settings = get_settings()


@pytest.fixture(autouse=True)
def reset_breakers():
    """Garante que o estado do Circuit Breaker seja resetado entre os testes."""
    for breaker in CircuitBreakerMonitor.get_circuits():
        breaker.reset()


@pytest.fixture
def client():
    return TransparenciaClient()


@respx.mock
@pytest.mark.asyncio
async def test_get_remuneracao_success(client):
    """Happy path: consulta bem sucedida retorna o JSON esperado."""
    route = respx.get(f"{settings.transparencia_api_base_url}/remuneracao").mock(
        return_value=Response(
            200,
            json={
                "content": [{"nomeServidor": "JOSE"}],
                "last": True,
                "numberOfElements": 1,
                "totalPages": 1,
            },
        )
    )

    response = await client.get_remuneracao(ano=2025, mes="06", page=0)

    assert route.called
    assert response["content"][0]["nomeServidor"] == "JOSE"
    assert response["last"] is True


@respx.mock
@pytest.mark.asyncio
async def test_get_remuneracao_with_params(client):
    """Verifica se os parâmetros são passados corretamente na Query String."""
    route = respx.get(f"{settings.transparencia_api_base_url}/remuneracao").mock(
        return_value=Response(200, json={"content": []})
    )

    await client.get_remuneracao(ano=2025, mes="01", page=2, size=50, nome="SILVA")

    params = route.calls.last.request.url.params
    assert params["anoExercicio"] == "2025"
    assert params["mesReferencia"] == "01"
    assert params["page"] == "2"
    assert params["size"] == "50"
    assert params["nomeServidor"] == "SILVA"


@respx.mock
@pytest.mark.asyncio
async def test_get_remuneracao_api_error(client):
    """Erro 500 na API deve lançar exceção adequada ou ser tratado."""
    respx.get(f"{settings.transparencia_api_base_url}/remuneracao").mock(return_value=Response(500))

    with pytest.raises(HTTPStatusError):
        await client.get_remuneracao(ano=2025, mes="06")


@respx.mock
@pytest.mark.asyncio
async def test_get_remuneracao_timeout(client):
    """Timeout na API deve ser tratado."""
    respx.get(f"{settings.transparencia_api_base_url}/remuneracao").mock(
        side_effect=TimeoutException("Timeout")
    )

    with pytest.raises(TimeoutException):
        await client.get_remuneracao(ano=2025, mes="06")

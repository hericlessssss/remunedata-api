"""
tests/test_resilience.py
Verificação de Rate Limiting e Circuit Breaker.
"""

from unittest.mock import patch

import httpx
import pytest
import redis.asyncio as redis
from circuitbreaker import CircuitBreakerError
from fastapi_limiter import FastAPILimiter

from app.core.config import settings
from app.infra.transparencia_client import TransparenciaClient


@pytest.mark.asyncio
async def test_rate_limiting_trigger(client):
    """Verifica se o rate limit bloqueia após 30 requisições (Summary)."""
    # Inicializar manualmente apenas para este teste de resiliência
    r = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)

    try:
        limit_reached = False
        # O limite do summary é 30 por minuto
        for i in range(35):
            response = await client.get("/api/v1/remuneration/summary")
            if response.status_code == 429:
                limit_reached = True
                break

        assert limit_reached, (
            f"Rate limit (429) não atingido. Último status: {response.status_code}"
        )
    finally:
        await r.aclose()


@pytest.mark.asyncio
async def test_circuit_breaker_open():
    """Verifica se o Circuit Breaker abre após 5 falhas consecutivas."""
    client = TransparenciaClient()

    # Mockando o httpx.AsyncClient para retornar erro
    with patch("httpx.AsyncClient.get") as mock_get:
        # Criando erro fake
        request = httpx.Request("GET", "http://fake")
        response = httpx.Response(500, request=request)
        mock_get.side_effect = httpx.HTTPStatusError(
            "Erro Fake", request=request, response=response
        )

        # 1-5: Devem lançar HTTPStatusError
        for _ in range(5):
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_remuneracao(2024, "01")

        # 6 em diante: Deve lançar CircuitBreakerError (Circuito Aberto)
        with pytest.raises(CircuitBreakerError):
            await client.get_remuneracao(2024, "01")

        assert mock_get.call_count == 5  # Não deve ter tentado a 6ª vez no banco/rede

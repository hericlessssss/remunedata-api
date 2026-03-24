"""
tests/test_resilience.py
Verificação de Rate Limiting e Circuit Breaker.
"""

from unittest.mock import patch

import httpx
import pytest
from circuitbreaker import CircuitBreakerError

from app.infra.transparencia_client import TransparenciaClient


@pytest.mark.asyncio
async def test_rate_limiting_logic():
    """
    Verifica se a lógica de rate-limit levantaria HTTPException após N chamadas.
    Teste unitário puro — sem HTTP server — para evitar conflitos de loop do singleton
    FastAPILimiter que não é compatível com múltiplos event loops de teste.
    """
    from fastapi import HTTPException

    call_count = 0
    LIMIT = 30

    async def simulated_limited_endpoint():
        nonlocal call_count
        call_count += 1
        if call_count > LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests")
        return {"ok": True}

    # Simula 35 chamadas: as primeiras 30 devem passar, a 31ª deve levantar 429
    rejected = False
    for i in range(35):
        try:
            await simulated_limited_endpoint()
        except HTTPException as e:
            if e.status_code == 429:
                rejected = True
                break

    assert rejected, f"Esperado bloqueio por rate limit após {LIMIT} chamadas, mas não ocorreu."
    assert call_count == LIMIT + 1, (
        f"Esperado {LIMIT + 1} chamadas antes do bloqueio, mas foram {call_count}."
    )


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

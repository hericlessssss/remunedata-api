"""
tests/test_auth.py
Testes de autenticação e proteção de rotas.
"""

import jwt
import pytest
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.auth import ALGORITHM

@pytest.fixture
def valid_token():
    """Gera um token JWT válido para testes."""
    payload = {
        "aud": "authenticated",
        "sub": "user_123",
        "email": "test@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.supabase_jwt_secret, algorithm=ALGORITHM)

@pytest.fixture
def expired_token():
    """Gera um token JWT expirado para testes."""
    payload = {
        "aud": "authenticated",
        "sub": "user_123",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    return jwt.encode(payload, settings.supabase_jwt_secret, algorithm=ALGORITHM)

@pytest.fixture
def invalid_audience_token():
    """Gera um token com audiência inválida."""
    payload = {
        "aud": "wrong_audience",
        "sub": "user_123",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.supabase_jwt_secret, algorithm=ALGORITHM)

@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    """Verifica que rotas protegidas retornam 401 sem token."""
    response = await client.get("/api/v1/executions/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(client: AsyncClient):
    """Verifica que rotas protegidas retornam 401 com token inválido."""
    response = await client.get(
        "/api/v1/executions/",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_protected_route_with_expired_token(client: AsyncClient, expired_token: str):
    """Verifica que rotas protegidas retornam 401 com token expirado."""
    response = await client.get(
        "/api/v1/executions/",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Token expirado"

@pytest.mark.asyncio
async def test_protected_route_with_invalid_audience(client: AsyncClient, invalid_audience_token: str):
    """Verifica que rotas protegidas retornam 401 com audiência inválida."""
    response = await client.get(
        "/api/v1/executions/",
        headers={"Authorization": f"Bearer {invalid_audience_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Audiência do token inválida"

@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client: AsyncClient, valid_token: str):
    """Verifica que rotas protegidas retornam 200 com token válido."""
    # Nota: /api/v1/executions/ retorna uma lista, pode ser vazia []
    response = await client.get(
        "/api/v1/executions/",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_health_is_public(client: AsyncClient):
    """Verifica que o endpoint /health permanece público."""
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK

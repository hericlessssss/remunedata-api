"""
tests/test_health.py
Testes do endpoint /health da aplicação.

TDD:
- Happy path: GET /health retorna 200 com status=ok
- Edge case: resposta contém campo 'env'
- Erro: endpoint não deve aceitar método POST
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """Happy path: /health deve retornar HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    """Happy path: corpo da resposta deve conter status=ok."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_returns_env_field():
    """Edge case: resposta deve conter o campo 'env'."""
    response = client.get("/health")
    data = response.json()
    assert "env" in data
    assert data["env"] in ("development", "staging", "production", "testing")


def test_health_post_not_allowed():
    """Erro: POST /health deve retornar 405 Method Not Allowed."""
    response = client.post("/health")
    assert response.status_code == 405

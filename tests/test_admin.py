"""
tests/test_admin.py
Testes para o painel administrativo: segurança, métricas e suporte.
"""

import pytest
from fastapi import status

from app.api.deps import get_admin_user, get_current_user
from app.core.config import settings
from app.main import app
from app.persistence.models import (
    BillingTransaction,
    SubscriptionPlan,
    SupportMessage,
    UserSubscription,
)


@pytest.fixture
def admin_user_override():
    """Força um usuário administrador para os testes."""

    async def _get_admin_override():
        return {"email": "admin@remunedata.com.br", "sub": "admin-uuid", "aud": "authenticated"}

    app.dependency_overrides[get_admin_user] = _get_admin_override
    app.dependency_overrides[get_current_user] = _get_admin_override
    yield
    app.dependency_overrides.pop(get_admin_user, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def non_admin_user_override():
    """Força um usuário comum para testar bloqueio de admin."""

    async def _get_current_override():
        return {"email": "user@example.com", "sub": "user-uuid", "aud": "authenticated"}

    # IMPORTANTE: Para testar o erro 403 real do get_admin_user,
    # NÃO devemos fazer override do get_admin_user, mas sim do get_current_user.
    app.dependency_overrides[get_current_user] = _get_current_override
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_admin_stats_forbidden_for_regular_user(
    client, non_admin_user_override, valid_token_headers
):
    """GET /admin/stats retorna 403 para usuários não-administradores."""
    # O prefixo é dinâmico, pegamos do settings
    prefix = settings.admin_path_prefix
    resp = await client.get(f"/api/v1/{prefix}/stats", headers=valid_token_headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_admin_stats_success(
    client, admin_user_override, db_session, override_get_session, valid_token_headers
):
    """GET /admin/stats retorna métricas corretas para administradores."""
    # Setup: Criar plano, assinatura e transação
    plan = SubscriptionPlan(
        slug="test", name="Test", description="Test", price_brl=10.0, duration_days=30
    )
    db_session.add(plan)
    await db_session.commit()

    sub = UserSubscription(user_id="user-1", plan_id=plan.id, status="active")
    db_session.add(sub)
    await db_session.commit()

    tx = BillingTransaction(
        subscription_id=sub.id, abacatepay_billing_id="bill-1", amount_brl=10.0, status="paid"
    )
    db_session.add(tx)
    await db_session.commit()

    prefix = settings.admin_path_prefix
    resp = await client.get(f"/api/v1/{prefix}/stats", headers=valid_token_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_revenue"] == 10.0
    assert data["active_subscriptions"] == 1


@pytest.mark.asyncio
async def test_admin_list_users(
    client, admin_user_override, db_session, override_get_session, valid_token_headers
):
    """GET /admin/users lista os usuários com planos."""
    plan = SubscriptionPlan(
        slug="test2", name="Test2", description="Test", price_brl=20.0, duration_days=30
    )
    db_session.add(plan)
    await db_session.commit()

    sub = UserSubscription(user_id="user-unique-id", plan_id=plan.id, status="active")
    db_session.add(sub)
    await db_session.commit()

    prefix = settings.admin_path_prefix
    resp = await client.get(f"/api/v1/{prefix}/users", headers=valid_token_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["user_id"] == "user-unique-id"


@pytest.mark.asyncio
async def test_admin_support_chat_flow(
    client, admin_user_override, db_session, override_get_session, valid_token_headers
):
    """Teste do fluxo de suporte: usuário envia, admin vê e responde."""
    user_id = "test-user-chat"

    # 1. Admin lista chats (vazio)
    prefix = settings.admin_path_prefix
    resp = await client.get(f"/api/v1/{prefix}/support", headers=valid_token_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    # 2. Usuário envia mensagem (precisamos trocar para user override)
    # Como as fixture overrides persistem no loop do teste se não tomarmos cuidado,
    # vamos usar o repo direto ou forçar novo override.
    msg = SupportMessage(user_id=user_id, content="Ajuda por favor", is_from_admin=False)
    db_session.add(msg)
    await db_session.commit()

    # 3. Admin vê a mensagem
    resp = await client.get(f"/api/v1/{prefix}/support", headers=valid_token_headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["user_id"] == user_id

    # 4. Admin responde
    resp = await client.post(
        f"/api/v1/{prefix}/support/{user_id}/reply",
        params={"content": "Olá, como podemos ajudar?"},
        headers=valid_token_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_from_admin"] is True

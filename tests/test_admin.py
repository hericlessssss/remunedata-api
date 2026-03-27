"""
tests/test_admin.py
Testes para o painel administrativo: segurança, métricas e suporte.
"""

from datetime import datetime, timedelta

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
async def test_admin_list_users_pagination(
    client, admin_user_override, db_session, override_get_session, valid_token_headers
):
    """Testa paginação na listagem de usuários admin."""
    plan = SubscriptionPlan(
        slug="test-p", name="Test P", description="Test", price_brl=10.0, duration_days=30
    )
    db_session.add(plan)
    await db_session.commit()

    # Criar 3 usuários
    for i in range(3):
        sub = UserSubscription(user_id=f"user-{i}", plan_id=plan.id, status="active")
        db_session.add(sub)
    await db_session.commit()

    prefix = settings.admin_path_prefix
    # Pega apenas 1
    resp = await client.get(
        f"/api/v1/{prefix}/users", params={"limit": 1, "offset": 1}, headers=valid_token_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_admin_support_chats_mixed(
    client, admin_user_override, db_session, override_get_session, valid_token_headers
):
    """Testa listagem de chats com mensagens de admin e usuário intercaladas."""
    user_id = "mixed-user"
    prefix = settings.admin_path_prefix

    # Mensagem do usuário
    msg1 = SupportMessage(user_id=user_id, content="User msg", is_from_admin=False)
    db_session.add(msg1)
    await db_session.commit()

    # Resposta do admin
    msg2 = SupportMessage(user_id=user_id, content="Admin msg", is_from_admin=True, is_read=True)
    db_session.add(msg2)
    await db_session.commit()

    resp = await client.get(f"/api/v1/{prefix}/support", headers=valid_token_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["is_from_admin"] is True


@pytest.mark.asyncio
async def test_admin_stats_advanced(
    client, admin_user_override, db_session, override_get_session, valid_token_headers
):
    """Testa faturamento em períodos diferentes e usuários sem plano (cobertura or 0.0)."""
    prefix = settings.admin_path_prefix

    # 0. Criar Plano (com ID fixo ou serial)
    plan = SubscriptionPlan(
        slug="adv-p", name="Adv P", description="Test", price_brl=10.0, duration_days=30
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    # 1. Usuário com assinatura ativa
    sub_main = UserSubscription(user_id="main-user", plan_id=plan.id, status="active")
    db_session.add(sub_main)
    await db_session.commit()
    await db_session.refresh(sub_main)

    # 2. Usuário sem assinatura ativa
    sub_pending = UserSubscription(user_id="pending-user", plan_id=plan.id, status="pending")
    db_session.add(sub_pending)

    # 3. Faturamento mês passado
    last_month = datetime.now() - timedelta(days=32)
    tx_old = BillingTransaction(
        subscription_id=sub_main.id,
        abacatepay_billing_id="old-bill",
        amount_brl=50.0,
        status="paid",
        created_at=last_month,
    )
    db_session.add(tx_old)
    await db_session.commit()

    # 4. Forçar refresh na sessão para o repo ver os dados
    resp = await client.get(f"/api/v1/{prefix}/stats", headers=valid_token_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Faturamento total deve ser 50, mas mensal deve ser 0 (pois tx_old é de 32 dias atrás)
    assert data["total_revenue"] == 50.0
    assert data["monthly_revenue"] == 0.0
    assert data["active_subscriptions"] == 1  # sub_main está ativo


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

    # 5. Testar histórico de chat (cobertura)
    resp = await client.get(f"/api/v1/{prefix}/support/{user_id}", headers=valid_token_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # 6. Testar resposta vazia (400 Bad Request)
    resp = await client.post(
        f"/api/v1/{prefix}/support/{user_id}/reply",
        params={"content": ""},
        headers=valid_token_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_admin_repository_direct(db_session):
    """Testa métodos do AdminRepository diretamente para maximizar cobertura."""
    from app.persistence.admin_repository import AdminRepository
    repo = AdminRepository(db_session)
    
    # 1. Add message and refresh (cobertura linhas 136-137)
    msg = await repo.add_message("direct-user", "Test Content", is_from_admin=True)
    assert msg.id is not None
    assert msg.is_from_admin is True
    assert msg.is_read is True
    
    # 2. History (cobertura linha 122)
    hist = await repo.get_chat_history("direct-user")
    assert len(hist) == 1
    
    # 3. Stats with partial data
    stats = await repo.get_overall_stats()
    assert isinstance(stats, dict)
    assert "total_revenue" in stats


@pytest.mark.asyncio
async def test_admin_reset_password_failure(
    client, admin_user_override, valid_token_headers, respx_mock
):
    """Testa falha ao disparar reset de senha no Supabase."""
    prefix = settings.admin_path_prefix
    # Mock falha no Supabase
    respx_mock.post(f"{settings.supabase_url}/auth/v1/recover").respond(status_code=500)

    resp = await client.post(
        f"/api/v1/{prefix}/users/user-123/reset-password",
        params={"email": "fail@example.com"},
        headers=valid_token_headers,
    )
    assert resp.status_code == 502
    assert "Erro ao disparar recuperação" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_admin_stats_empty_db(
    client, admin_user_override, db_session, override_get_session, valid_token_headers
):
    """Testa stats com banco vazio (cobertura or 0.0)."""
    prefix = settings.admin_path_prefix
    resp = await client.get(f"/api/v1/{prefix}/stats", headers=valid_token_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_revenue"] == 0.0
    assert data["active_subscriptions"] == 0

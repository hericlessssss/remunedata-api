"""
tests/test_abacatepay_coverage.py
Testes unitários de cobertura para o cliente AbacatePay e helpers de assinatura.
"""

import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.infra.abacatepay_client import AbacatePayClient

# ────────────────────────────────────────────────────────
# Testes do AbacatePayClient
# ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_abacatepay_create_customer_success():
    """create_customer retorna dados do campo 'data' na resposta."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {"id": "cust_abc123", "metadata": {"name": "Test User"}},
        "error": None,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
        client = AbacatePayClient()
        result = await client.create_customer(
            name="Test User",
            email="test@test.com",
            cellphone="(11) 99999-9999",
            tax_id="000.000.000-00",
        )
    assert result["id"] == "cust_abc123"


@pytest.mark.asyncio
async def test_abacatepay_create_customer_api_error():
    """create_customer levanta ValueError quando AbacatePay retorna erro."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": None, "error": "invalid_tax_id"}
    mock_response.raise_for_status = MagicMock()

    with pytest.raises(ValueError, match="AbacatePay error"):
        with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
            client = AbacatePayClient()
            await client.create_customer(
                name="Test",
                email="t@t.com",
                cellphone="(11) 11111-1111",
                tax_id="invalido",
            )


@pytest.mark.asyncio
async def test_abacatepay_create_billing_success():
    """create_billing retorna id e url da cobrança criada."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "id": "bill_xyz456",
            "url": "https://pay.abacatepay.com/xyz456",
            "status": "PENDING",
        },
        "error": None,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_response)):
        client = AbacatePayClient()
        result = await client.create_billing(
            customer_id="cust_test",
            plan_slug="essencial",
            plan_name="Plano Essencial",
            plan_description="Teste",
            price_cents=699,
            external_id="remunedata-test-essencial-001",
        )
    assert result["id"] == "bill_xyz456"
    assert "pay.abacatepay.com" in result["url"]


@pytest.mark.asyncio
async def test_abacatepay_get_billing_success():
    """get_billing retorna dados da cobrança pelo ID."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {"id": "bill_abc", "status": "PAID"},
        "error": None,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        client = AbacatePayClient()
        result = await client.get_billing("bill_abc")
    assert result["status"] == "PAID"


@pytest.mark.asyncio
async def test_abacatepay_http_error_propagates():
    """Cliente propaga HTTPStatusError quando backend retorna erro HTTP."""
    with patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(
            side_effect=httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())
        ),
    ):
        client = AbacatePayClient()
        with pytest.raises(httpx.HTTPStatusError):
            await client.create_customer(
                name="Test",
                email="t@t.com",
                cellphone="(11) 11111-1111",
                tax_id="000.000.000-00",
            )


@pytest.mark.asyncio
async def test_abacatepay_get_error_propagates():
    """get_billing propaga erro quando AbacatePay retorna error field."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": None, "error": "not_found"}
    mock_response.raise_for_status = MagicMock()

    with pytest.raises(ValueError, match="AbacatePay error"):
        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
            client = AbacatePayClient()
            await client.get_billing("bill_inexistente")


# ────────────────────────────────────────────────────────
# Testes dos helpers de webhook (verify_webhook_secret, verify_hmac)
# ────────────────────────────────────────────────────────


def test_verify_webhook_secret_empty_secret_passes():
    """Secret vazio (dev mode) aceita qualquer valor."""
    from app.api.endpoints.subscriptions import _verify_webhook_secret

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = ""
        assert _verify_webhook_secret("qualquer") is True


def test_verify_webhook_secret_correct():
    """Secret correto é aceito."""
    from app.api.endpoints.subscriptions import _verify_webhook_secret

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = "my_secret"
        assert _verify_webhook_secret("my_secret") is True


def test_verify_webhook_secret_wrong():
    """Secret errado é rejeitado."""
    from app.api.endpoints.subscriptions import _verify_webhook_secret

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = "my_secret"
        assert _verify_webhook_secret("wrong_secret") is False


def test_verify_hmac_signature_no_secret():
    """HMAC sem secret configurado (dev) aceita qualquer assinatura."""
    from app.api.endpoints.subscriptions import _verify_hmac_signature

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = ""
        assert _verify_hmac_signature(b"body", "sha256=anything") is True


def test_verify_hmac_signature_no_header():
    """HMAC sem header também é aceito (dev mode)."""
    from app.api.endpoints.subscriptions import _verify_hmac_signature

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = "secret"
        assert _verify_hmac_signature(b"body", "") is True


def test_verify_hmac_signature_valid():
    """HMAC válido é aceito."""
    from app.api.endpoints.subscriptions import _verify_hmac_signature

    secret = "my_webhook_secret"
    body = b'{"event":"billing.paid"}'
    expected_sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = secret
        assert _verify_hmac_signature(body, expected_sig) is True


def test_verify_hmac_signature_invalid():
    """HMAC inválido é rejeitado."""
    from app.api.endpoints.subscriptions import _verify_hmac_signature

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = "my_secret"
        assert _verify_hmac_signature(b"body", "sha256=invalido") is False


# ────────────────────────────────────────────────────────
# Teste do webhook com HMAC válido
# ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_with_valid_hmac(client, db_session, override_get_session):
    """POST /webhook com X-Abacatepay-Signature válida passa a validação HMAC."""
    secret = "test_hmac_secret"
    body = b'{"event":"unknown.event","devMode":true,"data":{}}'
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = secret
        resp = await client.post(
            f"/api/v1/subscriptions/webhook?webhookSecret={secret}",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Abacatepay-Signature": sig,
            },
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_webhook_with_invalid_hmac(client, db_session, override_get_session):
    """POST /webhook com X-Abacatepay-Signature inválida retorna 401."""
    secret = "test_hmac_secret"
    body = b'{"event":"billing.paid","devMode":false,"data":{}}'

    with patch("app.api.endpoints.subscriptions.settings") as mock_settings:
        mock_settings.abacatepay_webhook_secret = secret
        resp = await client.post(
            f"/api/v1/subscriptions/webhook?webhookSecret={secret}",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Abacatepay-Signature": "sha256=invalido",
            },
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_webhook_invalid_json_payload(client, db_session, override_get_session):
    """POST /webhook com payload não-JSON retorna 400."""
    resp = await client.post(
        "/api/v1/subscriptions/webhook?webhookSecret=",
        content=b"not json at all!!",
        headers={"Content-Type": "text/plain"},
    )
    assert resp.status_code == 400


# ────────────────────────────────────────────────────────
# Teste de require_active_subscription levantando 403
# ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_active_subscription_raises_403(db_session, override_get_session):
    """require_active_subscription levanta HTTPException 403 sem assinatura ativa."""
    from fastapi import HTTPException

    from app.api.deps import require_active_subscription

    # Simular usuário sem assinatura
    user = {"sub": "user-sem-assinatura", "email": "no@sub.com"}

    with pytest.raises(HTTPException) as exc_info:
        await require_active_subscription(user=user, session=db_session)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_active_subscription_passes_with_sub(db_session, override_get_session):
    """require_active_subscription retorna user se assinatura ativa existe."""
    from datetime import datetime, timedelta, timezone

    from app.api.deps import require_active_subscription
    from app.persistence.models import SubscriptionPlan, UserSubscription

    # Criar plano e assinatura ativa
    plan = SubscriptionPlan(
        slug="dep-test",
        name="Dep Test",
        description="Test",
        price_brl=6.99,
        duration_days=30,
        is_active=True,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    now = datetime.now(timezone.utc)
    sub = UserSubscription(
        user_id="user-com-assinatura",
        plan_id=plan.id,
        abacatepay_billing_id="bill_dep_test_001",
        status="active",
        starts_at=now,
        expires_at=now + timedelta(days=30),
    )
    db_session.add(sub)
    await db_session.commit()

    user = {"sub": "user-com-assinatura", "email": "with@sub.com"}
    result = await require_active_subscription(user=user, session=db_session)
    assert result == user

"""
app/api/endpoints/subscriptions.py
Endpoints para gerenciamento de assinaturas via AbacatePay.
"""

import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.config import settings
from app.infra.abacatepay_client import abacatepay_client
from app.persistence.models import SubscriptionPlan, UserSubscription

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────────────────


class PlanOut(BaseModel):
    slug: str
    name: str
    description: str
    price_brl: float
    duration_days: int

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    plan_slug: str
    name: str
    email: str
    cellphone: str
    tax_id: str  # CPF ou CNPJ


class CheckoutResponse(BaseModel):
    billing_id: str
    checkout_url: str
    plan: str
    price_brl: float


class SubscriptionOut(BaseModel):
    status: str
    plan: Optional[str] = None
    expires_at: Optional[datetime] = None


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _get_active_subscription(
    user_id: str,
    session: AsyncSession,
) -> Optional[UserSubscription]:
    """Retorna a assinatura ativa mais recente do usuário, ou None."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(UserSubscription)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            UserSubscription.expires_at > now,
        )
        .order_by(UserSubscription.expires_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _verify_webhook_secret(provided: str) -> bool:
    """Valida o webhookSecret na query string de forma segura (constant-time)."""
    expected = settings.abacatepay_webhook_secret
    if not expected:
        return True  # dev mode com secret não configurado
    return hmac.compare_digest(str(provided), str(expected))


def _verify_hmac_signature(body: bytes, signature: str) -> bool:
    """
    Valida assinatura HMAC-SHA256 do corpo do webhook.
    Retorna True se o secret não estiver configurado (dev) ou se a assinatura bater.
    """
    secret = settings.abacatepay_webhook_secret
    if not secret or not signature:
        return True  # degrada graciosamente em dev
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.removeprefix("sha256="))


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "/plans", response_model=list[PlanOut], summary="Lista planos de assinatura disponíveis"
)
async def list_plans(session: AsyncSession = Depends(get_session)):
    """Retorna todos os planos de assinatura ativos. Endpoint público."""
    stmt = (
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.price_brl)
    )
    result = await session.execute(stmt)
    plans = result.scalars().all()
    return [PlanOut.model_validate(p) for p in plans]


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inicia checkout de assinatura",
)
async def create_checkout(
    body: CheckoutRequest,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Cria uma cobrança AbacatePay e retorna a URL de pagamento.
    Requer autenticação JWT (Supabase).
    """
    # Buscar plano
    stmt = select(SubscriptionPlan).where(
        SubscriptionPlan.slug == body.plan_slug,
        SubscriptionPlan.is_active.is_(True),
    )
    result = await session.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plano '{body.plan_slug}' não encontrado.")

    user_id: str = user.get("sub", "")

    # Verificar se já tem assinatura ativa
    active = await _get_active_subscription(user_id, session)
    if active:
        raise HTTPException(
            status_code=409,
            detail="Você já possui uma assinatura ativa. Aguarde o vencimento para renovar.",
        )

    # Criar cliente na AbacatePay
    try:
        customer = await abacatepay_client.create_customer(
            name=body.name,
            email=body.email,
            cellphone=body.cellphone,
            tax_id=body.tax_id,
        )
        customer_id: str = customer["id"]
    except Exception as e:
        logger.error(f"Erro ao criar cliente AbacatePay: {e}")
        raise HTTPException(status_code=502, detail="Erro ao conectar com o gateway de pagamento.")

    # Gerar external_id único (user_id + plan + timestamp)
    ts = int(datetime.now(timezone.utc).timestamp())
    external_id = f"remunedata-{user_id[:8]}-{plan.slug}-{ts}"

    # Criar cobrança
    try:
        billing = await abacatepay_client.create_billing(
            customer_id=customer_id,
            plan_slug=plan.slug,
            plan_name=plan.name,
            plan_description=plan.description,
            price_cents=int(plan.price_brl * 100),
            external_id=external_id,
        )
    except Exception as e:
        logger.error(f"Erro ao criar cobrança AbacatePay: {e}")
        raise HTTPException(status_code=502, detail="Erro ao gerar cobrança de pagamento.")

    # Registrar assinatura pendente no banco
    subscription = UserSubscription(
        user_id=user_id,
        plan_id=plan.id,
        abacatepay_billing_id=billing["id"],
        abacatepay_customer_id=customer_id,
        status="pending",
    )
    session.add(subscription)
    await session.commit()

    return CheckoutResponse(
        billing_id=billing["id"],
        checkout_url=billing["url"],
        plan=plan.name,
        price_brl=plan.price_brl,
    )


@router.get("/me", response_model=SubscriptionOut, summary="Retorna assinatura ativa do usuário")
async def my_subscription(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Retorna o status e validade da assinatura ativa do usuário autenticado."""
    user_id: str = user.get("sub", "")
    sub = await _get_active_subscription(user_id, session)
    if not sub:
        return SubscriptionOut(status="inactive")

    # Carregar plano relacionado
    await session.refresh(sub, ["plan"])
    return SubscriptionOut(
        status="active",
        plan=sub.plan.name if sub.plan else None,
        expires_at=sub.expires_at,
    )


@router.post("/webhook", summary="Receptor de webhooks AbacatePay")
async def webhook(
    request: Request,
    webhook_secret: str = Query(..., alias="webhookSecret"),
    session: AsyncSession = Depends(get_session),
):
    """
    Recebe notificações da AbacatePay.
    Validações de segurança:
      1. webhookSecret na query string (obrigatório)
      2. Assinatura HMAC-SHA256 no header X-Abacatepay-Signature (quando disponível)
    """
    # 1. Validar secret da query string
    if not _verify_webhook_secret(webhook_secret):
        raise HTTPException(status_code=401, detail="Webhook secret inválido.")

    # 2. Ler e validar HMAC do body
    body_bytes = await request.body()
    hmac_header = request.headers.get("X-Abacatepay-Signature", "")
    if hmac_header and not _verify_hmac_signature(body_bytes, hmac_header):
        raise HTTPException(status_code=401, detail="Assinatura HMAC inválida.")

    # 3. Parsear payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido.")

    event: str = payload.get("event", "")
    data: dict = payload.get("data", {})
    dev_mode: bool = payload.get("devMode", False)

    logger.info(f"Webhook AbacatePay recebido: event={event} devMode={dev_mode}")

    if event == "billing.paid":
        billing_id: str = data.get("id", "")
        if not billing_id:
            return {"ok": True, "msg": "billing_id ausente, ignorado"}

        # Buscar assinatura pendente por billing_id (idempotência)
        stmt = select(UserSubscription).where(UserSubscription.abacatepay_billing_id == billing_id)
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()

        if sub is None:
            logger.warning(
                f"Webhook billing.paid para billing {billing_id} sem assinatura pendente."
            )
            return {"ok": True, "msg": "assinatura não encontrada"}

        if sub.status == "active":
            # Idempotência: já processado
            return {"ok": True, "msg": "já processado"}

        # Ativar assinatura
        plan_result = await session.get(SubscriptionPlan, sub.plan_id)
        now = datetime.now(timezone.utc)
        sub.status = "active"
        sub.starts_at = now
        sub.expires_at = now + timedelta(days=plan_result.duration_days if plan_result else 30)
        sub.updated_at = now

        await session.commit()
        logger.info(f"Assinatura {sub.id} ativada para user {sub.user_id} até {sub.expires_at}")

    elif event in ("billing.refunded", "billing.failed"):
        billing_id = data.get("id", "")
        stmt = select(UserSubscription).where(UserSubscription.abacatepay_billing_id == billing_id)
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()
        if sub and sub.status != "active":
            sub.status = "canceled"
            sub.updated_at = datetime.now(timezone.utc)
            await session.commit()
            logger.info(f"Assinatura {sub.id} cancelada por evento {event}")

    return {"ok": True}

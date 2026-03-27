"""
app/persistence/admin_repository.py
Repositório para consultas administrativas, métricas de faturamento e suporte.
"""

from datetime import datetime
from typing import List

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models import (
    BillingTransaction,
    SubscriptionPlan,
    SupportMessage,
    UserSubscription,
)


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_overall_stats(self) -> dict:
        """Retorna métricas globais de faturamento e usuários."""
        # 1. Faturamento Total
        stmt_total_revenue = select(func.sum(BillingTransaction.amount_brl))
        res_total = await self.session.execute(stmt_total_revenue)
        total_revenue = res_total.scalar() or 0.0

        # 2. Usuários com Planos Ativos
        stmt_active_subs = select(func.count(UserSubscription.id)).where(
            UserSubscription.status == "active"
        )
        res_active = await self.session.execute(stmt_active_subs)
        active_subscriptions = res_active.scalar() or 0

        # 3. Faturamento do Mês Atual
        now = datetime.now()
        first_day_of_month = datetime(now.year, now.month, 1)
        stmt_monthly_revenue = select(func.sum(BillingTransaction.amount_brl)).where(
            BillingTransaction.created_at >= first_day_of_month
        )
        res_monthly = await self.session.execute(stmt_monthly_revenue)
        monthly_revenue = res_monthly.scalar() or 0.0

        return {
            "total_revenue": float(total_revenue),
            "monthly_revenue": float(monthly_revenue),
            "active_subscriptions": active_subscriptions,
        }

    async def list_users_admin(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """Lista usuários e seus status de assinatura para o painel admin."""
        # Como não temos uma tabela 'User' centralizada (auth é no Supabase),
        # listamos a partir de UserSubscription e SupportMessage para identificar quem interagiu.
        # No futuro, se houver tabela Profile, usaremos ela.

        # Join com Plan para ver detalhes
        stmt = (
            select(UserSubscription, SubscriptionPlan)
            .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id)
            .order_by(UserSubscription.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)

        users = []
        for sub, plan in result:
            users.append(
                {
                    "user_id": sub.user_id,
                    "plan_name": plan.name,
                    "status": sub.status,
                    "expires_at": sub.expires_at,
                    "created_at": sub.created_at,
                }
            )
        return users

    async def get_support_chats(self, limit: int = 50) -> List[dict]:
        """Lista as últimas conversas de suporte agrupadas por usuário."""
        # Subquery para pegar a última mensagem de cada usuário
        subq = (
            select(SupportMessage.user_id, func.max(SupportMessage.created_at).label("last_msg_at"))
            .group_by(SupportMessage.user_id)
            .subquery()
        )

        stmt = (
            select(SupportMessage)
            .join(
                subq,
                (SupportMessage.user_id == subq.c.user_id)
                & (SupportMessage.created_at == subq.c.last_msg_at),
            )
            .order_by(desc(subq.c.last_msg_at))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return [
            {
                "user_id": m.user_id,
                "last_content": m.content,
                "last_at": m.created_at,
                "is_from_admin": m.is_from_admin,
                "is_read": m.is_read,
            }
            for m in result.scalars().all()
        ]

    async def get_chat_history(self, user_id: str) -> List[SupportMessage]:
        """Retorna o histórico completo de chat de um usuário."""
        stmt = (
            select(SupportMessage)
            .where(SupportMessage.user_id == user_id)
            .order_by(SupportMessage.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_message(
        self, user_id: str, content: str, is_from_admin: bool = False
    ) -> SupportMessage:
        """Adiciona uma nova mensagem ao chat."""
        msg = SupportMessage(
            user_id=user_id,
            content=content,
            is_from_admin=is_from_admin,
            is_read=is_from_admin,  # Se o admin mandou, ele já "leu"
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

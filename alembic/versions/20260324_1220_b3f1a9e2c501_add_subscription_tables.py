"""add_subscription_tables

Revision ID: b3f1a9e2c501
Revises: aa16e3afff99
Create Date: 2026-03-24 12:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3f1a9e2c501"
down_revision: Union[str, None] = "aa16e3afff99"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela de planos de assinatura
    op.create_table(
        "subscription_plan",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price_brl", sa.Float(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_subscription_plan_slug", "subscription_plan", ["slug"], unique=True)

    # Tabela de assinaturas dos usuários
    op.create_table(
        "user_subscription",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("abacatepay_billing_id", sa.String(255), nullable=True),
        sa.Column("abacatepay_customer_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plan.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("abacatepay_billing_id"),
    )
    op.create_index("ix_user_subscription_user_id", "user_subscription", ["user_id"])
    op.create_index(
        "ix_user_subscription_billing_id",
        "user_subscription",
        ["abacatepay_billing_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_user_subscription_billing_id", table_name="user_subscription")
    op.drop_index("ix_user_subscription_user_id", table_name="user_subscription")
    op.drop_table("user_subscription")
    op.drop_index("ix_subscription_plan_slug", table_name="subscription_plan")
    op.drop_table("subscription_plan")

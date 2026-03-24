"""
app/persistence/models.py
Definição dos modelos de banco de dados usando SQLAlchemy 2.0 ORM.
Baseado em /docs/13-modelo-minimo-de-persistencia.md.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe base para todos os modelos do projeto."""

    pass


class ExecutionAnnual(Base):
    """
    Representa a execução principal do coletor para um determinado ano.
    """

    __tablename__ = "execution_annual"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ano_exercicio: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    total_meses_processados: Mapped[int] = mapped_column(Integer, default=0)
    total_paginas_consumidas: Mapped[int] = mapped_column(Integer, default=0)
    total_registros_coletados: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    monthly_executions: Mapped[List["ExecutionMonthly"]] = relationship(
        back_populates="annual_execution", cascade="all, delete-orphan"
    )
    remunerations: Mapped[List["RemunerationCollected"]] = relationship(
        back_populates="annual_execution", cascade="all, delete-orphan"
    )


class ExecutionMonthly(Base):
    """
    Representa a execução de uma competência mensal dentro de uma execução anual.
    """

    __tablename__ = "execution_monthly"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    execution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("execution_annual.id"), nullable=False, index=True
    )
    mes_referencia: Mapped[str] = mapped_column(String(2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")

    paginas_consumidas: Mapped[int] = mapped_column(Integer, default=0)
    registros_coletados: Mapped[int] = mapped_column(Integer, default=0)
    total_pages_informado: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_elements_informado: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relacionamentos
    annual_execution: Mapped["ExecutionAnnual"] = relationship(back_populates="monthly_executions")
    remunerations: Mapped[List["RemunerationCollected"]] = relationship(
        back_populates="monthly_execution", cascade="all, delete-orphan"
    )


class RemunerationCollected(Base):
    """
    Representa cada registro retornado pela API para uma competência mensal.
    """

    __tablename__ = "remuneration_collected"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    execution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("execution_annual.id"), nullable=False, index=True
    )
    monthly_execution_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("execution_monthly.id"), nullable=False, index=True
    )

    # Identificação
    ano_exercicio: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    mes_referencia: Mapped[str] = mapped_column(String(2), nullable=False, index=True)

    # Dados do servidor
    codigo_identificacao: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    codigo_matricula: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    cpf_servidor: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nome_servidor: Mapped[str] = mapped_column(String(255), nullable=False)

    # Lotação
    codigo_orgao: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    nome_orgao: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    situacao_funcional: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    situacao_funcional_detalhada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cargo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    funcao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Valores financeiros
    valor_remuneracao_basica: Mapped[float] = mapped_column(Float, default=0.0)
    valor_beneficios: Mapped[float] = mapped_column(Float, default=0.0)
    valor_funcoes: Mapped[float] = mapped_column(Float, default=0.0)
    valor_comissao_conselheiro: Mapped[float] = mapped_column(Float, default=0.0)
    valor_hora_extra: Mapped[float] = mapped_column(Float, default=0.0)
    valor_verbas_eventuais: Mapped[float] = mapped_column(Float, default=0.0)
    valor_verbas_judiciais: Mapped[float] = mapped_column(Float, default=0.0)
    valor_receitas_meses_anteriores: Mapped[float] = mapped_column(Float, default=0.0)
    valor_reposicao_descontos_maior: Mapped[float] = mapped_column(Float, default=0.0)
    valor_licenca_premio: Mapped[float] = mapped_column(Float, default=0.0)
    valor_imposto_renda: Mapped[float] = mapped_column(Float, default=0.0)
    valor_seguridade_social: Mapped[float] = mapped_column(Float, default=0.0)
    valor_redutor_teto: Mapped[float] = mapped_column(Float, default=0.0)
    valor_descontos_meses_anteriores: Mapped[float] = mapped_column(Float, default=0.0)
    valor_reposicao_pagamento_maior: Mapped[float] = mapped_column(Float, default=0.0)
    valor_expurgo: Mapped[float] = mapped_column(Float, default=0.0)
    valor_liquido: Mapped[float] = mapped_column(Float, default=0.0)
    valor_bruto: Mapped[float] = mapped_column(Float, default=0.0)

    # Auditoria
    raw_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relacionamentos
    annual_execution: Mapped["ExecutionAnnual"] = relationship(back_populates="remunerations")
    monthly_execution: Mapped["ExecutionMonthly"] = relationship(back_populates="remunerations")


class SubscriptionPlan(Base):
    """
    Define os planos de assinatura disponíveis no RemuneData.
    Populado via seed no startup da aplicação.
    """

    __tablename__ = "subscription_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_brl: Mapped[float] = mapped_column(Float, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    subscriptions: Mapped[List["UserSubscription"]] = relationship(back_populates="plan")


class UserSubscription(Base):
    """
    Registra as assinaturas dos usuários autenticados via Supabase.
    O user_id corresponde ao campo 'sub' do JWT do Supabase.
    """

    __tablename__ = "user_subscription"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscription_plan.id"), nullable=False
    )

    # Dados do pagamento AbacatePay
    abacatepay_billing_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    abacatepay_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Controle de status e validade
    # Valores: pending | active | expired | canceled | refunded
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    plan: Mapped["SubscriptionPlan"] = relationship(back_populates="subscriptions")

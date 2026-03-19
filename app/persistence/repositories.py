"""
app/persistence/repositories.py
Implementação do padrão Repository para abstrair o SQLAlchemy.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.persistence.models import ExecutionAnnual, ExecutionMonthly, RemunerationCollected


class ExecutionRepository:
    """Repositório para gerenciar registros de execução (Anual e Mensal)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_annual(self, ano: int) -> ExecutionAnnual:
        """Busca uma execução anual para o ano informado ou cria uma nova."""
        stmt = select(ExecutionAnnual).where(ExecutionAnnual.ano_exercicio == ano).order_by(ExecutionAnnual.started_at.desc())
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        
        if not record:
            record = ExecutionAnnual(ano_exercicio=ano, status="running")
            self.session.add(record)
            await self.session.commit()
            await self.session.refresh(record)
            
        return record

    async def create_monthly(self, annual_id: int, mes: str) -> ExecutionMonthly:
        """Cria um registro de execução mensal vinculado a uma anual."""
        monthly = ExecutionMonthly(
            execution_id=annual_id,
            mes_referencia=mes,
            status="running"
        )
        self.session.add(monthly)
        await self.session.commit()
        await self.session.refresh(monthly)
        return monthly

    async def update_annual_progress(self, annual_id: int, pages: int, elements: int):
        """Atualiza os contadores globais da execução anual atomica e incrementalmente."""
        stmt = (
            update(ExecutionAnnual)
            .where(ExecutionAnnual.id == annual_id)
            .values(
                total_paginas_consumidas=ExecutionAnnual.total_paginas_consumidas + pages,
                total_registros_coletados=ExecutionAnnual.total_registros_coletados + elements,
                total_meses_processados=ExecutionAnnual.total_meses_processados + (1 if pages > 0 else 0)
            )
        )
        await self.session.execute(stmt)
        # Commit será feito pelo caller ou conforme estratégia de transação


class RemunerationRepository:
    """Repositório para gerenciar os dados de remuneração coletados."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_batch(self, items: list[RemunerationCollected]):
        """Salva uma lista de registros em lote."""
        if not items:
            return
            
        self.session.add_all(items)
        # Session commit is deferred to the service layer coordination
        # or done here if we want immediate persistence per page.
        # Following our current MonthlyCollector logic, we commit per page.
        await self.session.commit()

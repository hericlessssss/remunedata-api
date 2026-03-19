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


    async def list_annual(self, limit: int = 20, offset: int = 0) -> list[ExecutionAnnual]:
        """Lista as execuções anuais paginadas."""
        stmt = select(ExecutionAnnual).order_by(ExecutionAnnual.started_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_annual(self, annual_id: int) -> Optional[ExecutionAnnual]:
        """Busca detalhe de uma execução anual acompanhada dos meses."""
        # Força carregamento dos meses se necessário ou usa joinedload
        from sqlalchemy.orm import selectinload
        stmt = select(ExecutionAnnual).where(ExecutionAnnual.id == annual_id).options(selectinload(ExecutionAnnual.monthly_executions))
        result = await self.session.execute(stmt)
        return result.scalars().first()


class RemunerationRepository:
    """Repositório para gerenciar os dados de remuneração coletados."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self, 
        nome: Optional[str] = None, 
        cpf: Optional[str] = None, 
        ano: Optional[int] = None, 
        mes: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[RemunerationCollected], int]:
        """Busca paginada de registros com filtros."""
        from sqlalchemy import func
        stmt = select(RemunerationCollected)
        count_stmt = select(func.count()).select_from(RemunerationCollected)
        
        if nome:
            stmt = stmt.where(RemunerationCollected.nome_servidor.ilike(f"%{nome}%"))
            count_stmt = count_stmt.where(RemunerationCollected.nome_servidor.ilike(f"%{nome}%"))
        if cpf:
            stmt = stmt.where(RemunerationCollected.cpf_servidor == cpf)
            count_stmt = count_stmt.where(RemunerationCollected.cpf_servidor == cpf)
        if ano:
            stmt = stmt.where(RemunerationCollected.ano_exercicio == ano)
            count_stmt = count_stmt.where(RemunerationCollected.ano_exercicio == ano)
        if mes:
            stmt = stmt.where(RemunerationCollected.mes_referencia == mes)
            count_stmt = count_stmt.where(RemunerationCollected.mes_referencia == mes)
            
        # Count total
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        # Paginated results
        stmt = stmt.order_by(RemunerationCollected.nome_servidor).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def save_batch(self, items: list[RemunerationCollected]):
        """Salva uma lista de registros em lote."""
        if not items:
            return
            
        self.session.add_all(items)
        # Session commit is deferred to the service layer coordination
        # or done here if we want immediate persistence per page.
        # Following our current MonthlyCollector logic, we commit per page.
        await self.session.commit()

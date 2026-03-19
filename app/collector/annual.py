"""
app/collector/annual.py
Orquestrador de coleta anual.
Gerencia a iteração sobre os 12 meses e consolidação de resultados.
"""

from datetime import datetime, timezone
import collections

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.collector.monthly import MonthlyCollector
from app.persistence.models import ExecutionAnnual, ExecutionMonthly
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnnualCollector:
    """
    Orquestra a coleta de um ano completo (01 a 12).
    """

    def __init__(self, monthly_collector: MonthlyCollector, session: AsyncSession):
        self.monthly_collector = monthly_collector
        self.session = session

    async def run(self, ano: int) -> ExecutionAnnual:
        """
        Executa a coleta para todos os 12 meses do ano informado.
        """
        logger.info(f"Iniciando orquestração anual para o exercício {ano}")
        
        # 1. Iniciar registro anual no banco
        annual_exec = ExecutionAnnual(
            ano_exercicio=ano,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        self.session.add(annual_exec)
        await self.session.commit()
        await self.session.refresh(annual_exec)
        
        meses = [f"{m:02d}" for m in range(1, 13)]
        stats = collections.Counter()
        
        # 2. Iterar meses
        for mes in meses:
            try:
                logger.info(f"Orquestrando mês {mes}/{ano}")
                # Chama o coletor mensal (já lida com sua própria persistência e atualização da annual_exec)
                # Nota: collect() já faz commit interno de cada página/fim do mês.
                result = await self.monthly_collector.collect(
                    ano=ano, 
                    mes=mes, 
                    annual_execution_id=annual_exec.id
                )
                stats[result.status] += 1
                
            except Exception as e:
                logger.error(f"Falha crítica ao orquestrar mês {mes}/{ano}: {str(e)}")
                stats["error"] += 1
                # Continuamos para o próximo mês conforme estratégia de 'partial_success'
                continue

        # 3. Finalizar e consolidar status
        finished_at = datetime.now(timezone.utc)
        annual_exec.finished_at = finished_at
        
        duration = finished_at - annual_exec.started_at
        annual_exec.duration_ms = int(duration.total_seconds() * 1000)
        
        # Lógica de status final (Doc 12)
        if stats["success"] == 12:
            annual_exec.status = "success"
        elif stats["success"] > 0:
            annual_exec.status = "partial_success"
        else:
            annual_exec.status = "error"
            
        await self.session.commit()
        await self.session.refresh(annual_exec)
        
        logger.info(
            f"Orquestração anual {ano} finalizada. "
            f"Status: {annual_exec.status}, "
            f"Meses OK: {stats['success']}, "
            f"Meses Erro: {stats['error']}"
        )
        
        return annual_exec

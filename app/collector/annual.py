"""
app/collector/annual.py
Orquestrador de coleta anual via Repositórios.
"""

from datetime import datetime, timezone
import collections
from app.collector.monthly import MonthlyCollector
from app.persistence.models import ExecutionAnnual
from app.persistence.repositories import ExecutionRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnnualCollector:
    """
    Orquestra a coleta de um ano completo (01 a 12) usando repositórios.
    """

    def __init__(self, monthly_collector: MonthlyCollector, execution_repo: ExecutionRepository):
        self.monthly_collector = monthly_collector
        self.execution_repo = execution_repo

    async def run(self, ano: int) -> ExecutionAnnual:
        """
        Executa a coleta para todos os 12 meses do ano informado.
        """
        logger.info(f"Iniciando orquestração anual para o exercício {ano}")
        
        # 1. Iniciar registro anual via Repo
        annual_exec = await self.execution_repo.get_or_create_annual(ano)
        annual_exec.status = "running"
        annual_exec.started_at = datetime.now(timezone.utc)
        await self.execution_repo.session.commit()
        
        meses = [f"{m:02d}" for m in range(1, 13)]
        stats = collections.Counter()
        
        # 2. Iterar meses
        for mes in meses:
            try:
                logger.info(f"Orquestrando mês {mes}/{ano}")
                result = await self.monthly_collector.collect(
                    ano=ano, 
                    mes=mes, 
                    annual_execution_id=annual_exec.id
                )
                stats[result.status] += 1
                
            except Exception as e:
                logger.error(f"Falha crítica ao orquestrar mês {mes}/{ano}: {str(e)}")
                stats["error"] += 1
                continue

        # 3. Finalizar e consolidar status
        finished_at = datetime.now(timezone.utc)
        annual_exec.finished_at = finished_at
        
        duration = finished_at - annual_exec.started_at
        annual_exec.duration_ms = int(duration.total_seconds() * 1000)
        
        if stats["success"] == 12:
            annual_exec.status = "success"
        elif stats["success"] > 0:
            annual_exec.status = "partial_success"
        else:
            annual_exec.status = "error"
            
        await self.execution_repo.session.commit()
        await self.execution_repo.session.refresh(annual_exec)
        
        logger.info(
            f"Orquestração anual {ano} finalizada. Status: {annual_exec.status}"
        )
        
        return annual_exec

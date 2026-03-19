"""
app/workers/tasks.py
Definição de tarefas assíncronas do Celery.
"""

import asyncio

from celery.utils.log import get_task_logger

from app.collector.annual import AnnualCollector
from app.collector.monthly import MonthlyCollector
from app.core.celery_app import celery_app
from app.infra.transparencia_client import TransparenciaClient
from app.persistence.repositories import ExecutionRepository, RemunerationRepository
from app.persistence.session import async_session_maker

logger = get_task_logger(__name__)


@celery_app.task(name="collect_annual_task", bind=True)
def collect_annual_task(self, ano: int):
    """
    Tarefa Celery para executar a coleta anual completa.
    Wrapper síncrono para a execução assíncrona dos coletores.
    """
    logger.info(f"Iniciando tarefa de coleta anual: {ano} (Task ID: {self.request.id})")

    async def _run():
        async with async_session_maker() as session:
            # Setup dependências
            client = TransparenciaClient()
            exec_repo = ExecutionRepository(session)
            rem_repo = RemunerationRepository(session)

            monthly_collector = MonthlyCollector(client, exec_repo, rem_repo)
            annual_collector = AnnualCollector(monthly_collector, exec_repo)

            # Executar
            result = await annual_collector.run(ano)

            # Extrair dados básicos antes de fechar a sessão/loop para evitar DetachedInstanceError
            return {"status": result.status, "execution_id": result.id}

    try:
        # Celery roda em processos síncronos, precisamos do loop para o código async
        task_result = asyncio.run(_run())
        logger.info(f"Tarefa de coleta anual {ano} concluída com status: {task_result['status']}")
        return task_result
    except Exception as e:
        logger.error(f"Erro fatal na tarefa de coleta {ano}: {str(e)}")
        raise e


@celery_app.task(name="sync_recent_years_task")
def sync_recent_years_task():
    """
    Tarefa periódica para sincronizar o ano atual e o anterior.
    """
    from datetime import datetime

    current_year = datetime.now().year
    previous_year = current_year - 1

    logger.info(f"Iniciando sincronização periódica: {previous_year} e {current_year}")

    # Dispara as tarefas de coleta anual para ambos os anos
    collect_annual_task.delay(previous_year)
    collect_annual_task.delay(current_year)

    return {"status": "queued", "years": [previous_year, current_year]}

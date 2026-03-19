"""
app/api/endpoints/executions.py
Endpoints para consulta de status de execução.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_execution_repository
from app.api.schemas import ExecutionAnnualRead, ExecutionAnnualDetail
from app.persistence.repositories import ExecutionRepository
from app.workers.tasks import collect_annual_task

router = APIRouter()


@router.post("/", response_model=ExecutionAnnualRead, status_code=201)
async def trigger_collection(
    ano: int = Query(..., ge=2000, le=2100),
    repo: ExecutionRepository = Depends(get_execution_repository)
):
    """Dispara uma nova coleta anual em background."""
    # 1. Criar registro inicial no banco
    record = await repo.get_or_create_annual(ano)
    
    if record.status == "running":
        # Se já estiver rodando, apenas retorna o registro ( idempotência básica )
        return record
    
    # 2. Resetar status se for um re-run de erro/concluído
    record.status = "running"
    await repo.session.commit()
    
    # 3. Enfileirar no Celery
    collect_annual_task.delay(ano)
    
    return record


@router.get("/", response_model=List[ExecutionAnnualRead])
async def list_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: ExecutionRepository = Depends(get_execution_repository)
):
    """Lista as últimas execuções anuais do sistema."""
    return await repo.list_annual(limit=limit, offset=skip)


@router.get("/{execution_id}", response_model=ExecutionAnnualDetail)
async def get_execution(
    execution_id: int,
    repo: ExecutionRepository = Depends(get_execution_repository)
):
    """Retorna detalhes de uma execução anual específica, incluindo meses."""
    record = await repo.get_annual(execution_id)
    if not record:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    return record

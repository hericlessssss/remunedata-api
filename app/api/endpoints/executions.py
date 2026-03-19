"""
app/api/endpoints/executions.py
Endpoints para consulta de status de execução.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_execution_repository
from app.api.schemas import ExecutionAnnualRead, ExecutionAnnualDetail
from app.persistence.repositories import ExecutionRepository

router = APIRouter()


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

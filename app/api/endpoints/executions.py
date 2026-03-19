"""
app/api/endpoints/executions.py
Endpoints para consulta de status de execução.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_execution_repository, get_remuneration_repository
from app.api.schemas import ExecutionAnnualRead, ExecutionAnnualDetail
from app.persistence.repositories import ExecutionRepository, RemunerationRepository
from app.workers.tasks import collect_annual_task
from fastapi.responses import StreamingResponse
import io
import pandas as pd

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


@router.get("/{id}/export")
async def export_execution(
    id: int,
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    repo: ExecutionRepository = Depends(get_execution_repository),
    remu_repo: RemunerationRepository = Depends(get_remuneration_repository)
):
    """
    Exporta os dados da execução anual em formato CSV ou XLSX.
    """
    # 1. Verificar se a execução existe
    execution = await repo.get_annual(id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    
    # 2. Buscar todos os registros relacionados
    records = await remu_repo.get_all_by_execution(id)
    if not records:
        raise HTTPException(status_code=404, detail="Nenhum registro de remuneração encontrado para esta execução")

    # 3. Converter para DataFrame
    # Filtramos apenas as colunas de negócio (omitindo IDs internos e payloads)
    data = []
    for r in records:
        data.append({
            "Ano": r.ano_exercicio,
            "Mês": r.mes_referencia,
            "ID Identificação": r.codigo_identificacao,
            "Matrícula": r.codigo_matricula,
            "Nome": r.nome_servidor,
            "CPF": r.cpf_servidor or "",
            "Órgão": r.nome_orgao or "",
            "Cargo": r.cargo or "",
            "Função": r.funcao or "",
            "Situação": r.situacao_funcional or "",
            "Remuneração Básica": r.valor_remuneracao_basica,
            "Benefícios": r.valor_beneficios,
            "Gratificações/Funções": r.valor_funcoes,
            "Hora Extra": r.valor_hora_extra,
            "Verbas Eventuais": r.valor_verbas_eventuais,
            "Imposto de Renda": r.valor_imposto_renda,
            "Seguridade Social": r.valor_seguridade_social,
            "Redutor Teto": r.valor_redutor_teto,
            "Valor Líquido": r.valor_liquido,
            "Valor Bruto": r.valor_bruto,
        })
    
    df = pd.DataFrame(data)
    
    # 4. Preparar Stream de resposta
    filename = f"remuneracao_{execution.ano_exercicio}_exec_{id}"
    
    if format == "csv":
        # CSV com BOM para Excel identificar UTF-8 automaticamente
        stream = io.StringIO()
        df.to_csv(stream, index=False, encoding="utf-8-sig")
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    else:
        stream = io.BytesIO()
        with pd.ExcelWriter(stream, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Remuneração")
        stream.seek(0)
        response = StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
        
    return response

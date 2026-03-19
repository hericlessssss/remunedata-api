"""
app/api/endpoints/remuneration.py
Endpoints para consulta de dados de remuneração coletados.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_remuneration_repository
from app.api.schemas import PaginatedRemuneration
from app.persistence.repositories import RemunerationRepository

router = APIRouter()


@router.get("/", response_model=PaginatedRemuneration)
async def search_remuneration(
    nome: Optional[str] = Query(None, description="Parte do nome do servidor"),
    cpf: Optional[str] = Query(None, description="CPF do servidor (exato)"),
    cargo: Optional[str] = Query(None, description="Parte do cargo do servidor"),
    orgao: Optional[str] = Query(None, description="Parte do nome do órgão"),
    ano: Optional[int] = Query(None),
    mes: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
    repo: RemunerationRepository = Depends(get_remuneration_repository)
):
    """Busca registros de remuneração com filtros e paginação."""
    offset = (page - 1) * size
    items, total = await repo.search(
        nome=nome,
        cpf=cpf,
        cargo=cargo,
        orgao=orgao,
        ano=ano,
        mes=mes,
        limit=size,
        offset=offset
    )
    
    pages = (total + size - 1) // size
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


from datetime import datetime, timedelta

class SummaryCache:
    data: Optional[dict] = None
    expires_at: datetime = datetime.min
    ano: Optional[int] = None

summary_cache = SummaryCache()

@router.get("/summary")
async def get_summary(
    ano: Optional[int] = Query(None),
    repo: RemunerationRepository = Depends(get_remuneration_repository)
):
    """Retorna dados agregados para o dashboard com cache de 60 segundos."""
    now = datetime.now()
    
    # Se tiver cache válido no mesmo ano, retorna
    if summary_cache.data and summary_cache.expires_at > now:
        if summary_cache.ano == ano:
            return summary_cache.data
            
    # Caso contrário, busca do banco
    data = await repo.get_summary(ano=ano)
    
    # Atualiza cache
    summary_cache.data = data
    summary_cache.ano = ano
    summary_cache.expires_at = now + timedelta(seconds=60)
    
    return data

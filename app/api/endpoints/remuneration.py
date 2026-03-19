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


@router.get("/summary")
async def get_summary(
    ano: Optional[int] = Query(None),
    repo: RemunerationRepository = Depends(get_remuneration_repository)
):
    """Retorna dados agregados para o dashboard."""
    return await repo.get_summary(ano=ano)

"""
app/api/endpoints/admin.py
Rotas administrativas para gestão de usuários, faturamento e suporte.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_admin_repository, get_admin_user
from app.core.config import settings
from app.persistence.admin_repository import AdminRepository

router = APIRouter()


@router.get("/stats")
async def get_admin_stats(
    admin: dict = Depends(get_admin_user), repo: AdminRepository = Depends(get_admin_repository)
):
    """Retorna métricas globais de faturamento e usuários."""
    return await repo.get_overall_stats()


@router.get("/users")
async def list_users(
    admin: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository),
    limit: int = 50,
    offset: int = 0,
):
    """Lista usuários e seus status de assinatura."""
    return await repo.list_users_admin(limit=limit, offset=offset)


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    email: str,  # Precisamos do e-mail para o Supabase
    admin: dict = Depends(get_admin_user),
):
    """Dispara e-mail de recuperação de senha via Admin API do Supabase."""
    async with httpx.AsyncClient() as client:
        # Nota: O Supabase exige a Service Role Key para operações administrativas
        response = await client.post(
            f"{settings.supabase_url}/auth/v1/recover",
            json={"email": email},
            headers={
                "apikey": settings.supabase_service_role_key,
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Erro ao disparar recuperação no Supabase: {response.text}",
            )

    return {"ok": True, "message": f"E-mail de recuperação enviado para {email}"}


@router.get("/support")
async def list_support_chats(
    admin: dict = Depends(get_admin_user), repo: AdminRepository = Depends(get_admin_repository)
):
    """Lista conversas de suporte agrupadas por usuário."""
    return await repo.get_support_chats()


@router.get("/support/{user_id}")
async def get_chat_history(
    user_id: str,
    admin: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository),
):
    """Retorna o histórico completo de chat de um usuário."""
    return await repo.get_chat_history(user_id)


@router.post("/support/{user_id}/reply")
async def reply_to_user(
    user_id: str,
    content: str,  # Pode ser trocado por um schema Pydantic se crescer
    admin: dict = Depends(get_admin_user),
    repo: AdminRepository = Depends(get_admin_repository),
):
    """Envia uma resposta administrativa para o usuário."""
    if not content:
        raise HTTPException(status_code=400, detail="Conteúdo não pode ser vazio")

    msg = await repo.add_message(user_id=user_id, content=content, is_from_admin=True)
    return msg

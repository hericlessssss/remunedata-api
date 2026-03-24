"""
app/core/auth.py
Lógica de validação de tokens JWT emitidos pelo Supabase.
"""

from typing import Dict, Any
import jwt
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ALGORITHM = "HS256"

def verify_token(token: str) -> Dict[str, Any]:
    """
    Decodifica e valida o JWT do Supabase usando o Segredo JWT (HS256).
    
    Supabase usa tokens assinados com o Segredo configurado no dashboard.
    O 'aud' do token costuma ser 'authenticated'.
    """
    try:
        # Nota: O Supabase emite tokens com audiência 'authenticated' por padrão
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[ALGORITHM],
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado recebido.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        logger.warning(f"Token com audiência inválida. Detalhes: {str(jwt.InvalidAudienceError)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Audiência do token inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        logger.error(f"Erro ao validar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

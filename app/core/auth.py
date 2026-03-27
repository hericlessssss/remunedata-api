from typing import Any, Dict

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient, PyJWKClientError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Algoritmos aceitos (Supabase migrou para ES256/ECC, mas aceitamos HS256 para legacy)
ALGORITHM = "HS256"
ACCEPTED_ALGORITHMS = ["HS256", "ES256"]

# Singleton opcional para cache de chaves JWKS do Supabase (para ES256)
_jwks_client = None
if settings.supabase_jwks_url:
    _jwks_client = PyJWKClient(settings.supabase_jwks_url)


def verify_token(token: str) -> Dict[str, Any]:
    """
    Decodifica e valida o JWT do Supabase.
    Suporta HS256 (Segredo) e ES256 (Chaves ECC do Discovery URL).
    """
    try:
        # 1. Identificar o algoritmo no header
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg")

        if alg not in ACCEPTED_ALGORITHMS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Algoritmo '{alg}' não permitido. Use {ACCEPTED_ALGORITHMS}.",
            )

        # 2. Validar conforme o algoritmo
        if alg == "ES256" and _jwks_client:
            # Busca a chave pública no Supabase (Discovery URL)
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key.key, algorithms=["ES256"], audience="authenticated"
            )
        else:
            # Fallback para o segredo HS256 (Shared Secret)
            payload = jwt.decode(
                token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated"
            )
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado recebido.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError as e:
        logger.warning(f"Token com audiência inválida: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Audiência do token inválida: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, PyJWKClientError) as e:
        logger.error(f"Erro ao validar token ({alg if 'alg' in locals() else 'unknown'}): {str(e)}")
        # Debug detalhado no log para o usuário
        if "alg" in locals() and alg == "ES256" and not settings.supabase_jwks_url:
            logger.warning("Recebido token ES256 mas SUPABASE_JWKS_URL não está configurada.")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou configuração divergente: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

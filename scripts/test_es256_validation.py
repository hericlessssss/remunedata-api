"""
scripts/test_es256_validation.py
Valida se a API consegue alcançar o JWKS do Supabase e carregar as chaves ES256.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from jwt import PyJWKClient
from app.core.config import settings

def test_jwks_connection():
    url = settings.supabase_jwks_url
    if not url:
        print("â Œ ERRO: SUPABASE_JWKS_URL nÃ£o configurada no .env")
        return

    print(f"ðŸ”🔍 Testando conexÃ£o com JWKS: {url}")
    try:
        client = PyJWKClient(url)
        signing_keys = client.get_signing_keys()
        
        print(f"âœ… SUCESSO! Encontradas {len(signing_keys)} chaves de assinatura.")
        for key in signing_keys:
            # Em PyJWT, PyJWK tem o atributo 'kid' diretamente
            try:
                kid = getattr(key, 'kid', 'N/A')
                alg = getattr(key, 'algorithm', 'N/A')
                print(f"   - Key ID: {kid}")
                print(f"   - Alg: {alg}")
            except Exception:
                print(f"   - Chave encontrada, mas sem atributos legÃ­veis.")
            
    except Exception as e:
        print(f"â Œ FALHA ao buscar chaves: {str(e)}")

if __name__ == "__main__":
    test_jwks_connection()

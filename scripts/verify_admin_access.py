"""
scripts/verify_admin_access.py
Verifica se usuários na ADMIN_EMAILS conseguem burlar a checagem de assinatura.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from unittest.mock import MagicMock

from app.api.deps import require_active_subscription
from app.core.config import settings


async def test_admin_bypass():
    print("ðŸ”🔍 Testando bypass de assinatura para ADMIN...")

    # 1. Configura um admin real
    admin_email = settings.admin_emails[0]
    mock_user = {"email": admin_email, "sub": "admin-id-123"}
    mock_session = MagicMock()  # NÃ£o deve nem ser usada se for admin

    try:
        # Chama a dependÃªncia
        result = await require_active_subscription(user=mock_user, session=mock_session)
        if result == mock_user:
            print(f"âœ… SUCESSO: Admin {admin_email} liberado sem consulta ao banco.")
        else:
            print("â Œ FALHA: Resultado inesperado da dependÃªncia.")
    except Exception as e:
        print(f"â Œ FALHA: Admin foi bloqueado ou erro ocorreu: {e}")

    # 2. Testa usuÃ¡rio comum (deve falhar por falta de sessÃ£o real/mock)
    print("\nðŸ”🔍 Testando bloqueio para usuário comum...")
    mock_regular = {"email": "user@comum.com", "sub": "user-id-456"}
    try:
        await require_active_subscription(user=mock_regular, session=mock_session)
        print("â Œ FALHA: UsuÃ¡rio comum passou sem assinatura!")
    except Exception as e:
        print(
            f"âœ… SUCESSO: UsuÃ¡rio comum bloqueado corretamente (Erro esperado: {type(e).__name__})"
        )


if __name__ == "__main__":
    asyncio.run(test_admin_bypass())

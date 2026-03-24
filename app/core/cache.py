"""
app/core/cache.py
Implementação de camada de cache usando Redis assíncrono.
"""

import json
import logging
from typing import Any, Optional

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Implementa operações básicas de cache (get/set) sobre o Redis."""

    def __init__(self, redis_url: str):
        self._redis = Redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """Tenta buscar um valor no cache. Retorna None se não encontrar ou falhar."""
        try:
            data = await self._redis.get(key)
            if data:
                try:
                    return json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    return data
            return None
        except Exception as e:
            logger.warning(f"Erro ao ler cache (key={key}): {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Armazena valor no cache com expiração (TTL em segundos)."""
        try:
            # Se não for tipo primitivo, serializa para JSON
            if not isinstance(value, (str, int, float, bool)) and value is not None:
                serialized = json.dumps(value)
            else:
                serialized = value

            await self._redis.set(key, serialized, ex=ttl)
        except Exception as e:
            logger.warning(f"Erro ao gravar cache (key={key}): {e}")

    async def delete(self, key: str):
        """Remove uma chave específica."""
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.warning(f"Erro ao deletar cache (key={key}): {e}")

    async def clear_prefix(self, prefix: str):
        """Remove todas as chaves que iniciam com o prefixo informado."""
        try:
            keys = await self._redis.keys(f"{prefix}*")
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Erro ao limpar prefixo cache (prefix={prefix}): {e}")


# Instância global compartilhada
cache = RedisCache(settings.redis_url)


def get_cache() -> RedisCache:
    """Retorna a instância do cache para uso em dependências FastAPI."""
    return cache

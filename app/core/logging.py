"""
app/core/logging.py
Configuração de logging estruturado para a aplicação.
Usa a stdlib logging com formatação clara para desenvolvimento
e JSON simplificado pronto para ingestão em ferramentas de observabilidade.
"""

import logging
import sys
from typing import Any


def configure_logging(level: str = "INFO") -> None:
    """
    Configura o sistema de logging da aplicação.

    Args:
        level: Nível de log. Ex: "DEBUG", "INFO", "WARNING", "ERROR".
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Formato legível para desenvolvimento
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%dT%H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=date_fmt))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Evitar handlers duplicados em ambientes de reload (uvicorn --reload)
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers.clear()
        root_logger.addHandler(handler)

    # Silenciar loggers de libs que poluem o output em nível DEBUG
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger nomeado para o módulo solicitado.

    Uso:
        logger = get_logger(__name__)
        logger.info("Iniciando coleta", extra={"ano": 2025})

    Args:
        name: Nome do módulo. Use __name__ para rastrear a origem.
    """
    return logging.getLogger(name)


def log_extra(**kwargs: Any) -> dict[str, Any]:
    """
    Helper para criar contexto extra de log de forma legível.

    Uso:
        logger.info("Página coletada", extra=log_extra(page=1, records=150))

    Returns:
        Dicionário com chave 'extra_context' contendo os kwargs.
    """
    return {"extra_context": kwargs}

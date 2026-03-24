"""
alembic/env.py
Configuração do ambiente Alembic para migrations.

Lê DATABASE_URL_SYNC do ambiente para suporte a conexão síncrona,
que é o que o Alembic requer (não suporta asyncpg diretamente).
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Objeto de configuração Alembic (acesso ao alembic.ini)
config = context.config

# Configurar logging a partir do alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Sobrescrever a URL de conexão com a variável de ambiente (prioritária)
# Usa DATABASE_URL_SYNC pois Alembic requer driver síncrono
database_url_sync = os.getenv("DATABASE_URL_SYNC")
if database_url_sync:
    config.set_main_option("sqlalchemy.url", database_url_sync)

# target_metadata: apontar para o MetaData dos models para autogenerate.
sys.path.append(str(Path(__file__).parent.parent))

from app.persistence.models import Base  # noqa: E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Rodar migrations em modo offline (sem conexão ativa com o banco).
    Gera o SQL sem executar, útil para revisão ou ambientes sem acesso direto.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Rodar migrations em modo online (com conexão ativa com o banco).
    Modo padrão para execução em `alembic upgrade head`.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

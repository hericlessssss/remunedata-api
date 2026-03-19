"""
tests/conftest.py
Fixtures compartilhadas pelos testes da aplicação.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """
    Garante variáveis de ambiente mínimas para testes.
    Aplicada automaticamente a todos os testes (autouse=True).

    Isso evita erros de ValidationError do Settings em testes
    que não importam config diretamente.
    """
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/df_remuneration_test",
    )
    monkeypatch.setenv(
        "DATABASE_URL_SYNC",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/df_remuneration_test",
    )
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

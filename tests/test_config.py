"""
tests/test_config.py
Testes do módulo de configuração (app/core/config.py).

TDD:
- Happy path: Settings carrega variáveis corretamente
- Edge case: valores padrão são aplicados para campos opcionais
- Erro: Settings sem DATABASE_URL deve falhar com ValidationError

Nota de implementação:
    Pydantic BaseSettings carrega variáveis de DOIS lugares:
    1. Variáveis de ambiente (processo)
    2. Arquivo .env (em disco)

    Quando testamos valores padrão ou ausência de variáveis obrigatórias,
    usamos Settings(_env_file=None) para evitar que o .env em disco
    interfira no resultado do teste.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettingsHappyPath:
    """Happy path: Settings carrega corretamente com todas as vars presentes."""

    def test_settings_loads_database_url(self, monkeypatch):
        """DATABASE_URL deve ser carregada do ambiente."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
        monkeypatch.setenv(
            "DATABASE_URL_SYNC", "postgresql+psycopg2://user:pass@localhost:5432/test"
        )
        settings = Settings(_env_file=None)
        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/test"

    def test_settings_loads_database_url_sync(self, monkeypatch):
        """DATABASE_URL_SYNC deve ser carregada do ambiente."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
        monkeypatch.setenv(
            "DATABASE_URL_SYNC", "postgresql+psycopg2://user:pass@localhost:5432/test"
        )
        settings = Settings(_env_file=None)
        assert (
            settings.database_url_sync == "postgresql+psycopg2://user:pass@localhost:5432/test"
        )


class TestSettingsDefaults:
    """Edge case: valores padrão são aplicados para campos opcionais."""

    def test_default_redis_url(self, monkeypatch):
        """REDIS_URL deve ter valor padrão quando não definido no ambiente."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
        monkeypatch.setenv(
            "DATABASE_URL_SYNC", "postgresql+psycopg2://user:pass@localhost:5432/test"
        )
        monkeypatch.delenv("REDIS_URL", raising=False)
        # _env_file=None: evitar que o .env em disco forneça REDIS_URL
        settings = Settings(_env_file=None)
        assert settings.redis_url == "redis://localhost:6379/0"

    def test_default_page_size(self, monkeypatch):
        """TRANSPARENCIA_PAGE_SIZE deve ter valor padrão de 150."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
        monkeypatch.setenv(
            "DATABASE_URL_SYNC", "postgresql+psycopg2://user:pass@localhost:5432/test"
        )
        settings = Settings(_env_file=None)
        assert settings.transparencia_page_size == 150

    def test_default_api_base_url(self, monkeypatch):
        """TRANSPARENCIA_API_BASE_URL deve apontar para o Portal da Transparência."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
        monkeypatch.setenv(
            "DATABASE_URL_SYNC", "postgresql+psycopg2://user:pass@localhost:5432/test"
        )
        settings = Settings(_env_file=None)
        assert "transparencia.df.gov.br" in settings.transparencia_api_base_url

    def test_default_log_level(self, monkeypatch):
        """LOG_LEVEL deve ter valor padrão de INFO."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
        monkeypatch.setenv(
            "DATABASE_URL_SYNC", "postgresql+psycopg2://user:pass@localhost:5432/test"
        )
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        settings = Settings(_env_file=None)
        assert settings.log_level == "INFO"


class TestSettingsValidationError:
    """Erro: Settings sem variáveis obrigatórias deve lançar ValidationError."""

    def test_missing_database_url_raises(self, monkeypatch):
        """Sem DATABASE_URL, Settings deve lançar ValidationError."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
        # _env_file=None: garantir que o .env em disco não forneça as variáveis
        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_missing_database_url_sync_raises(self, monkeypatch):
        """Sem DATABASE_URL_SYNC, Settings deve lançar ValidationError."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test")
        monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
        with pytest.raises(ValidationError):
            Settings(_env_file=None)

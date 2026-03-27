"""
app/core/config.py
Configuração central da aplicação via Pydantic BaseSettings.
Lê variáveis de ambiente (ou arquivo .env) e valida os valores.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação lidas de variáveis de ambiente.

    As variáveis devem ser definidas no arquivo .env (não commitado) ou
    diretamente no ambiente. O arquivo .env.example serve como referência.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Ignora variáveis extras no .env (não causa erro)
        extra="ignore",
    )

    # Banco de dados
    database_url: str = Field(
        description="URL de conexão assíncrona (asyncpg) para SQLAlchemy 2.x",
    )
    database_url_sync: str = Field(
        description="URL de conexão síncrona (psycopg2) para Alembic migrations",
    )

    # Supabase Auth
    supabase_url: str = Field(
        description="URL do projeto Supabase",
    )
    supabase_jwt_secret: str = Field(
        description="Segredo JWT para validação de tokens (HS256)",
    )

    # Sentry
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="DSN do projeto Sentry para rastreamento de erros",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="URL de conexão com Redis",
    )

    # Aplicação
    app_env: str = Field(
        default="development",
        description="Ambiente da aplicação: development, staging, production",
    )
    log_level: str = Field(
        default="INFO",
        description="Nível de logging: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )

    # API do Portal da Transparência
    transparencia_api_base_url: str = Field(
        default="https://www.transparencia.df.gov.br/api",
        description="URL base da API do Portal da Transparência do DF",
    )
    transparencia_page_size: int = Field(
        default=150,
        description="Tamanho máximo de página validado na API (não alterar sem nova validação)",
        ge=1,
        le=150,
    )
    transparencia_timeout_seconds: int = Field(
        default=30,
        description="Timeout em segundos para requisições HTTP à API",
        ge=5,
        le=120,
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["*"],
        description="Lista de origens permitidas para CORS (ex: ['https://remunedata.com.br'])",
    )

    # AbacatePay
    abacatepay_api_key: str = Field(
        default="",
        description="Bearer token da conta AbacatePay",
    )
    abacatepay_webhook_secret: str = Field(
        default="",
        description="Secret para validação dos webhooks da AbacatePay",
    )
    abacatepay_base_url: str = Field(
        default="https://api.abacatepay.com/v1",
        description="URL base da API AbacatePay",
    )
    front_url: str = Field(
        default="https://remunedata.com.br",
        description="URL base do frontend (usada nos redirects de pagamento)",
    )

    # Configurações Admin
    supabase_service_role_key: str = Field(
        default="",
        description="Chave secreta para operações administrativas no Supabase",
    )
    admin_path_prefix: str = Field(
        default="admin-secret-dashboard",
        description="Prefixo da URL para o painel administrativo",
    )
    admin_emails: list[str] = Field(
        default=["admin@remunedata.com.br"],
        description="Lista de e-mails com permissão de administrador",
    )

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


def get_settings() -> Settings:
    """
    Retorna instância das configurações.
    """
    return Settings()


# Instância global para uso no app
settings = get_settings()

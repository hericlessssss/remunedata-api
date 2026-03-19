from app.core.config import Settings


def test_cors_origins_parsing():
    # Teste padrão (aberto)
    settings = Settings(database_url="sqlite+aiosqlite://", database_url_sync="sqlite://")
    assert settings.cors_origins == ["*"]

    # Teste com lista real (simulando env var)
    # Pydantic Settings trata strings de listas JSON automaticamente
    origins = ["https://remunedata.com.br", "http://localhost:3000"]
    settings = Settings(
        database_url="sqlite+aiosqlite://", database_url_sync="sqlite://", cors_origins=origins
    )
    assert settings.cors_origins == origins

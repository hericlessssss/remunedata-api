# 15 - Stack mínimo e bootstrap

## Objetivo
Definir o stack mínimo da V1 e os arquivos base para iniciar a implementação do projeto.

## Stack escolhido para a V1
- Python 3.12
- FastAPI
- PostgreSQL
- Redis
- Celery
- SQLAlchemy 2.x
- Alembic
- Pydantic
- Docker
- Docker Compose
- pytest
- tox
- coverage.py

## Justificativa das escolhas
- FastAPI: melhor aderência a API REST com tipagem forte.
- PostgreSQL: banco relacional exigido pelo projeto.
- Redis: exigido para filas e controle de concorrência.
- Celery: opção madura para execução assíncrona com workers.
- SQLAlchemy 2.x: ORM compatível com a arquitetura proposta.
- Alembic: controle de migrations do banco.
- Pydantic: validação e tipagem de entrada e saída.
- Docker e Docker Compose: exigidos para execução padronizada do ambiente.
- pytest, tox e coverage.py: base mínima para qualidade e cobertura de testes.

## Arquivos iniciais do bootstrap
- `pyproject.toml`
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `app/main.py`
- `app/core/config.py`
- `app/core/logging.py`
- `app/infra/transparencia_client.py`
- `app/collector/run_collection.py`
- `app/collector/month_collection.py`
- `app/persistence/models.py`
- `app/persistence/session.py`
- `app/persistence/repositories.py`
- `alembic.ini`
- `alembic/`
- `tests/`

## Ordem sugerida de criação
1. criar `pyproject.toml`
2. criar `Dockerfile`
3. criar `docker-compose.yml`
4. criar `.env.example`
5. criar estrutura inicial de pastas em `app/`
6. criar `session.py` e `models.py`
7. configurar Alembic
8. implementar o cliente da API externa
9. implementar a regra mínima da coleta
10. criar os primeiros testes

## Observações
- a V1 deve priorizar clareza e execução local simples
- a estrutura inicial deve nascer pronta para crescer com API, worker e scheduler
- o bootstrap deve respeitar separação por camadas desde o início

## Conclusão
Com esse stack mínimo e essa ordem de bootstrap, o projeto já pode iniciar a implementação de forma alinhada aos requisitos técnicos e arquiteturais do documento.
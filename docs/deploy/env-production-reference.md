# Production Environment Reference

Esta documentação descreve todas as variáveis de ambiente necessárias para rodar o projeto em produção no Coolify.

## 1. Banco de Dados (PostgreSQL)

| Variável | Obrigatória | Descrição | Exemplo / Valor |
| :--- | :--- | :--- | :--- |
| `POSTGRES_USER` | Sim | Usuário do banco. | `remunedata_admin` |
| `POSTGRES_PASSWORD` | Sim | Senha do banco (Segredo). | `minha_senha_segura` |
| `POSTGRES_DB` | Sim | Nome do banco de dados. | `remunedata_prod` |
| `DATABASE_URL` | Sim | URL completa para SQLAlchemy (async). | `postgresql+asyncpg://...` |
| `DATABASE_URL_SYNC` | Sim | URL completa para Alembic (sync). | `postgresql+psycopg2://...` |

## 2. Redis (Queue & Cache)

| Variável | Obrigatória | Descrição | Exemplo / Valor |
| :--- | :--- | :--- | :--- |
| `REDIS_PASSWORD` | Sim | Senha do Redis (Segredo). | `senha_redis_forte` |
| `REDIS_URL` | Sim | URL de conexão com Redis. | `redis://:senha@redis:6379/0` |

## 3. Aplicação (FastAPI / Celery)

| Variável | Obrigatória | Descrição | Exemplo / Valor |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Sim | Ambiente de execução. | `production` |
| `LOG_LEVEL` | Não | Nível de log (DEBUG, INFO, etc). | `INFO` |
| `CORS_ORIGINS` | Não | JSON array de origens permitidas. | `["https://remunedata.com.br"]` |
| `DB_HOST` | Sim | Hostname interno do banco. | `db` |
| `REDIS_HOST` | Sim | Hostname interno do Redis. | `redis` |

## 4. Infraestrutura (Coolify / GitHub)

| Variável | Onde Configurar | Descrição |
| :--- | :--- | :--- |
| `COOLIFY_WEBHOOK` | GitHub Secrets | URL de trigger do Coolify. |
| `GITHUB_TOKEN`| Automático | Token para push no GHCR. |

---

> [!IMPORTANT]
> No Coolify, estas variáveis devem ser cadastradas na aba **Environment Variables** do Resource (Service Stack). Certifique-se de marcar senhas como "Secret".

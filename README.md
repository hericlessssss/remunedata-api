# df-remuneration-collector

> Ferramenta de RPA para coleta de dados de remuneração dos servidores públicos do Distrito Federal a partir do Portal da Transparência do DF.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Objetivo](#objetivo)
- [Stack](#stack)
- [Pré-requisitos](#pré-requisitos)
- [Makefile (Atalhos)](#makefile-atalhos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Como Testar (Manual)](#como-testar-manual)
- [Como subir com Docker Compose](#como-subir-com-docker-compose)
- [Como rodar sem Docker](#como-rodar-sem-docker)
- [Como executar migrations](#como-executar-migrations)
- [Como rodar os testes](#como-rodar-os-testes)
- [Como verificar cobertura](#como-verificar-cobertura)
- [Endpoints disponíveis](#endpoints-disponíveis)
- [Troubleshooting](#troubleshooting)

---

## Visão Geral

Este projeto coleta, armazena e expõe dados de remuneração dos servidores públicos do DF a partir da API do Portal da Transparência do DF (`https://www.transparencia.df.gov.br/api/remuneracao`).

A coleta é feita por competência mensal (`anoExercicio` + `mesReferencia`) usando paginação com `size=150` (teto validado da API), armazenando os resultados em PostgreSQL com rastreabilidade completa de cada execução.

---

## Objetivo

- Coletar dados de remuneração paginados da API pública do DF
- Persistir os dados em PostgreSQL com modelo estruturado e rastreável
- Expor consultas via API REST (FastAPI)
- Permitir exportação em CSV/XLSX com limites de segurança (5k/1k)
- Suportar execução via worker assíncrono (Celery + Redis) e agendamento (Celery Beat)
- Disponibilizar Dashboard Analítico local

---

## Stack

- **Python 3.12** — linguagem principal
- **FastAPI** + **Uvicorn** — API REST
- **PostgreSQL 16** — banco relacional
- **SQLAlchemy 2.x** (async) — ORM
- **Alembic** — migrations
- **Redis 7** — cache e fila
- **Celery** — worker assíncrono e agendamento
- **httpx** — cliente HTTP para a API do Portal
- **Pydantic v2** — validação e configuração
- **Docker** + **Docker Compose** — ambiente padronizado
- **pytest** + **coverage.py** + **tox** — qualidade e testes

---

## Pré-requisitos

### Para rodar com Docker (recomendado)
- Docker Desktop >= 24 instalado e em execução
- Docker Compose (incluído no Docker Desktop)
- Git

### Para rodar sem Docker
- Python 3.12 instalado
- PostgreSQL 16 rodando localmente
- Redis 7 rodando localmente
- Git

## Makefile (Atalhos)

Para facilitar o dia a dia, incluí um `Makefile` com os comandos mais comuns.

### Instalação do make por Sistema Operacional:

#### **Windows (Recomendado)**
Se você ainda não tem o `make` instalado, abra o PowerShell como **Administrador** e execute:
```powershell
winget install GnuWin32.Make
```
Após instalar, execute o comando abaixo (também no PowerShell) para adicionar o `make` ao seu PATH permanentemente:
```powershell
$makePath = "C:\Program Files (x86)\GnuWin32\bin"
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$makePath", "User")
```
Nota: Feche e abra o seu terminal (e o VS Code) para que a alteração tenha efeito.

#### **macOS**
```bash
brew install make
```

#### **Linux (Ubuntu/Debian)**
```bash
sudo apt update && sudo apt install make
```

### Comandos Disponíveis:

| Comando | Descrição |
|---|---|
| `make up` | Sobe todos os serviços via Docker (app, worker, scheduler, db, redis) |
| `make down` | Para e remove os containers |
| `make build` | Reconstrói as imagens Docker |
| `make test` | Executa todos os testes automatizados |
| `make migrate` | Aplica as migrations do banco de dados |
| `make logs` | Acompanha os logs de todos os serviços |
| `make status` | Verifica o status dos serviços |
| `make clean` | **Reseta o ambiente** (apaga containers e volumes de dados) |

---

## Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/hericlessssss/df-remuneration-collector.git
cd df-remuneration-collector
```

### 2. Criar o arquivo .env

Copie o arquivo de exemplo e edite com suas configurações:

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Abra o `.env` e ajuste os valores se necessário. Para desenvolvimento local com Docker, os valores padrão já funcionam.

**Variáveis obrigatórias:**

```env
# URL de conexão assíncrona (SQLAlchemy 2.x)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/df_remuneration

# URL de conexão síncrona (Alembic migrations)
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@postgres:5432/df_remuneration
```

Atenção: O arquivo `.env` **nunca deve ser commitado**. Está no `.gitignore`.

---

## Como Testar (Manual)

Se você deseja validar as funcionalidades (coleta, busca e exportação) passo a passo, consulte o nosso:

**[Guia de Testes Direto ao Ponto (TESTING.md)](./TESTING.md)**

---

## Como subir com Docker Compose

### Build e subida completa

```bash
# Build da imagem e subida de todos os serviços (app + postgres + redis)
docker compose up --build
```

### Subida em background (detached)

```bash
docker compose up -d --build
```

### Ver logs em tempo real

```bash
docker compose logs -f app
```

### Parar os serviços

```bash
# Para sem remover volumes (banco preservado)
docker compose down

# Para e remove volumes (banco APAGADO -- use com cuidado)
docker compose down -v
```

### Verificar se tudo está rodando

```bash
docker compose ps
```

Saída esperada:
```
NAME                       STATUS
df_remuneration_app        running
df_remuneration_postgres   running (healthy)
df_remuneration_redis      running (healthy)
```

### Acessar a aplicação

- **Dashboard Analítico:** `http://localhost:8000/dashboard/`
- **Docs (Swagger):** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/health`

### Serviços em Execução

O projeto sobe 5 serviços principais:
1. **app**: API FastAPI (Porta 8000)
2. **worker**: Processamento de coletas em background (com fix de memória)
3. **scheduler**: Agendamento de coletas periódicas (Celery Beat)
4. **postgres**: Banco de dados (Porta 5432)
5. **redis**: Broker de mensagens para o Celery

---

## Como rodar sem Docker

### 1. Criar e ativar ambiente virtual

```bash
# Criar o venv
python -m venv .venv

# Ativar no Linux / macOS
source .venv/bin/activate

# Ativar no Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependências

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. Configurar o .env

Edite o `.env` para apontar para `localhost` (não para `postgres`):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/df_remuneration
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/df_remuneration
REDIS_URL=redis://localhost:6379/0
```

### 4. Garantir PostgreSQL e Redis rodando

Você pode usar Docker apenas para os serviços de infraestrutura:

```bash
docker compose up -d postgres redis
```

### 5. Iniciar a aplicação

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Como executar migrations

As migrations criam e atualizam as tabelas do banco de dados.

### Com Docker (recomendado)

```bash
# Aplicar todas as migrations pendentes
docker compose run --rm app alembic upgrade head

# Ver histórico de migrations
docker compose run --rm app alembic history

# Criar uma nova migration (apos alterar models.py)
docker compose run --rm app alembic revision --autogenerate -m "descricao_da_mudanca"

# Reverter a ultima migration
docker compose run --rm app alembic downgrade -1
```

### Localmente (com venv ativo)

```bash
alembic upgrade head
alembic history
alembic revision --autogenerate -m "descricao_da_mudanca"
alembic downgrade -1
```

---

## Como rodar os testes

### Com Docker (recomendado)

```bash
# Rodar todos os testes
docker compose run --rm app pytest tests/ -v

# Rodar um arquivo especifico
docker compose run --rm app pytest tests/test_health.py -v

# Rodar com logs visíveis
docker compose run --rm app pytest tests/ -v -s
```

### Localmente (com venv ativo)

```bash
pytest tests/ -v --tb=short
```

---

## Como verificar cobertura

```bash
# Com Docker
docker compose run --rm app coverage run -m pytest tests/ -v
docker compose run --rm app coverage report -m

# Localmente
coverage run -m pytest tests/ -v
coverage report -m

# Gerar relatorio HTML
coverage html
```

A cobertura mínima configurada é **86%** (alcançado: **87.7%**).

---

## Endpoints disponíveis

| Método | URL | Descrição |
|---|---|---|
| GET | `/api/v1/remuneration/summary` | Dashboard Summary (agregados/top orgaos) |
| GET | `/api/v1/remuneration/` | Busca com filtros (nome, cpf, cargo, orgao) |
| POST | `/api/v1/executions/` | Dispara nova coleta anual |
| GET | `/api/v1/executions/` | Lista execuções |
| GET | `/api/v1/executions/{id}/export` | Exporta CSV/XLSX (limites: 5k/1k) |
| GET | `/dashboard/` | Interface visual do Dashboard |
| GET | `/health` | Health Check |

---

## Troubleshooting

### docker compose up falha com "port already in use"

Algum processo local está usando a porta 8000, 5432 ou 6379. 

Pare os serviços locais de Postgres/Redis se estiver usando Docker.

### ModuleNotFoundError: No module named 'app'

Instale o pacote em modo editável:
```bash
pip install -e ".[dev]"
```

---

## Documentação técnica

A pasta `/docs` contém toda a documentação funcional detalhada. Para decisões técnicas e histórico de mudanças, consulte [`PROJECT.md`](./PROJECT.md).

---

## CI/CD e Deploy

Este projeto está preparado para deploy automatizado via GitHub Actions e Coolify.

- **Fluxo de CI/CD:** documentado em [`docs/cicd.md`](./docs/cicd.md).
- **Configuração Coolify:** documentado em [`docs/coolify-setup.md`](./docs/coolify-setup.md).
- **Estratégia de Ambientes:** documentado em [`docs/environment-strategy.md`](./docs/environment-strategy.md).
```

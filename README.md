# df-remuneration-collector

> Ferramenta de RPA para coleta de dados de remuneração dos servidores públicos do Distrito Federal a partir do Portal da Transparência do DF.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Objetivo](#objetivo)
- [Stack](#stack)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
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
- Permitir exportação em CSV/XLSX (futuro)
- Suportar execução via worker assíncrono (Celery + Redis) e agendamento (futuro)

---

## Stack

- **Python 3.12** — linguagem principal
- **FastAPI** + **Uvicorn** — API REST
- **PostgreSQL 16** — banco relacional
- **SQLAlchemy 2.x** (async) — ORM
- **Alembic** — migrations
- **Redis 7** — cache e fila
- **Celery** — worker assíncrono (futuro)
- **httpx** — cliente HTTP para a API do Portal
- **Pydantic v2** — validação e configuração
- **Docker** + **Docker Compose** — ambiente padronizado
- **pytest** + **coverage.py** + **tox** — qualidade e testes

---

## Pré-requisitos

### Para rodar com Docker (recomendado)
- [Docker Desktop](https://docs.docker.com/desktop/) >= 24 instalado e em execução
- [Docker Compose](https://docs.docker.com/compose/) (incluído no Docker Desktop)
- Git

### Para rodar sem Docker
- Python 3.12 instalado ([python.org](https://www.python.org/downloads/))
- PostgreSQL 16 rodando localmente
- Redis 7 rodando localmente
- Git

---

## Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/df-remuneration-collector.git
cd df-remuneration-collector
```

### 2. Criar o arquivo `.env`

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

> ⚠️ **Atenção:** O arquivo `.env` **nunca deve ser commitado**. Está no `.gitignore`.

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
# Parar sem remover volumes (banco preservado)
docker compose down

# Parar e remover volumes (banco APAGADO — use com cuidado)
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

- **Health check:** `http://localhost:8000/health`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

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

### 3. Configurar o `.env`

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

# Criar uma nova migration (após alterar models.py)
docker compose run --rm app alembic revision --autogenerate -m "descricao_da_mudanca"

# Reverter a última migration
docker compose run --rm app alembic downgrade -1
```

### Localmente (com venv ativo)

```bash
alembic upgrade head
alembic history
alembic revision --autogenerate -m "descricao_da_mudanca"
alembic downgrade -1
```

> **Nota:** Por enquanto, não há tabelas criadas (etapa 1 = bootstrap). As migrations de tabelas reais serão adicionadas na Etapa 3.

---

## Como rodar os testes

### Com Docker (recomendado)

```bash
# Rodar todos os testes
docker compose run --rm app pytest tests/ -v

# Rodar um arquivo específico
docker compose run --rm app pytest tests/test_health.py -v

# Rodar com logs visíveis
docker compose run --rm app pytest tests/ -v -s
```

### Localmente (com venv ativo)

```bash
pytest tests/ -v --tb=short
```

### Com tox (simula CI)

```bash
tox
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

# Gerar relatório HTML
coverage html
# Abrir htmlcov/index.html no navegador
```

A cobertura mínima exigida é **80%** (configurada em `pyproject.toml`).

---

## Endpoints disponíveis

| Método | URL | Descrição |
|---|---|---|
| GET | `/health` | Verifica se a aplicação está viva |
| GET | `/docs` | Swagger UI (documentação interativa) |
| GET | `/redoc` | ReDoc (documentação alternativa) |

> Mais endpoints serão adicionados nas próximas etapas.

---

## Troubleshooting

### `docker compose up` falha com "port already in use"

Algum processo local está usando a porta 8000, 5432 ou 6379.

```bash
# Ver o que está usando a porta (ex: 5432)
# Windows
netstat -ano | findstr :5432

# Parar o processo ou alterar a porta no docker-compose.yml
```

### `ModuleNotFoundError: No module named 'app'`

Instale o pacote em modo editável:

```bash
pip install -e ".[dev]"
```

### `ValidationError: DATABASE_URL is required`

Crie o arquivo `.env` a partir do `.env.example`:

```bash
# Windows PowerShell
Copy-Item .env.example .env
```

### Erro de conexão com PostgreSQL

Verifique se o container `postgres` está saudável:

```bash
docker compose ps
docker compose logs postgres
```

### `alembic: command not found`

Certifique-se de que o pacote está instalado e o venv está ativado:

```bash
pip install -e ".[dev]"
```

---

## Documentação técnica

A pasta `/docs` contém toda a documentação funcional construída antes do código:

| Arquivo | Conteúdo |
|---|---|
| `01-descoberta-da-fonte-de-dados.md` | Análise da API do Portal da Transparência |
| `02-contrato-da-fonte.md` | Parâmetros e estrutura da resposta |
| `03-validacao-da-chamada-minima.md` | Chamada HTTP mínima validada |
| `04-validacao-da-paginacao.md` | Paginação validada |
| `05-validacao-do-limite-de-size.md` | Limite real de size=150 validado |
| `06-validacao-do-filtro-por-nome.md` | Filtro por nome funcional |
| `07-validacao-do-filtro-por-cpf.md` | Filtro por CPF não funcional |
| `08-validacao-da-ordenacao-padrao.md` | Ordenação estável validada |
| `09-validacao-do-fim-da-paginacao.md` | Condições de parada validadas |
| `10-validacao-da-estrategia-anual.md` | Coleta mensal validada |
| `11-algoritmo-minimo-da-coleta.md` | Algoritmo mínimo do coletor |
| `12-contrato-minimo-do-coletor.md` | Contrato de entrada/saída |
| `13-modelo-minimo-de-persistencia.md` | Modelo mínimo de banco |
| `14-estrutura-minima-do-projeto.md` | Estrutura de pastas |
| `15-stack-minimo-e-bootstrap.md` | Stack e ordem de bootstrap |

Para decisões técnicas e histórico de mudanças, consulte [`PROJECT.md`](./PROJECT.md).

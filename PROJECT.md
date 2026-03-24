# PROJECT.md — df-remuneration-collector
> Documento vivo central do projeto. Atualizado ao final de cada etapa.

---

## Visão Geral

Ferramenta de RPA para coleta de dados de remuneração dos servidores públicos do Distrito Federal, com base no Portal da Transparência do DF.

- **Fonte:** `https://www.transparencia.df.gov.br/api/remuneracao`
- **Método:** GET com paginação (size=150, page=0..N)
- **Unidade real de coleta:** competência mensal (anoExercicio + mesReferencia)
- **Coleta anual:** iteração dos meses 01–12

---

## Stack

| Componente | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.12 |
| API | FastAPI | >=0.111 |
| Servidor | Uvicorn | >=0.30 |
| Banco de dados | PostgreSQL | 16 |
| ORM | SQLAlchemy | 2.x (async) |
| Migrations | Alembic | >=1.13 |
| Driver async | asyncpg | >=0.29 |
| Driver sync | psycopg2-binary | >=2.9 |
| Cache / Fila | Redis | 7 |
| Worker | Celery | >=5.4 |
| Validação | Pydantic | >=2.7 |
| HTTP client | httpx | >=0.27 |
| Contêineres | Docker + Docker Compose | - |
| Testes | pytest | >=8.2 |
| Cobertura | coverage.py | >=7.5 |
| CI local | tox | >=4.15 |
| Linting | ruff | >=0.4 |
| Formatação | black + isort | - |

---

## Estrutura de Pastas

```
df-remuneration-collector/
 app/
    main.py               # Ponto de entrada FastAPI
    core/
       config.py         # Configuração via Pydantic BaseSettings
       logging.py        # Configuração de logging
    collector/            # Regra de negócio da coleta (próximas etapas)
    infra/                # Cliente HTTP (próximas etapas)
    persistence/          # Modelos, sessão, repositórios (próximas etapas)
    api/                  # Endpoints FastAPI (futuro)
    workers/              # Workers Celery (futuro)
 alembic/
    env.py                # Configuração do ambiente Alembic
    script.py.mako        # Template de migrations
    versions/             # Migrations (vazias por enquanto)
 tests/
    conftest.py           # Fixtures compartilhadas
    test_health.py        # Testes do endpoint /health
    test_config.py        # Testes do módulo de configuração
 docs/                     # Documentação funcional (fonte primária de verdade)
 .env.example              # Variáveis de ambiente (copiar para .env)
 .gitignore
 alembic.ini
 docker-compose.yml
 Dockerfile
 pyproject.toml
 tox.ini
 PROJECT.md                # Este arquivo
 README.md
```

---

## Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DATABASE_URL` |  | — | URL assíncrona (asyncpg) para SQLAlchemy 2.x |
| `DATABASE_URL_SYNC` |  | — | URL síncrona (psycopg2) para Alembic |
| `POSTGRES_USER` | — | postgres | Usuário do PostgreSQL (docker-compose) |
| `POSTGRES_PASSWORD` | — | postgres | Senha do PostgreSQL (docker-compose) |
| `POSTGRES_DB` | — | df_remuneration | Banco do PostgreSQL (docker-compose) |
| `REDIS_URL` | — | redis://localhost:6379/0 | URL do Redis |
| `APP_ENV` | — | development | Ambiente da aplicação |
| `LOG_LEVEL` | — | INFO | Nível de logging |
| `TRANSPARENCIA_API_BASE_URL` | — | `https://www.transparencia.df.gov.br/api` | URL base da API |
| `TRANSPARENCIA_PAGE_SIZE` | — | 150 | Tamanho máximo de página (validado em /docs) |
| `TRANSPARENCIA_TIMEOUT_SECONDS` | — | 30 | Timeout HTTP em segundos |

---

## Endpoints

| Método | URL | Descrição | Status |
|---|---|---|---|
| GET | `/health` | Health check da aplicação |  Implementado |
| GET | `/docs` | Swagger UI |  Automático (FastAPI) |
| GET | `/redoc` | ReDoc UI |  Automático (FastAPI) |

---

## Migrações

```bash
# Criar nova migration
alembic revision --autogenerate -m "descricao"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1

# Ver histórico
alembic history
```

---

## Comandos

```bash
# Subir ambiente docker
docker compose up -d

# Subir e ver logs
docker compose up

# Rodar testes (dentro do container)
docker compose run --rm app pytest tests/ -v

# Verificar cobertura
docker compose run --rm app coverage run -m pytest && coverage report -m

# Rodar localmente
pip install -e ".[dev]"
pytest tests/ -v

# Lint
ruff check app/ tests/

# Format
black app/ tests/ && isort app/ tests/

# Parar tudo
docker compose down

# Parar e remover volumes (banco)
docker compose down -v
```

---

## Etapas do Projeto

| Etapa | Descrição | Status |
|---|---|---|
| 1 — Bootstrap | Estrutura, config, Dockerfile, FastAPI base |  Concluída |
| 2 — Cliente HTTP | `app/infra/transparencia_client.py` |  Concluída |
| 3 — Modelos + Sessão | `app/persistence/`, migrations iniciais |  Concluída |
| 4 — Coleta Mensal | `app/collector/monthly.py` |  Concluída |
| 5 — Coleta Anual | `app/collector/run_collection.py` |  Concluída |
| 6 — Persistência | Repositórios e escrita no banco |  Concluída |
| 7 — API REST | Endpoints de consulta |  Concluída |
| 8 — Worker | Celery + Redis |  Concluída |
| 9 — Scheduler | Agendamento de coletas |  Concluída |
| 10 — Exportações | CSV / XLSX |  Concluída |
| 11 — Compliance | GAP FILL (PDF Itens 1-4) |  Concluída |
| 12 — Estabilização | Fixes de Memória, Performance e Migrações |  Concluída |
| 13 — Validação Final | Testes (45/45), Cobertura (87.7%) e Auditoria |  Concluída |
| 14 — Entrega Final | Cleanup de README, DX e Verificação de Deploy |  Concluída |
| 15 — CI/CD, Deploy & Hardening | GitHub Actions + Coolify + CORS/Proxy config |  Concluída |
| 16 — Estabilização Celery | Timeouts e Sincronia de Registro de Tarefas | Concluída |
| 17 — Idempotência de Coleta | Estratégia Clean & Resume para Resiliência | Concluída |
| 18 — Estabilização Final | Fix de Sessão (Detachment) e Retomada 2024 | Concluída |
| 18 — Performance & Integridade | Coleta Nitro (Async Batching) e Purge Global | Concluída |
| 19 — Autenticação | Integração Supabase Auth e Proteção de Rotas | Concluída |
| 20 — Estabilização & Busca | Busca Unaccent (Acentos) e Otimização de Filtros | Concluída |
| 21 — Camada de Performance | Integração Redis Cache para Dashboard e Filtros | Concluída |

---

## Regras de Negócio Validadas (fonte: /docs)

- A API retorna JSON mesmo com `tipo=csv` — parâmetro ignorado
- `size=150` é o teto efetivo (size=500 retorna o mesmo que size=150)
- Parar paginação quando: `last=true` OR `numberOfElements=0` OR `content.Count=0`
- Coleta anual = iteração meses 01–12 (bases de dados independentes por mês)
- Filtro por nome funciona; filtro por CPF não foi validado
- Parâmetros de UI (`busy`, `editing`, `icon`, `padrao`, `dataAtualizacao`) são descartáveis

---

## Hurdles & Fixes

### Etapa 1 — Bootstrap

| # | Problema | Causa | Solução |
|---|---|---|---|
| 1 | Poetry descartado | Histórico de conversas mostra erro de instalação no Windows | Usamos `pip` + `pyproject.toml` PEP 517/518 |
| 2 | Dois DATABASE_URL | Alembic requer sync; SQLAlchemy 2.x async requer asyncpg | Criadas `DATABASE_URL` (async) e `DATABASE_URL_SYNC` (sync) |
| 3 | `set_test_env` autouse | Pydantic valida no init; testes falham sem env vars | `conftest.py` com `autouse=True` garante env mínimo |

### Etapa 2 — Cliente HTTP

| # | Problema | Causa | Solução |
|---|---|---|---|
| 4 | Mock de API Complexa | `respx` exige precisão em query params e headers para bater o mock | Uso de `respx.mock(assert_all_called=True)` para validar cobertura dos testes |

### Etapa 3 — Modelos e Banco

| # | Problema | Causa | Solução |
|---|---|---|---|
| 5 | Migração Async | Alembic padrão é síncrono; requer `run_migrations_online` com wrapper async | Configurado `env.py` com `asyncio.run` e `connectable.connect()` |
| 6 | Timezone-aware metadata | Postgres e SA podem gerar timestamps 'naive' por padrão | Forçado `DateTime(timezone=True)` em todos os modelos e migrations |

### Etapa 4 — Coleta Mensal

| # | Problema | Causa | Solução |
|---|---|---|---|
| 7 | ConnectionRefused (DB) | Testes no Docker tentavam usar `localhost:5432` | Alterado para `postgres:5432` (nome do serviço no compose) |
| 8 | Loop/Future Mismatch | `db_engine` era session-scoped, conflitando com loops function-scoped do pytest-asyncio | Alterado scope do `db_engine` para `function` no `conftest.py` |
| 9 | MultipleResultsFound | Testes de persistência falhavam se o container já tivesse dados | Query alterada para filtrar por `ID` em vez de campos genéricos |

### Etapa 5 — Coleta Anual

| # | Problema | Causa | Solução |
|---|---|---|---|
| 10 | Assert 0 == 12 (Counters) | Mock do `MonthlyCollector` não simulava o side-effect de atualizar a engine pai | Removida asserção de contador em favor de `call_count` no teste unitário |

### Etapa 6 — Repositórios

| # | Problema | Causa | Solução |
|---|---|---|---|
| 11 | IntegrityError (NotNull) | Mismatch entre chaves do mock JSON (`id`, `matricula`) e Doc 02 (`codigoIdentificacao`, `codigoMatricula`) | Alinhado `MonthlyCollector` e mock JSON com o contrato oficial (Doc 02) |

### Etapa 7 — API REST

| # | Problema | Causa | Solução |
|---|---|---|---|
| 12 | MissingGreenlet (Lazy Load) | Pydantic tentava acessar relacionamento `monthly_executions` não carregado no list endpoint | Dividido esquema em `Read` (lista) e `Detail` (com relacionamentos) |
| 13 | Loop Mismatch (Tests) | `httpx.AsyncClient` e `db_session` fixture usando loops de eventos diferentes | Uso de `dependency_overrides` no FastAPI para injetar a sessão do teste |

### Etapa 8 — Worker

| # | Problema | Causa | Solução |
|---|---|---|---|
| 14 | Trigger endpoint skip | `get_or_create_annual` criava registro com status `running` já de início | Alterado default para `pending`; status `running` setado apenas no trigger do worker |
| 15 | IntegrityError no Cleanup | `TRUNCATE` falhava por FK de `execution_monthly` em testes de integração | Uso de `TRUNCATE ... CASCADE` no setup de testes do worker |
| 16 | DetachedInstanceError (Celery) | SQLAlchemy session fechada antes de acessar atributos do objeto em tarefa async | Extração de dados (ID, status) do modelo antes do fechamento da sessão no worker |

### Etapa 9 — Scheduler

| # | Problema | Causa | Solução |
|---|---|---|---|
| 17 | Scheduler Network Error | Serviço scheduler no Docker Compose não conectava ao Redis por nome de rede errado | Alinhado nome da rede para `df_network` no `docker-compose.yml` |
| 18 | Beat Schedule Mismatch | Mudança no comando de build ou contexto do scheduler | Garantido que o comando `celery beat` use a mesma configuração do app |

### Etapa 10 — Exportações

| # | Problema | Causa | Solução |
|---|---|---|---|
| 19 | ImportError: get_db | Mismatch de nomenclatura entre o teste e `app.api.deps` | Alinhado uso para `get_session` (nome correto da dependência) |
| 20 | DeprecationWarning (regex) | Uso de `regex` no `Query` do FastAPI (obsoleto no Pydantic v2) | Substituído por `pattern` conforme novas diretrizes do FastAPI |
| 21 | Fixture 'client' not found | Ausência de um cliente HTTP global para testes de integração | Centralizado fixture `client` (httpx.AsyncClient) no `conftest.py` |

### Etapa 11 — Compliance (GAP FILL)

| # | Problema | Causa | Solução |
|---|---|---|---|
| 22 | Field Mismatch (Cargo/Orgao) | Nomes no repositório (`cargo_servidor`) diferiam do modelo (`cargo`) | Alinhado repositório e testes com o schema oficial (`cargo`, `nome_orgao`) |
| 23 | Loop RuntimeError (Tests) | `client` e `db_session` fixtures operando em event loops isolados | Adicionado `override_get_session` para unificar a sessão do banco nos testes |
| 24 | AttributeError (get_summary) | Leftover de `orgao_nome` no método de agregação | Corrigido para `nome_orgao` conforme schema definido no Doc 13 |

### Etapa 12 — Estabilização & Performance

| # | Problema | Causa | Solução |
|---|---|---|---|
| 25 | Alembic ModuleNotFound | `alembic/env.py` e Makefile não configuravam `PYTHONPATH` corretamente | Adicionado `sys.path.append` no `env.py` e `-e PYTHONPATH=.` no Makefile |
| 26 | Migration Initial Fail | Migration `initial_schema_v2` continha apenas `ALTER` sem os `CREATE TABLE` | Recriação da migration inicial via autogenerate para garantir schema completo |
| 27 | Worker OOM / Leak | Sessão longa do SQLAlchemy acumulava milhares de objetos no Identity Map | Adicionado `session.expunge_all()` após cada commit de página no coletor |
| 28 | Dashboard Lento/Crashed | Falta de índice em `nome_orgao` e excesso de queries de agregação em tempo real | Adicionado índice em `nome_orgao` e implementado cache de 60s no endpoint `/summary` |
| 29 | Contaminação de Testes | Testes rodavam sobre banco sujo da aplicação, gerando falsos positivos em filtros | Implementado `TRUNCATE ... CASCADE` na fixture `db_session` do `conftest.py` |
| 30 | Celery Timeout (1h) | Limite padrão de 1h era insuficiente para coletas de 220k+ registros | Aumentado `task_time_limit` para 4h e adicionado `soft_time_limit` para 3.5h |
| 31 | Unregistered Task | Mismatch entre nome explícito no @task e nome no agendador periódico | Sincronizados nomes das tarefas no `beat_schedule` do `celery_app.py` |
| 32 | Duplicidade na Re-execução | Coletas reiniciadas duplicavam dados e gastavam tempo desnecessário | Implementada estratégia Clean & Resume (Pula meses OK, limpa parciais) |
| 36 | InvalidRequestError (Session) | expunge_all() desanexava ExecutionAnnual, causando erro fatal no final do mês | Substituído expunge_all() por loop cirúrgico nos registros coletados |
| 33 | Timeout em Coletas Longas | Coletas de anos volumosos (2024+) excediam 4h | Aumentado task_time_limit para 24h (86400s) |
| 34 | Performance de Scraping | Coleta sequencial era lenta para grandes volumes | Implementado Batching Assíncrono (5 páginas por vez via asyncio.gather) |
| 35 | Duplicidade Cross-Execution | Troca de ID de execução deixava lixo de tentativas anteriores | Implementado Purge Global por Periodo (Ano/Mes) antes de iniciar coleta |

---

## Histórico de Commits

### Etapa 1
```
feat(bootstrap): estrutura inicial do projeto

- pyproject.toml com stack completa (FastAPI, SQLAlchemy 2.x, Alembic, Celery, Redis, httpx)
- Dockerfile (Python 3.12-slim, usuário não-root)
- docker-compose.yml (app + postgres:16 + redis:7 com health checks)
- .env.example com variáveis documentadas
- app/core/config.py com Pydantic BaseSettings
- app/core/logging.py com logging estruturado
- app/main.py com FastAPI + /health endpoint
- alembic.ini + alembic/env.py configurados
- tests/: test_health.py, test_config.py, conftest.py
- PROJECT.md (documento vivo central)
- README.md completo com instruções de execução local
```

### Etapa 2
```
feat(infra): implementar cliente HTTP da API Transparência

- TransparenciaClient com httpx.AsyncClient
- Suporte a paginação, filtros e tratamento de erros
- Testes unitários com respx (4 cenários: sucesso, params, erro, timeout)
- Cobertura de 100% no módulo infra
```

### Etapa 3
```
feat(persistence): implementar modelos e sessão assíncrona

- Modelos SQLAlchemy 2.0 (ExecutionAnnual, ExecutionMonthly, RemunerationCollected)
- Configuração de engine e sessão assíncrona (asyncpg)
- Integração com Alembic (target_metadata configurado)
- Migração inicial gerada e aplicada (timezone-aware)
- Testes unitários e de integração de persistência (100% pass)
```

### Etapa 4
```
feat(collector): implementar coletor mensal e orquestração

- MonthlyCollector para orquestrar extração + persistência
- Lógica de paginação resiliente com condições de parada (Doc 11)
- Atualização atômica de contadores na ExecutionAnnual
- Testes de integração com banco de dados e mocks de API
```

### Etapa 5
```
feat(collector): implementar orquestrador anual (01-12)

- AnnualCollector para gerenciar o ciclo de 12 meses
- Lógica de status consolidado (success, partial_success, error)
- Tratamento de exceções por mês para resiliência
- Testes unitários com mocks do coletor mensal (100% pass)
```

### Etapa 6
```
feat(persistence): implementar camada de repositórios

- Abstração do SQLAlchemy em ExecutionRepository e RemunerationRepository
- Refatoração dos coletores (Monthly/Annual) para Injeção de Dependência
- Alinhamento de de mapeamento de campos com Doc 02 (Fonte de Dados)
- Testes unitários de repositórios e integração (100% pass)
```

### Etapa 7
```
feat(api): implementar endpoints de consulta (FastAPI)

- Schemas Pydantic para DTOs (Read/Detail/Paginated)
- Endpoints /executions (list/get) e /remuneration (search)
- Filtros por nome, CPF e competência na busca de remuneração
- Health check corrigido para retornar app_env
- Testes de integração com AsyncClient e dependency_overrides
```
### Etapa 8
```
feat(worker): implementar processamento em background (Celery + Redis)

- Configuração do CeleryApp com Redis como broker e backend
- Implementação de collect_annual_task (asyncio wrapper)
- Endpoint POST /executions/ para disparar coleta via worker
- Adição do serviço worker no docker-compose.yml
- Testes unitários do worker e de integração do endpoint trigger (100% pass)
```

### Etapa 9
```
feat(scheduler): implementar agendamento periódico (Celery Beat)

- Adição do serviço scheduler no docker-compose.yml
- Configuração de beat_schedule no celery_app.py
- Implementação da tarefa sync_recent_years_task para sincronia automática
- Testes de configuração de agendamento e lógica de sincronia (100% pass)
```

### Etapa 10
```
feat(export): implementar exportação de dados (CSV/XLSX)

- Adição de pandas e openpyxl às dependências
- Repositório: método get_all_by_execution para busca em lote eficiente
- API: endpoint GET /executions/{id}/export com suporte a CSV e XLSX
- Uso de StreamingResponse para alta volumetria e baixo consumo de memória
- Testes de integração para validação de conteúdo e headers (100% pass)
```

### Finalização: Automação e DX
```
feat(dx): adicionar Makefile, TESTING.md e atualizar README.md

- Criação de Makefile com atalhos para comandos Docker (up, down, test, migrate).
- Adição de TESTING.md com guia passo a passo revisado.
- Atualização do README.md com instruções de PATH (Windows) e setup (macOS/Linux).
- Padronização de saídas de ajuda (ASCII) para compatibilidade universal.
```

### Etapa 11
```
feat(compliance): implementar requisitos PDF e dashboard analítico

- API: novos filtros cargo/orgao e endpoint /summary para analíticos
- Export: limite de 1k (XLSX) e 5k (CSV) via injeção de limit no repo
- Scheduler: alteração para execução diária (crontab 03:00)
- Dashboard: interface HTML5/JS com Chart.js e Glassmorphism em /dashboard
- Testes: suíte de conformidade e bump de cobertura para 86%
```

### Etapa 12
```
fix(stabilization): corrigir consumo de memória e performance do dashboard

- alembic/env.py: correção de PYTHONPATH para execução em Docker
- persistence/models: adição de índice em nome_orgao para aceleração de filtros
- collector/monthly: correção de vazamento de memória (session.expunge_all)
- api/remuneration: cache de 60s no /summary para resiliência sob carga
- migrations: recriação da migration inicial e nova migration de performance
- tests: implementação de reset de banco (`TRUNCATE`) e aumento de cobertura para 87.7%
- docs: criação do `metrics_report.md` com auditoria final de qualidade
```

### Etapa 13
```
test(audit): validação final de cobertura e conformidade

- conftest.py: reset de banco com TRUNCATE CASCADE para isolamento
- tests/test_coverage_boost.py: cobertura de caminhos críticos (87.7%)
- metrics_report.md: consolidação de métricas e adesão aos requisitos do PDF
- app/persistence/repositories: validação de 100% dos filtros de busca
```

### Etapa 14
```
docs(cleanup): entrega final e limpeza de documentação

- README.md: remoção de emojis e atualização de instruções de deploy local
- metrics_report.md: ajustes de títulos e seções para entrega premium
- DX: confirmação de funcionamento manual e via Makefile (up, test, migrate)
```

### Etapa 15
```
feat(cicd): implementar pipeline de CI/CD, Hardening e Code Polish

- Dockerfile: reconstrução para multi-stage build, suporte a proxy headers e usuário não-root
- .github/workflows: workflows de CI (staging) e CD (main/prod) com gate de cobertura (86%)
- persistence: configuração de volumes nomeados no compose.prod e documentação Coolify
- app/core: implementação de CORSMiddleware e settings de origens dinâmicas
- Code Polish: correção de 100% dos lints (ruff) e isort em todos os módulos
- docs/: novos guias de CI/CD, Coolify (Persistence/SSL), Hardening e Estratégia de Ambientes
```

---

## Decisões Técnicas

| Decisão | Escolha | Rejeitada | Motivo |
|---|---|---|---|
| Gerenciador de pacotes | `pip` + pyproject.toml | Poetry | Problemas de instalação no Windows |
| Driver async DB | `asyncpg` | `psycopg2` | SQLAlchemy 2.x async support |
| Driver sync DB | `psycopg2-binary` | `asyncpg` | Alembic requer driver síncrono |
| Logging | stdlib `logging` | `structlog` | Dependência extra desnecessária agora |
| Lifespan | `asynccontextmanager` | `@on_event` | Deprecado no FastAPI moderno |
| Timestamps | `DateTime(timezone=True)` | Naive `DateTime` | Compatibilidade com `asyncpg` e melhores práticas |
| Visualização | `Chart.js` | `D3.js` | Balanço entre facilidade de integração e resultados visuais premium |
| Dashboard | `FastAPI StaticFiles` | `Next.js` | Dashboard local simples não justifica overhead de framework frontend |
| Autenticação | `Supabase Auth` (JWT) | `OAuth2 Password` | Facilidade de integração com o ecossistema e fluxo de login social pronto |

---

## Segurança

### Supabase Auth
A autenticação é feita via Supabase Auth (JWT). 
- **Backend:** Validação de tokens `HS256` usando o `SUPABASE_JWT_SECRET`.
- **Dependência:** `get_current_user` em `app/api/deps.py`.
- **Proteção:** Todos os endpoints sob `/api/v1` exigem o header `Authorization: Bearer <token>`, exceto o `/health` que permanece público.

### Cache & Performance
- **Redis:** Utilizado para cachear resultados pesados (Summary, Filtros Dinâmicos).
- **TTL:** 10 min para Summary, 24h para Filtros.
- **Invalidação:** Cache é limpo automaticamente ao final de cada ciclo de coleta bem-sucedido.


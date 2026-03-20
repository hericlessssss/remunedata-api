# Coolify Deployment Assessment (v4.0.0-beta.463)

## 1. Estado Atual do Repositório

### Arquitetura de Containers
- **API (FastAPI)**: Imagem base `python:3.12-slim`, multi-stage build, usuário não-root (`appuser`).
- **Worker (Celery)**: Mesma imagem da API, rodando comando `worker`.
- **Scheduler (Celery Beat)**: Mesma imagem da API, rodando comando `beat`.
- **Banco de Dados**: PostgreSQL 16 Alpine.
- **Cache/Broker**: Redis 7 Alpine.

### Configuração de Rede (Crítico)
- Atualmente o `docker-compose.prod.yml` utiliza **IPs fixos** (`172.28.0.10`, `172.28.0.20`) e uma subrede customizada (`172.28.0.0/16`).
- As URLs de conexão (`DATABASE_URL`, `REDIS_URL`) estão apontando para esses IPs.
- O `entrypoint.sh` tenta resolver o `DB_HOST` via Python `socket.gethostbyname`.

### Fluxo de Migrations
- Executado no `entrypoint.sh` via `alembic upgrade head`.
- **Risco**: Se a API, o Worker e o Scheduler subirem simultaneamente, todos tentarão aplicar migrations ao mesmo tempo, gerando lock ou corrupção.

### CI/CD
- Workflow `cd-main.yml` funcional: build -> push (GHCR) -> trigger webhook.
- O trigger do Coolify é um `curl -X POST` simples, sem validação de sucesso do rollout.

---

## 2. Incompatibilidades e Riscos com Coolify v4.0.0-beta.463

1. **IPs Fixos**: Coolify gerencia sua própria rede Docker e proxy reverso. Forçar IPs pode conflitar com outros recursos no mesmo servidor ou falhar se a interface virtual não for criada exatamente como esperado.
2. **DNS Interno**: O Coolify espera que os serviços se comuniquem pelo nome definido no Compose (ex: `http://db-remune:5432`).
3. **Healthchecks**: No Compose atual, a API não possui `healthcheck`, apenas `depends_on`. O Coolify precisa de healthchecks reais para saber quando o tráfego pode ser direcionado ao container.
4. **Migrations no Boot**: Em um ambiente de "Stack" do Coolify, os serviços podem reiniciar de forma imprevisível. Rodar migration no boot de cada replica é um anti-padrão de produção.

---

## 3. Diagnóstico Técnico

- **Complexidade Desnecessária**: O uso de IPs fixos foi uma tentativa de contornar problemas de DNS que não deveriam existir se a configuração de rede padrão do Docker/Coolify fosse usada corretamente.
- **Fragilidade no Boot**: O loop de wait no `entrypoint.sh` é robusto, mas o acoplamento com migrations dificulta o escalonamento lateral.
- **Falta de Observabilidade**: Não há smoke tests pós-deploy no pipeline de CI/CD.

---

## 4. Proposta de Arquitetura Alvo

### Mudanças Estruturais
- **Remover Subnets e IPs**: Voltar ao padrão de service discovery do Docker Compose.
- **Service Naming**: Usar `db` e `redis` como hostnames internos.
- **Migration Service**: Definir um serviço "migrator" (one-off) ou garantir que apenas a API execute migrations de forma controlada (ex: `depends_on` condition).
- **Consolidação de Imagem**: Manter a imagem única (já feito), mas otimizar o build para produção.

### Estratégia Coolify
- **Deploy via Stack (Docker Compose)**.
- **Exposição**: Apenas o serviço `api` terá um FQDN atribuído no Coolify.
- **Registry**: Configurar credenciais do GHCR no Coolify.
- **Variables**: Mover segredos (senhas de banco, etc) para a aba "Environment Variables" do Coolify.

---

## 5. Próximos Passos

1. Validar a arquitetura alvo.
2. Ajustar `docker-compose.prod.yml`.
3. Ajustar `entrypoint.sh`.
4. Refatorar pipeline de CI/CD para incluir versionamento por SHA e smoke tests.

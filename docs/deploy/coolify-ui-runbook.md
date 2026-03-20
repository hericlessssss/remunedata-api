# Coolify UI Runbook (v4.0.0-beta.463)

Guia passo a passo para configurar o ambiente do RemuneData do zero no Coolify.

## 1. Pré-requisitos
- Coolify v4.0.0-beta.463 instalado e operacional.
- Domínio `api.remunedata.com.br` apontando para o IP do servidor Coolify (DNS A Record).
- Repositório GitHub conectado ao Coolify.

## 2. Criação do Recurso
1. No Dashboard, clique em **+ New Resource**.
2. Escolha **Public Repository** ou **Private Repository**.
3. Selecione o repositório `remunedata-api`.
4. Em **Build Pack**, selecione obrigatoriamente **Docker Compose**.
5. Em **Base Directory**, mantenha `/`.
6. Em **Docker Compose Location**, preencha `docker-compose.prod.yml`.

## 3. Configuração de Variáveis (Essencial)
Navegue até a aba **Environment Variables** e adicione todas as variáveis do arquivo `docs/deploy/env-production-reference.md`.

> [!TIP]
> Use o botão "Bulk Edit" para colar as variáveis do arquivo `.env.example.production` e depois altere apenas os valores sensíveis. Marque `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `DATABASE_URL` e `REDIS_URL` como **Secret**.

## 4. Configuração do Domínio (Proxy)
1. No recurso criado, localize o serviço **api**.
2. No campo **Domains**, insira: `https://api.remunedata.com.br`.
3. Certifique-se de que a porta configurada no Coolify para este domínio é a **8000**.

## 5. Healthchecks
O Coolify v4.0.0-beta.463 lerá automaticamente os healthchecks do `docker-compose.prod.yml`.
- Verifique se o status dos containers `db`, `redis` e `api` mudam para `Healthy` após o boot.

## 6. Ativação do Deploy Automático
1. Vá na aba **Configuration** do recurso.
2. Localize a seção **Webhooks**.
3. Copie a **Deploy Webhook** URL.
4. Salve esta URL no GitHub Secrets como `COOLIFY_WEBHOOK`.

---

## checklist Operacional
- [ ] Banco de dados (`db`) está Healthy?
- [ ] Redis (`redis`) está Healthy?
- [ ] Migration (`migrate`) finalizou com sucesso?
- [ ] API (`api`) está Healthy?
- [ ] Dashboard está acessível em `https://api.remunedata.com.br/dashboard`?
- [ ] Swagger está acessível em `https://api.remunedata.com.br/docs`?

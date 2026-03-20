# GitHub Actions & Coolify Integration

Esta documentação explica como o pipeline de CI/CD interage com o Coolify v4.0.0-beta.463.

## Fluxo de Deploy
1. **Push na `main`**: Dispara o workflow `CD Main`.
2. **Lint & Tests**: Valida a qualidade do código e integridade da base.
3. **Docker Build & Push**:
   - Constrói a imagem de produção.
   - Gera tags: `latest` e o `SHA` do commit.
   - Faz o push para o **GitHub Container Registry (GHCR)**.
412. **Trigger API (Coolify)**:
   - O GitHub Action chama a API oficial do Coolify (`/api/v1/deploy`).
   - O Coolify inicia o pull das imagens e o rollout da stack de forma assíncrona.

## Configuração Necessária no GitHub

Para que o deploy funcione, os seguintes segredos devem ser configurados em `Settings > Secrets and variables > Actions`:

| Secret | Descrição | Origem no Coolify |
| :--- | :--- | :--- |
| `COOLIFY_API_TOKEN` | Token de acesso à API. | Keys & Tokens > API Tokens |
| `COOLIFY_INSTANCE_URL` | URL do painel (ex: `http://IP:8000`). | URL do Painel |
| `COOLIFY_RESOURCE_UUID` | Identificador único do recurso. | URL do Recurso (parte final) |

## Configuração no Coolify

### 1. Registry
Certifique-se de que o Coolify possui as credenciais do GHCR configuradas:
- `Server > Private Registries`
- Registry URL: `https://ghcr.io`
- Username: Seu usuário GitHub
- Password: Um **Personal Access Token (PAT)** com permissão `read:packages`.

### 2. Resource Stack
O recurso no Coolify deve ser do tipo **Docker Compose** (ou Stack).
- O campo `Docker Compose` deve apontar para o arquivo `docker-compose.prod.yml` no repositório.

## Monitoramento
Você pode acompanhar o status do deploy:
1. No GitHub: Aba `Actions` do repositório.
2. No Coolify: Aba `Deployments` do recurso.

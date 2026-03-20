# Rollback and Troubleshooting Guide

## 1. Procedimento de Rollback

Se o deploy da `main` quebrar a produção:

### Opção A: Reverter via GitHub (Recomendado)
1. Faça um `git revert` do commit problemático na branch `main`.
2. Faça o push. O CI/CD gerará uma nova imagem e disparará o deploy da versão estável anterior.

### Opção B: Rollback via Coolify
1. No Coolify, vá em `Deployments`.
2. Localize um deployment anterior que estava funcional (selo verde).
3. Clique em **Redeploy** naquela versão específica.

---

## 2. Troubleshooting Comum

### A API não sobe e fica em "Starting" ou "Restarting"
- **Provável causa**: Falha na conexão com o banco ou migração pendente.
- **O que fazer**: 
  - Verifique os logs do container `migrate`. Se ele falhou, a API não subirá (devido ao `depends_on`).
  - Verifique se as variáveis `DATABASE_URL` e `DATABASE_URL_SYNC` estão corretas.

### Erro: "Temporary failure in name resolution"
- **Provável causa**: O container tentou acessar `db` antes da rede Docker estar pronta.
- **O que fazer**: O `entrypoint.sh` já possui um loop de retry. Se persistir, verifique se o serviço `db` no compose foi renomeado corretamente para `db`.

### Celery Worker não processa tarefas
- **Provável causa**: Falha na conexão com o Redis.
- **O que fazer**: 
  - Verifique se o `redis` está `Healthy`.
  - Verifique se a `REDIS_PASSWORD` e `REDIS_URL` coincidem.

### Erro de Permissão no GHCR
- **Provável causa**: PAT expirado ou sem permissão `read:packages`.
- **O que fazer**: Atualize o token em `Server > Private Registries` no Coolify.

---

## 3. Logs Úteis
- Ver logs da Stack inteira: No Coolify, na página da Stack, clique em **Logs**.
- Ver logs de um serviço específico: Clique no nome do serviço (ex: `worker`) e depois em **Logs**.

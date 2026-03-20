# Production Deploy Runbook

Este documento consolida o procedimento para deploy e manutenção da API em produção.

## 1. Fluxo de Deploy (Automático)
O deploy é disparado automaticamente a cada push na branch `main`.
1. Aguarde a conclusão do workflow **CD Main** no GitHub.
2. Verifique o status no Coolify em `Resources > RemuneData Stack > Deployments`.

## 2. Deploy Manual (Emergência)
Caso o CI/CD falhe e você precise forçar um deploy:
1. No Coolify, acesse o Recurso.
2. Clique em **Deploy** no canto superior direito.
3. Escolha **Force Redeploy** se precisar baixar a imagem `latest` novamente sem alteração de código.

## 3. Verificação Pós-Deploy (Checklist)
Após o status ficar `Running` no Coolify:
1. **Health**: Verifique se todos os serviços (`api`, `worker`, `db`, `redis`) estão com o selo verde `Healthy`.
2. **Logs**: Clique no serviço `api` e veja os logs. Procure por "Application startup complete".
3. **Migration**: Verifique se o container `migrate` terminou com `Exit Code 0`.
4. **Smoke Test**:
   ```bash
   curl -I https://api.remunedata.com.br/health
   # Deve retornar HTTP 200 OK
   ```

## 4. Manutenção de Banco de Dados
As migrations são automáticas. Se precisar rodar um comando manual no banco:
1. No Coolify, vá em `db > Terminal`.
2. Execute: `psql -U remunedata_admin -d remunedata_prod`.

## 5. Limpeza de Volumes
Os volumes `postgres_data` e `redis_data` são persistentes. Eles **não** são apagados em novos deploys, a menos que você delete o recurso e marque a opção para remover volumes.

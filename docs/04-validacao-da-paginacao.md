# 04 - Validação da paginação

## Objetivo
Validar se o parâmetro `page` altera corretamente o lote retornado pela API de remuneração.

## Consulta base
- `anoExercicio`: `2025`
- `mesReferencia`: `06`
- `size`: `5`
- `nomeServidor`: vazio

## Teste 1 - página 0
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=`
- Status code: `200`
- pageNumber retornado: não validado explicitamente no corpo
- numberOfElements: não validado explicitamente no corpo
- totalPages: não validado explicitamente no corpo
- totalElements: não validado explicitamente no corpo
- primeiro `codigoIdentificacao`: `37412615`
- primeiro `nomeServidor`: `ADILA DE JESUS VIEIRA`
- observações: a API respondeu corretamente com dados na página inicial.

## Teste 2 - página 1
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=1&size=5&nomeServidor=`
- Status code: `200`
- pageNumber retornado: não validado explicitamente no corpo
- numberOfElements: não validado explicitamente no corpo
- totalPages: não validado explicitamente no corpo
- totalElements: não validado explicitamente no corpo
- primeiro `codigoIdentificacao`: `37396194`
- primeiro `nomeServidor`: `ALISSON ALAZAFE SILVA BATISTA DE MORAES`
- observações: o primeiro registro retornado mudou em relação à página 0, indicando mudança real de lote.

## Teste 3 - página 2
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=2&size=5&nomeServidor=`
- Status code: `200`
- pageNumber retornado: não validado explicitamente no corpo
- numberOfElements: não validado explicitamente no corpo
- totalPages: não validado explicitamente no corpo
- totalElements: não validado explicitamente no corpo
- primeiro `codigoIdentificacao`: `37406776`
- primeiro `nomeServidor`: `ANA PAULA PEREIRA SANTOS`
- observações: o primeiro registro retornado mudou novamente, reforçando que a paginação está funcionando.

## Teste 4 - repetição da página 2
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=2&size=5&nomeServidor=`
- Status code: `200`
- primeiro `codigoIdentificacao`: `37406776`
- primeiro `nomeServidor`: `ANA PAULA PEREIRA SANTOS`
- observações: a repetição da mesma página retornou o mesmo primeiro registro, indicando consistência no resultado da paginação.

## Conclusão
A API respondeu corretamente a páginas diferentes, alterando os registros retornados entre `page=0`, `page=1` e `page=2`. Além disso, ao repetir `page=2`, o primeiro registro permaneceu igual, o que indica consistência. Com isso, a paginação pode ser considerada validada em nível básico.

## Limitações desta validação
- Os metadados como `pageNumber`, `numberOfElements`, `totalPages` e `totalElements` não foram extraídos explicitamente do corpo JSON nesta etapa.
- A validação foi feita com base na mudança dos registros retornados entre páginas.
- Em uma etapa futura, vale validar os metadados diretamente no JSON da resposta.

## Dúvidas em aberto
- Confirmar explicitamente no corpo JSON os campos `pageNumber`, `numberOfElements`, `totalPages` e `totalElements`.
- Verificar se existe ordenação padrão fixa na API.
- Validar se a paginação continua consistente em páginas mais distantes.
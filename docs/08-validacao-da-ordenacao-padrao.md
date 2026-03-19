# 08 - Validação da ordenação padrão

## Objetivo
Validar se a API retorna resultados em ordem estável ao repetir a mesma consulta.

## Consulta base
- `anoExercicio`: `2025`
- `mesReferencia`: `06`
- `size`: `10`
- `nomeServidor`: vazio

## Teste 1 - página 0, primeira execução
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=10&nomeServidor=`
- Status code: `200`
- Evidência observada: `RawContentLength = 10863`
- Primeiro `codigoIdentificacao`: `37412615`
- Primeiro `nomeServidor`: `ADILA DE JESUS VIEIRA`
- Observações: a API respondeu corretamente e retornou o mesmo primeiro registro já observado em testes anteriores para a página 0.

## Teste 2 - página 0, segunda execução
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=10&nomeServidor=`
- Status code: `200`
- Evidência observada: `RawContentLength = 10863`
- Primeiro `codigoIdentificacao`: `37412615`
- Primeiro `nomeServidor`: `ADILA DE JESUS VIEIRA`
- Observações: a repetição da mesma consulta retornou o mesmo primeiro registro e o mesmo tamanho bruto de resposta.

## Comparação da página 0
- A ordem permaneceu igual? sim
- Observações: a repetição exata da consulta para `page=0` devolveu o mesmo primeiro registro e o mesmo tamanho bruto de resposta, o que indica estabilidade básica da ordenação nessa página.

## Teste 3 - página 1, primeira execução
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=1&size=10&nomeServidor=`
- Status code: `200`
- Evidência observada: `RawContentLength = 10876`
- Primeiro `codigoIdentificacao`: `37406776`
- Primeiro `nomeServidor`: `ANA PAULA PEREIRA SANTOS`
- Observações: a API respondeu corretamente e retornou um primeiro registro diferente da página 0, como esperado para outra página.

## Teste 4 - página 1, segunda execução
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=1&size=10&nomeServidor=`
- Status code: `200`
- Evidência observada: `RawContentLength = 10876`
- Primeiro `codigoIdentificacao`: `37406776`
- Primeiro `nomeServidor`: `ANA PAULA PEREIRA SANTOS`
- Observações: a repetição da consulta para `page=1` retornou o mesmo primeiro registro e o mesmo tamanho bruto de resposta.

## Comparação da página 1
- A ordem permaneceu igual? sim
- Observações: a repetição exata da consulta para `page=1` devolveu o mesmo primeiro registro e o mesmo tamanho bruto de resposta, o que indica estabilidade básica da ordenação nessa página.

## Conclusão
As repetições da mesma consulta retornaram os mesmos registros de início nas páginas testadas, com o mesmo tamanho bruto de resposta em cada repetição. Para `page=0`, o primeiro registro permaneceu `ADILA DE JESUS VIEIRA` com `codigoIdentificacao 37412615`. Para `page=1`, o primeiro registro permaneceu `ANA PAULA PEREIRA SANTOS` com `codigoIdentificacao 37406776`. Com isso, a API pode ser considerada ordenada de forma estável em nível básico para fins de coleta paginada.

## Limitações desta validação
- Nesta etapa, a comparação foi feita com base no primeiro registro e no `RawContentLength`.
- Não foi feita extração explícita dos 3 primeiros registros completos em cada execução.
- Ainda vale validar páginas mais distantes para aumentar a confiança.

## Resultado prático para o projeto
Até nova evidência, o projeto pode assumir:
- a ordenação padrão da API é estável o suficiente para coleta paginada básica;
- repetir a mesma consulta tende a retornar o mesmo lote inicial de registros;
- o coletor pode confiar, por enquanto, na paginação sequencial da API.

## Dúvidas em aberto
- A estabilidade da ordenação se mantém em páginas mais distantes?
- Existe algum critério implícito de ordenação não documentado?
- A ordenação permanece estável em outros meses e anos?
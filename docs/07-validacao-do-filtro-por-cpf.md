# 07 - Validação do filtro por CPF

## Objetivo
Validar se a API de remuneração aceita filtro por CPF e como esse filtro se comporta.

## Consulta base
- `anoExercicio`: `2025`
- `mesReferencia`: `06`
- `page`: `0`
- `size`: `5`
- `nomeServidor`: vazio

## CPF de referência usado no teste
- valor testado: `***927115**`
- origem: CPF mascarado observado em resposta anterior

## Teste 1 - parâmetro `cpfServidor`
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=&cpfServidor=***927115**`
- Status code: `200`
- Evidência observada: `RawContentLength = 5559`
- Primeiro nome retornado: `ADILA DE JESUS VIEIRA`
- Houve redução visível no retorno? não
- Parece que o filtro foi aplicado? não
- Observações: o tamanho da resposta permaneceu igual ao da chamada sem filtro por CPF, indicando que o parâmetro provavelmente foi ignorado.

## Teste 2 - parâmetro `cpf`
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=&cpf=***927115**`
- Status code: `200`
- Evidência observada: `RawContentLength = 5559`
- Primeiro nome retornado: `ADILA DE JESUS VIEIRA`
- Houve redução visível no retorno? não
- Parece que o filtro foi aplicado? não
- Observações: o uso do parâmetro `cpf` não alterou o comportamento da resposta, o que sugere que esse nome de parâmetro não é reconhecido pela API.

## Teste 3 - CPF sem máscara
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=&cpfServidor=927115`
- Status code: `200`
- Evidência observada: `RawContentLength = 5559`
- Primeiro nome retornado: `ADILA DE JESUS VIEIRA`
- Houve redução visível no retorno? não
- Parece que o filtro foi aplicado? não
- Observações: enviar apenas a parte numérica do CPF também não alterou o retorno, reforçando que o filtro por CPF não parece estar exposto de forma funcional.

## Comparação dos resultados
- Sem filtro por CPF: `RawContentLength = 5559`
- Com `cpfServidor=***927115**`: `RawContentLength = 5559`
- Com `cpf=***927115**`: `RawContentLength = 5559`
- Com `cpfServidor=927115`: `RawContentLength = 5559`

## Conclusão
Os testes realizados não evidenciaram aplicação do filtro por CPF. Tanto o parâmetro `cpfServidor` quanto o parâmetro `cpf`, com e sem máscara, produziram exatamente o mesmo comportamento da chamada sem filtro. Com isso, a conclusão inicial é que a API não expõe filtro por CPF de forma utilizável, ou utiliza outro nome de parâmetro ainda não identificado.

## Limitações desta validação
- A análise foi feita com base no comportamento da resposta e no tamanho bruto (`RawContentLength`).
- Nesta etapa, não foi feita inspeção aprofundada do corpo JSON para comparar todos os registros item a item.
- Ainda é possível que exista outro parâmetro de CPF não identificado no front-end.

## Resultado prático para o projeto
Até nova evidência, o projeto deve assumir:
- o filtro por CPF não está disponível de forma funcional na API pública identificada;
- filtros confiáveis atualmente validados são os de competência, paginação, tamanho de página e nome do servidor.

## Dúvidas em aberto
- Existe outro nome de parâmetro para filtro por CPF no front-end original?
- O filtro por CPF pode existir apenas em outro endpoint não identificado?
- A API aceita CPF apenas em algum formato específico não testado?
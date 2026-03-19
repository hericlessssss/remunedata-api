# 06 - Validação do filtro por nome

## Objetivo
Validar se o parâmetro `nomeServidor` filtra corretamente os resultados da API e se aceita busca parcial.

## Consulta base
- `anoExercicio`: `2025`
- `mesReferencia`: `06`
- `page`: `0`
- `size`: `5`

## Teste 1 - sem filtro
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=`
- Status code: `200`
- Evidência observada: `RawContentLength = 5559`
- Primeiro nome retornado: `ADILA DE JESUS VIEIRA`
- Observações: a API respondeu normalmente sem filtro e retornou a listagem geral da página inicial.

## Teste 2 - nome completo
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=ADILA%20DE%20JESUS%20VIEIRA`
- Status code: `200`
- Evidência observada: `RawContentLength = 1303`
- Primeiro nome retornado: `ADILA DE JESUS VIEIRA`
- Filtrou corretamente? sim
- Observações: o retorno ficou muito menor do que sem filtro, indicando que a API restringiu corretamente os resultados ao nome informado.

## Teste 3 - busca parcial
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=ADILA`
- Status code: `200`
- Evidência observada: `RawContentLength = 5362`
- Primeiro nome retornado: `ADILA DE JESUS VIEIRA`
- Aceitou busca parcial? sim
- Observações: a API respondeu normalmente e retornou resultados compatíveis com busca parcial pelo início do nome.

## Teste 4 - outro trecho do nome
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=JESUS`
- Status code: `200`
- Evidência observada: `RawContentLength = 5564`
- Primeiro nome retornado: `ADILA DE JESUS VIEIRA`
- Aceitou busca parcial? sim
- Observações: a API também respondeu corretamente quando recebeu um trecho intermediário do nome, reforçando que o filtro não depende de nome completo.

## Comparação dos resultados
- Sem filtro: `RawContentLength = 5559`
- Nome completo: `RawContentLength = 1303`
- Parcial `ADILA`: `RawContentLength = 5362`
- Parcial `JESUS`: `RawContentLength = 5564`

## Conclusão
O parâmetro `nomeServidor` filtrou corretamente os resultados da API. O teste com nome completo reduziu fortemente o volume da resposta, o que indica filtragem específica. Os testes com `ADILA` e `JESUS` também retornaram sucesso e resultados compatíveis, o que valida que a API aceita busca parcial. Com isso, o filtro por nome pode ser considerado utilizável para a API do projeto.

## Limitações desta validação
- Nesta etapa, a validação foi feita principalmente com base no comportamento da resposta e no tamanho bruto (`RawContentLength`).
- Ainda vale, em uma etapa futura, contar explicitamente os itens retornados em `content`.
- Ainda vale testar variações de maiúsculas/minúsculas para verificar se a busca é case-sensitive ou não.

## Resultado prático para o projeto
Até nova evidência, o projeto pode assumir:
- o parâmetro `nomeServidor` funciona;
- o filtro aceita nome completo;
- o filtro aceita busca parcial.

## Dúvidas em aberto
- A busca é case-sensitive ou case-insensitive?
- O filtro ignora acentos ou exige correspondência exata?
- O comportamento se mantém igual para outros meses e anos?
# 10 - Validação da estratégia anual

## Objetivo
Validar se a coleta de um ano deve ser feita mês a mês, usando `mesReferencia` dentro de `anoExercicio`.

## Consulta base
- `anoExercicio`: `2025`
- `page`: `0`
- `size`: `5`
- `nomeServidor`: vazio

## Teste 1 - mês 01
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=01&page=0&size=5&nomeServidor=`
- `totalElements`: `244046`
- `totalPages`: `48810`
- primeiro `codigoIdentificacao`: `34576835`
- primeiro `nomeServidor`: `ADILA DE JESUS VIEIRA`
- observações: a API respondeu corretamente para janeiro de 2025, com um universo próprio de registros e paginação.

## Teste 2 - mês 06
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=0&size=5&nomeServidor=`
- `totalElements`: `259053`
- `totalPages`: `51811`
- primeiro `codigoIdentificacao`: `37412615`
- primeiro `nomeServidor`: `ADILA DE JESUS VIEIRA`
- observações: a API respondeu corretamente para junho de 2025, com total de registros maior do que em janeiro e com `codigoIdentificacao` diferente para o primeiro item.

## Teste 3 - mês 12
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=12&page=0&size=5&nomeServidor=`
- `totalElements`: `261503`
- `totalPages`: `52301`
- primeiro `codigoIdentificacao`: `40306112`
- primeiro `nomeServidor`: `ADILA DE JESUS VIEIRA`
- observações: a API respondeu corretamente para dezembro de 2025, com total ainda maior e novo `codigoIdentificacao` para o primeiro item.

## Comparação entre os meses
- os totais mudaram? sim
- os primeiros registros mudaram? parcialmente
- a API se comporta como base mensal? sim

## Evidências observadas
- Janeiro/2025: `244046` registros
- Junho/2025: `259053` registros
- Dezembro/2025: `261503` registros

## Interpretação
Os três meses testados dentro do mesmo `anoExercicio` retornaram universos diferentes de dados, com variação em:
- `totalElements`
- `totalPages`
- `codigoIdentificacao` do primeiro item

Embora o primeiro `nomeServidor` tenha permanecido como `ADILA DE JESUS VIEIRA`, o identificador associado mudou entre as competências, o que reforça que a consulta representa recortes mensais independentes.

## Conclusão
A API retorna conjuntos diferentes por `mesReferencia`, mesmo dentro do mesmo `anoExercicio`. Isso indica que o conceito de “coletar um ano” deve ser implementado como iteração mês a mês, de `01` a `12`, acumulando os resultados de cada competência.

## Resultado prático para o projeto
Até nova evidência, o projeto deve assumir:
- a coleta anual não é uma consulta única;
- a coleta anual deve iterar as 12 competências do ano;
- cada competência mensal precisa ser tratada como uma execução lógica de coleta dentro do ano solicitado.

## Dúvidas em aberto
- O comportamento é igual para todos os meses intermediários não testados?
- O mesmo padrão se repete em outros anos além de 2025?
- A mudança de `codigoIdentificacao` ao longo dos meses representa recálculo mensal ou nova chave por competência?
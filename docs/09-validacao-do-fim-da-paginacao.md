# 09 - Validação do fim da paginação

## Objetivo
Validar como a API se comporta na última página válida e em uma página além do limite.

## Consulta base
- `anoExercicio`: `2025`
- `mesReferencia`: `06`
- `size`: `10`
- `nomeServidor`: vazio

## Descoberta inicial
- `totalPages`: `25906`
- `number` da primeira consulta: `0`
- `last` da primeira consulta: `False`
- `totalElements`: `259053`
- `numberOfElements`: `10`

## Regra derivada
- última página válida: `25905`
- primeira página fora do limite: `25906`

## Teste 1 - última página válida
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=25905&size=10&nomeServidor=`
- Status code: `200`
- Veio `content`? sim
- Quantidade de itens: `3`
- `number` retornado: `25905`
- `last` retornado: `True`
- `numberOfElements`: `3`
- Observações: a última página válida retornou dados normalmente, mas com quantidade menor que o tamanho solicitado da página, o que é esperado para o fim da paginação.

## Teste 2 - página além do limite
- URL: `https://www.transparencia.df.gov.br/api/remuneracao?anoExercicio=2025&mesReferencia=06&page=25906&size=10&nomeServidor=`
- Status code: `200`
- Veio `content`? sim
- Quantidade de itens: `0`
- `number` retornado: `25906`
- `numberOfElements`: `0`
- `last` retornado: `True`
- Observações: a API não gerou erro ao receber uma página além do limite. Em vez disso, retornou resposta vazia com `200 OK`, mantendo o indicador `last=True`.

## Comparação do comportamento
- Última página válida (`25905`): retornou `3` registros e `last=True`
- Página além do limite (`25906`): retornou `0` registros e `last=True`

## Conclusão
A API trata corretamente o fim da paginação. A última página válida retorna os registros restantes e marca `last=True`. Uma página além do limite continua respondendo com `200 OK`, porém com `content` vazio e `numberOfElements=0`. Com isso, o coletor pode parar de forma confiável quando encontrar qualquer uma destas condições:

- `last = True`
- `numberOfElements = 0`
- `content.Count = 0`

## Limitações desta validação
- Esta validação foi feita para a competência `06/2025`.
- Ainda vale confirmar se o mesmo comportamento se mantém em outros meses e anos.
- Não foi testado o comportamento com outros valores de `size`.

## Resultado prático para o projeto
Até nova evidência, o projeto pode assumir:
- a paginação termina de forma previsível;
- não é necessário depender de erro HTTP para detectar o fim;
- o coletor deve encerrar o loop quando encontrar `last=True` ou resposta vazia.

## Dúvidas em aberto
- O comportamento é idêntico para outras competências?
- O comportamento permanece igual usando `size=150`?
- Há alguma diferença quando filtros por nome estão ativos?
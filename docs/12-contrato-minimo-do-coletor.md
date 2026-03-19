# 12 - Contrato mínimo do coletor

## Objetivo
Definir a entrada e a saída mínimas do coletor antes da implementação em código.

## Entrada mínima
A entrada mínima do coletor deve conter:

- `anoExercicio` (obrigatório)

Campos que podem existir no futuro:
- `mesReferencia` (para coleta isolada de um único mês)
- `nomeServidor` (para testes ou coletas filtradas)

## Exemplo de entrada
{
  "anoExercicio": 2025
}

## Saída mínima da execução anual
Ao final de uma execução anual, o coletor deve retornar pelo menos:

- `anoExercicio`
- `status`
- `startedAt`
- `finishedAt`
- `durationMs`
- `totalMesesProcessados`
- `totalPaginasConsumidas`
- `totalRegistrosColetados`
- `competencias`

## Saída mínima por competência mensal
Cada item de competência mensal deve conter pelo menos:

- `mesReferencia`
- `status`
- `paginasConsumidas`
- `registrosColetados`
- `totalPagesInformado`
- `totalElementsInformado`

## Exemplo de saída
{
  "anoExercicio": 2025,
  "status": "success",
  "startedAt": "2026-03-18T10:00:00Z",
  "finishedAt": "2026-03-18T10:45:00Z",
  "durationMs": 2700000,
  "totalMesesProcessados": 12,
  "totalPaginasConsumidas": 12345,
  "totalRegistrosColetados": 3000000,
  "competencias": [
    {
      "mesReferencia": "01",
      "status": "success",
      "paginasConsumidas": 48810,
      "registrosColetados": 244046,
      "totalPagesInformado": 48810,
      "totalElementsInformado": 244046
    }
  ]
}

## Erros mínimos que o coletor deve representar
O coletor deve conseguir representar ao menos estes cenários:

- falha de rede
- timeout
- resposta não-JSON
- JSON inválido
- estrutura inesperada da resposta
- erro ao processar uma página
- erro ao processar uma competência mensal

## Regras de status
Sugestão inicial de status:

- `success`
- `partial_success`
- `error`

## Conclusão
Com este contrato mínimo, a implementação do coletor já pode começar com uma interface clara de entrada e saída.
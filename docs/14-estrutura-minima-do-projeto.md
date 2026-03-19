# 14 - Estrutura mínima do projeto

## Objetivo
Definir uma estrutura mínima e organizada para o projeto antes do início da implementação.

## Estrutura proposta

- `app/`
- `app/core/`
- `app/collector/`
- `app/infra/`
- `app/persistence/`
- `app/api/`
- `app/workers/`
- `tests/`
- `docs/`

## Responsabilidades

### `app/`
Ponto central da aplicação.

### `app/core/`
Responsável por configurações, constantes, utilitários compartilhados e elementos centrais da aplicação.

### `app/collector/`
Responsável pela regra de negócio da coleta:
- execução anual
- execução mensal
- paginação
- condição de parada

### `app/infra/`
Responsável pela comunicação com sistemas externos, especialmente a API do Portal da Transparência.

### `app/persistence/`
Responsável pela persistência de dados:
- modelos
- sessão de banco
- repositórios
- operações de escrita e leitura

### `app/api/`
Reservado para os endpoints futuros da aplicação.

### `app/workers/`
Reservado para execução assíncrona e processamento em background no futuro.

### `tests/`
Responsável pelos testes automatizados do projeto.

### `docs/`
Responsável pela documentação funcional e técnica do projeto.

## Estrutura inicial de arquivos sugerida

- `app/main.py`
- `app/core/config.py`
- `app/infra/transparencia_client.py`
- `app/collector/run_collection.py`
- `app/collector/month_collection.py`
- `app/persistence/models.py`
- `app/persistence/repositories.py`

## Regras de organização
- a regra de negócio da coleta não deve ficar misturada com detalhes de HTTP
- a regra de negócio da coleta não deve ficar misturada com detalhes de banco de dados
- o cliente da API externa deve ficar isolado em `infra`
- a persistência deve ficar isolada em `persistence`
- a orquestração da coleta deve acontecer em `collector`
- a documentação deve continuar sendo mantida em `docs`

## Observações
- a estrutura deve priorizar clareza e facilidade de manutenção
- a primeira versão não precisa de divisão excessiva
- a separação inicial deve evitar acoplamento desnecessário

## Conclusão
Com essa estrutura mínima, o projeto já pode começar a implementação com separação básica de responsabilidades e menor risco de desorganização.
# df-remuneration-collector Makefile
# Comandos para facilitar o desenvolvimento local com Docker

.PHONY: help up down build restart test migrate logs shell clean status

help:
	@echo "Comandos disponiveis:"
	@echo "  make up       - Sobe todos os servicos (detached)"
	@echo "  make down     - Para todos os servicos"
	@echo "  make build    - Build/Rebuild das imagens"
	@echo "  make restart  - Restart dos servicos"
	@echo "  make test     - Executa a suite de testes completa"
	@echo "  make migrate  - Aplica as migrations do banco de dados"
	@echo "  make logs     - Visualiza logs de todos os servicos (follow)"
	@echo "  make shell    - Abre um terminal bash no container da app"
	@echo "  make clean    - Para servicos e remove volumes (Alerta: apaga o banco!)"
	@echo "  make status   - Verifica o status dos containers"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart

test:
	docker compose run --rm -e PYTHONPATH=. app pytest tests/ -v --tb=short

migrate:
	docker compose run --rm -e PYTHONPATH=. app alembic upgrade head

logs:
	docker compose logs -f

shell:
	docker compose run --rm app bash

clean:
	docker compose down -v

status:
	docker compose ps

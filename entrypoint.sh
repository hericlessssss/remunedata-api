#!/bin/bash
set -e

# Esperar o banco de dados estar pronto (opcional, mas recomendado se não houver healthcheck externo)
# echo "Waiting for database..."
# sleep 5 

echo "Running migrations..."
PYTHONPATH=. alembic upgrade head

echo "Starting application..."
# Usar exec para que o processo do app receba sinais do Docker (SIGTERM, etc.)
exec "$@"

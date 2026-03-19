#!/bin/bash
set -e

# Esperar o banco de dados estar resolvível e pronto (DNS fix para Coolify)
echo "Waiting for database host 'db-remune' with 60s timeout..."
python3 -c "
import socket
import time
import os

db_host = os.environ.get('DB_HOST', 'db-remune')
timeout = 60
start_time = time.time()
while time.time() - start_time < timeout:
    try:
        socket.gethostbyname(db_host)
        with socket.create_connection((db_host, 5432), timeout=2):
            print(f'Database {db_host} is up!')
            exit(0)
    except (socket.gaierror, socket.error):
        time.sleep(1)
        print('.', end='', flush=True)
print(f'\nERROR: Timeout waiting for {db_host}')
exit(1)
"

echo "Running migrations..."
PYTHONPATH=. alembic upgrade head

echo "Starting application..."
exec "$@"

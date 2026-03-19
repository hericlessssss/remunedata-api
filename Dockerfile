FROM python:3.12-slim

# Evitar geração de .pyc e garantir output não bufferizado
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar metadados primeiro (melhor cache de camadas)
COPY pyproject.toml ./
COPY README.md ./

# Instalar dependências (prod + dev para imagem única no dev)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

# Copiar código-fonte
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Criar usuário não-root para segurança
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

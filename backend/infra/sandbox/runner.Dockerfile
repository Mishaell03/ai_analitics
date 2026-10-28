FROM python:3.12-slim

# Только trusted runner содержит Docker CLI; образ ученика не меняется.
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker-cli \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir fastapi 'uvicorn[standard]' httpx python-dotenv asyncpg 'pglast>=7,<8'

WORKDIR /srv
COPY app/api/v1/schemas/exercises.py app/api/v1/schemas/exercises.py
COPY app/api/v1/schemas/sandbox.py app/api/v1/schemas/sandbox.py
COPY app/services/sandbox app/services/sandbox

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.services.sandbox.runner:create_app", "--factory", "--host", "0.0.0.0", "--port", "8090", "--workers", "1", "--limit-concurrency", "16", "--no-access-log"]

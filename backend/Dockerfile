FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN pip install --upgrade pip && pip install . \
    && chmod +x /docker-entrypoint.sh

ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    ALEMBIC_CONFIG=/app/alembic.ini

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "chatbot.presentation.api.main"]

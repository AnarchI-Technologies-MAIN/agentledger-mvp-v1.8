# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.9 AS uv
FROM python:3.14.7-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN groupadd --system agentledger \
    && useradd --system --gid agentledger --home-dir /app agentledger

WORKDIR /app
COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY manage.py ./
COPY apps ./apps
COPY collector ./collector
COPY src ./src
COPY templates ./templates
COPY static ./static

RUN chown -R agentledger:agentledger /app
USER agentledger

RUN DJANGO_SETTINGS_MODULE=agentledger.settings.production \
    DJANGO_SECRET_KEY=build-only-staticfiles-secret-with-no-runtime-authority-123456 \
    DATABASE_URL=postgresql://build:build@localhost/build \
    ALLOWED_HOSTS=localhost \
    CSRF_TRUSTED_ORIGINS=https://localhost \
    REPORTS_BUCKET_NAME=build \
    REPORTS_BUCKET_ENDPOINT=https://localhost \
    REPORTS_BUCKET_ACCESS_KEY_ID=build \
    REPORTS_BUCKET_SECRET_ACCESS_KEY=build \
    REPORT_RENDERER_URL=http://localhost \
    uv run --no-sync python manage.py collectstatic --no-input

CMD ["uv", "run", "--no-sync", "gunicorn", "--config", "src/agentledger/gunicorn.conf.py", "agentledger.wsgi:application"]

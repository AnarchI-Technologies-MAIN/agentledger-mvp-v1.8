# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.9 AS uv
FROM python:3.14.7-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN groupadd --gid 10001 agentledger \
    && useradd --uid 10001 --gid agentledger --home-dir /app --no-create-home agentledger

WORKDIR /app
RUN chown agentledger:agentledger /app
COPY --chown=agentledger:agentledger pyproject.toml uv.lock ./
USER agentledger
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/app/.cache/uv,uid=10001,gid=10001 \
    uv sync --frozen --no-default-groups --no-install-project

COPY --chown=agentledger:agentledger manage.py ./
COPY --chown=agentledger:agentledger apps ./apps
COPY --chown=agentledger:agentledger collector ./collector
COPY --chown=agentledger:agentledger src ./src
COPY --chown=agentledger:agentledger templates ./templates
COPY --chown=agentledger:agentledger static ./static

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
    .venv/bin/python manage.py collectstatic --no-input

EXPOSE 8000

CMD [".venv/bin/gunicorn", "--config", "src/agentledger/gunicorn.conf.py", "agentledger.wsgi:application"]

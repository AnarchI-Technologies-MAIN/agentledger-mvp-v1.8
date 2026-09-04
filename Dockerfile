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
COPY src ./src
COPY templates ./templates
COPY static ./static

RUN chown -R agentledger:agentledger /app
USER agentledger

CMD ["uv", "run", "--no-sync", "gunicorn", "--config", "src/agentledger/gunicorn.conf.py", "agentledger.wsgi:application"]

FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PORT=10000
EXPOSE ${PORT}

CMD uv run gunicorn --bind 0.0.0.0:${PORT} app:app

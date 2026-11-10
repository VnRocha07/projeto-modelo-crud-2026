FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /srv/api
COPY api/pyproject.toml api/uv.lock ./
RUN uv sync --frozen --no-dev

COPY api/app ./app
COPY db /srv/db
COPY web /srv/web

EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

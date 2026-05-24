FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 装依赖：用 uv 读 pyproject.toml 一把装到系统 python
COPY pyproject.toml ./
RUN uv pip install --system \
    fastapi 'uvicorn[standard]' 'sqlalchemy[asyncio]' alembic asyncpg \
    psycopg2-binary aiosqlite 'pydantic[email]' pydantic-settings \
    'python-jose[cryptography]' 'passlib[bcrypt]' bcrypt==4.0.1 \
    cryptography python-multipart loguru redis rq httpx openpyxl

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

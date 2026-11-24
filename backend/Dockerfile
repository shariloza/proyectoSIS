# Imagen única para la API y el worker (mismo código, distinto comando).
# Contexto de build: raíz del repositorio (incluye el dataset semilla).
FROM ghcr.io/astral-sh/uv:0.13.9 AS uv

FROM python:3.12.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    OPENBLAS_NUM_THREADS=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --from=uv /uv /usr/local/bin/uv

# Dependencias primero: se cachean mientras no cambie el lockfile.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY backend/src ./src
RUN uv sync --locked --no-dev

COPY data/raw/student_depression_dataset.csv /app/seed/student_depression_dataset.csv

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/artifacts \
    && chown app:app /app/artifacts
USER app

EXPOSE 8000

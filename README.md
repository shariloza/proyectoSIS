# Riesgo de depresión en estudiantes

Trabajo final de TALLERSISIA: un modelo de clasificación entrenado con CRISP-ML(Q), con una API REST y un cliente web.

> Herramienta académica de estimación de riesgo. **No es un diagnóstico.** Si estás pasando por un momento difícil, busca apoyo profesional.

## Estado

| Componente | Estado |
|---|---|
| Base de datos (PostgreSQL + Alembic) | ✅ Esquema inicial |
| Modelo de ML | ⏳ PR 2 |
| API REST | ⏳ PR 3 |
| Cliente web | ⏳ PR 4 |

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) con Docker Compose v2
- [uv](https://docs.astral.sh/uv/) (instala Python 3.12 por su cuenta) para desarrollar el backend

## Levantar el proyecto

```bash
# 1. Variables de entorno: copia la plantilla y reemplaza los valores marcados con CAMBIAR
cp .env.example .env    # PowerShell: Copy-Item .env.example .env

# 2. Base de datos
docker compose up -d db
docker compose ps          # db debe figurar como "healthy"

# 3. Backend: dependencias y migraciones
cd backend
uv sync
uv run alembic upgrade head
```

## Calidad

Desde `backend/`:

```bash
uv run ruff check .            # lint
uv run ruff format --check .   # formato
uv run mypy                    # tipos (strict)
uv run pytest                  # unitarios + integración (requiere la db levantada)
uv run pytest -m "not integration"   # solo unitarios
```

El mismo pipeline corre en GitHub Actions en cada PR hacia `dev` y `main` ([.github/workflows/ci.yml](.github/workflows/ci.yml)).

## Estructura

```text
backend/
  src/app/
    config.py              # configuración validada al iniciar (fail fast)
    shared/database.py     # Base declarativa y convenciones del esquema
    modules/<módulo>/
      domain/              # conceptos del dominio (estados, roles)
      infrastructure/      # persistencia (ORM)
  migrations/              # Alembic
  tests/ unit/ integration/
data/raw/                  # dataset semilla
docs/                      # análisis, arquitectura y base de ingeniería
```

## Flujo de trabajo

`feature/*` → PR → `dev` → PR final → `main`. Cada PR pasa por CI y por la revisión de IA (GitHub Copilot).

## Documentación

- [Análisis y arquitectura](docs/analisis-arquitectura.md)
- [Base de ingeniería](docs/base-ingenieria.md)

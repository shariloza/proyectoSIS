# Riesgo de depresión en estudiantes

Trabajo final de TALLERSISIA: un modelo de clasificación entrenado con CRISP-ML(Q), con una API REST y un cliente web.

> Herramienta académica de estimación de riesgo. **No es un diagnóstico.** Si estás pasando por un momento difícil, busca apoyo profesional.

## Estado

| Componente | Estado |
|---|---|
| Base de datos (PostgreSQL + Alembic) | ✅ |
| Modelo de ML (CRISP-ML(Q)) | ✅ v1 aprobado: ROC-AUC 0,870 |
| API REST + worker de re-entrenamiento | ✅ Swagger en `/docs` |
| Cliente web | ⏳ PR 4 |

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) con Docker Compose v2
- [uv](https://docs.astral.sh/uv/) (instala Python 3.12 por su cuenta), solo para desarrollar el backend

## Levantar el proyecto con Docker

```bash
# 1. Variables de entorno: copia la plantilla y reemplaza los valores marcados con CAMBIAR
cp .env.example .env    # PowerShell: Copy-Item .env.example .env

# 2. Todo el sistema: base de datos, API y worker
docker compose up -d --build
docker compose ps          # db, api y worker deben figurar como "healthy"
```

El primer arranque aplica las migraciones, crea el administrador (`ADMIN_EMAIL` / `ADMIN_PASSWORD`
del `.env`) y entrena el modelo inicial v1 (tarda 1-3 minutos). Después:

| Qué | URL |
|---|---|
| Swagger (documentación interactiva) | http://127.0.0.1:8000/docs |
| Contrato OpenAPI | [docs/openapi.json](docs/openapi.json) |
| Health | http://127.0.0.1:8000/api/v1/health/ready |

## Desarrollo del backend sin Docker (opcional)

```bash
docker compose up -d db
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.bootstrap --seed-dataset ../data/raw/student_depression_dataset.csv
uv run uvicorn app.main:production_app --factory --reload     # API
uv run python -m app.worker                                    # worker (otra terminal)
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
    main.py | worker.py | bootstrap.py   # puntos de entrada
    config.py              # configuración validada al iniciar (fail fast)
    api/                   # dependencias HTTP y formato único de errores
    ml/                    # contrato del dataset, preparación, entrenamiento, evaluación, artefactos
    modules/<módulo>/      # auth, prediction, model_registry, datasets, training, health
      domain/ application/ infrastructure/ presentation/
    shared/                # base de datos, errores, logs, rate limiting
  migrations/              # Alembic
  scripts/figures.py       # EDA y gráficas del documento
  tests/ unit/ ml/ integration/ api/ contract/
data/raw/                  # dataset semilla
docs/                      # análisis, base de ingeniería, OpenAPI y figuras
```

## Flujo de trabajo

`feature/*` → PR → `dev` → PR final → `main`. Cada PR pasa por CI y por la revisión de IA (GitHub Copilot).

## Documentación

- [Análisis y arquitectura](docs/analisis-arquitectura.md)
- [Base de ingeniería](docs/base-ingenieria.md)

# Despliegue

## Local con Docker Compose (método oficial)

Requisitos: Docker Desktop con Compose v2 y ~4 GB de RAM libres.

```bash
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
# Editar .env: reemplazar todos los valores CAMBIAR (contraseñas y JWT_SECRET)
docker compose up -d --build --wait
```

| Servicio | URL | Healthcheck |
|---|---|---|
| Aplicación web | http://127.0.0.1:8080 | `wget /` |
| API / Swagger | http://127.0.0.1:8000/docs | `GET /api/v1/health/ready` (BD + modelo activo) |
| PostgreSQL | `127.0.0.1:5432` | `pg_isready` |
| Worker | — | heartbeat de menos de 60 s |

El primer arranque de `api` ejecuta, en orden: `alembic upgrade head` → `python -m app.bootstrap`
(admin, dataset semilla, entrenamiento y activación de v1, de 1 a 3 minutos) → `uvicorn`. Los
siguientes arranques omiten el entrenamiento porque el bootstrap es idempotente.

### Variables de entorno

Todas están en [.env.example](../.env.example). El backend no arranca si falta una o es inválida.

| Variable | Descripción |
|---|---|
| `ENVIRONMENT`, `LOG_LEVEL` | `development`/`test`/`production`; nivel de log |
| `POSTGRES_*` | Conexión. En Docker, `POSTGRES_HOST`/`PORT` se reemplazan por `db:5432` |
| `JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_EXPIRE_MINUTES` | Tokens de administración |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Administrador inicial (lo crea el bootstrap) |
| `CORS_ORIGINS` | Lista JSON de orígenes permitidos (desarrollo con Vite) |
| `ARTIFACTS_DIRECTORY` | Modelos y datasets. En Docker: `/app/artifacts` (volumen) |
| `MAX_UPLOAD_MEGABYTES`, `TRAINING_TIMEOUT_SECONDS` | Límite de subida y timeout del re-entrenamiento |

### Operación

```bash
docker compose ps                 # estado y salud
docker compose logs -f api worker # logs JSON con request_id
docker compose down               # detener (los datos quedan en los volúmenes)
docker compose down -v            # detener y BORRAR base y artefactos
```

## Pipeline de CI (GitHub Actions)

[.github/workflows/ci.yml](../.github/workflows/ci.yml) corre en cada PR y push a `dev` y `main`:

1. **Backend:** `uv sync --locked`, ruff (lint y formato), mypy strict, `alembic upgrade head` y
   pytest contra un PostgreSQL de servicio.
2. **Frontend:** `npm ci`, tipos sincronizados con `docs/openapi.json`, ESLint, Prettier, `tsc`,
   Vitest y build.
3. **E2E:** genera un `.env` con secretos aleatorios, ejecuta `docker compose up --build --wait` y
   las pruebas de Playwright.

## Publicación en Internet (opcional, no realizada)

El proyecto está listo para Dokploy u otro host con Docker Compose:

- Poner un proxy con TLS (Traefik o Caddy) delante de `web` y no publicar `api` ni `db`.
- `ENVIRONMENT=production`, secretos nuevos y `--forwarded-allow-ips` limitado a la IP del proxy.
- Desactivar `/docs` si no se desea exponer Swagger.
- Programar `pg_dump` y el respaldo del volumen `artifacts`, y probar la restauración.

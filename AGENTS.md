# AGENTS.md

Guía para agentes de IA (y personas) que trabajen en este repositorio.

## Antes de cambiar algo
1. Leer [CLAUDE.md](CLAUDE.md) (contexto y hallazgos del dataset), [docs/base-ingenieria.md](docs/base-ingenieria.md) (estándar obligatorio) y [docs/analisis-arquitectura.md](docs/analisis-arquitectura.md) (decisiones aprobadas).
2. No cambiar la arquitectura, el esquema ni los contratos de la API sin una decisión explícita del responsable.

## Convenciones
- **Ramas:** `feature/<tema>` desde `dev`, con un PR por fase hacia `dev`. `main` solo recibe PRs desde `dev`.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `ci:`).
- **Idioma:** código e identificadores en inglés; documentación, mensajes de error al usuario y UI en español.
- **Backend:** módulos en `backend/src/app/modules/<módulo>/{domain,application,infrastructure,presentation}`. Solo se crean las capas que el módulo necesita. Sin lógica de negocio en controladores ni en repositorios.
- **Base de datos:** todo cambio de esquema se hace con una migración de Alembic revisada a mano. El test `test_migration_matches_orm_models` falla si el ORM y las migraciones divergen.
- **Configuración:** toda variable nueva se agrega a `Settings` (con validación), a `.env.example` y al bloque `env` del CI.

- **Contrato de la API:** al cambiar endpoints, regenerar `docs/openapi.json` y los tipos del
  frontend (`npm run gen:api`). El CI falla si quedan desincronizados.
- **ML:** columnas, rangos y categorías se definen solo en `backend/src/app/ml/schema.py`.
- **Documentación:** describe el sistema real. Al cambiar el comportamiento, actualizar `docs/`.

## Comandos
```bash
# backend/
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
uv run alembic revision --autogenerate -m "<descripción>"   # luego revisar el archivo generado
uv run python -m app.openapi ../docs/openapi.json            # exportar el contrato
# frontend/
npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
npm run e2e                                                  # requiere docker compose up
```

## Prohibido
- Commitear `.env`, secretos, artefactos de modelos o datasets subidos.
- Usar la columna de pensamientos suicidas como feature o guardarla.
- Marcar un test como pasado sin haberlo ejecutado. Desactivar validaciones o tests para que el CI pase.
- Imágenes Docker con la etiqueta `latest`.

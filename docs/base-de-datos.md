# Base de datos

PostgreSQL 16. Todo el esquema se crea con migraciones de Alembic
([backend/migrations](../backend/migrations)). El test `test_migration_matches_records`
garantiza que los modelos de SQLAlchemy (`records.py`) y las migraciones no divergen.

## Diagrama entidad-relación

El mismo diagrama, en formato DBML y con colores, está en [sql/diagrama.dbml](sql/diagrama.dbml).
Para obtener la imagen: copiar el archivo en [dbdiagram.io](https://dbdiagram.io) y usar
*Export → PNG* o *PDF*.

```mermaid
erDiagram
    admin_users {
        uuid id PK "gen_random_uuid()"
        varchar(254) email UK
        varchar(255) password_hash "Argon2"
        varchar(20) role "CHECK IN ('admin')"
        boolean is_active "DEFAULT true"
        timestamptz created_at "DEFAULT now()"
    }
    datasets {
        uuid id PK
        varchar(255) original_filename
        varchar(512) storage_path UK
        varchar(64) sha256 UK "CHECK length = 64"
        integer row_count "CHECK > 0"
        bigint size_bytes "CHECK > 0"
        jsonb validation_report
        uuid uploaded_by FK "NULL = dataset semilla"
        timestamptz created_at
    }
    training_jobs {
        uuid id PK
        uuid dataset_id FK
        varchar(20) status "PENDING|RUNNING|SUCCEEDED|FAILED|TIMED_OUT"
        smallint attempts "CHECK 0..3"
        text error_message
        uuid requested_by FK
        timestamptz created_at
        timestamptz started_at
        timestamptz heartbeat_at
        timestamptz finished_at
    }
    model_versions {
        uuid id PK
        varchar(20) version UK "v1, v2…"
        uuid dataset_id FK
        uuid training_job_id FK,UK "NULL = modelo inicial"
        varchar(100) algorithm
        jsonb hyperparameters
        jsonb metrics "validation y test"
        jsonb acceptance_report "criterios C1-C9"
        jsonb dependencies "versiones de librerías"
        varchar(20) preprocessing_version
        integer random_seed
        varchar(512) artifact_path UK
        varchar(64) artifact_sha256
        varchar(20) status "CANDIDATE|APPROVED|REJECTED|ACTIVE|RETIRED"
        timestamptz trained_at
        timestamptz activated_at
    }
    model_activation_events {
        bigint id PK
        uuid model_version_id FK
        uuid previous_model_version_id FK
        varchar(20) action "ACTIVATE|ROLLBACK"
        uuid performed_by FK
        timestamptz created_at
    }
    predictions {
        uuid id PK
        uuid model_version_id FK
        jsonb input_features "sin datos identificables"
        smallint predicted_class "CHECK IN (0,1)"
        numeric probability "(5,4) CHECK 0..1"
        varchar(10) risk_band "LOW|MODERATE|HIGH"
        integer latency_milliseconds "CHECK >= 0"
        timestamptz created_at
    }

    admin_users ||--o{ datasets : sube
    admin_users ||--o{ training_jobs : solicita
    admin_users ||--o{ model_activation_events : ejecuta
    datasets ||--o{ training_jobs : entrena
    datasets ||--o{ model_versions : origen
    training_jobs |o--o| model_versions : produce
    model_versions ||--o{ model_activation_events : historial
    model_versions ||--o{ predictions : genera
```

> El ERD también puede exportarse desde pgAdmin: Tools → ERD Tool sobre la base `depression_risk`.

## Restricciones e índices relevantes

| Objeto | Propósito |
|---|---|
| `uq_model_versions_single_active`: índice único parcial `WHERE status = 'ACTIVE'` | Nunca hay dos modelos activos |
| `uq_training_jobs_single_running`: índice único parcial `WHERE status = 'RUNNING'` | Un solo entrenamiento a la vez |
| `ix_training_jobs_status_created_at` | El worker toma el siguiente trabajo pendiente |
| `ix_predictions_created_at`, `ix_predictions_model_version_created_at` | Historial paginado y filtrado por versión |
| Todas las FK con `ON DELETE RESTRICT` | No se borra historial de forma implícita |
| CHECK de estados, rangos y longitudes de hash | La base valida aunque falle la aplicación |

## Script SQL

[docs/sql/schema.sql](sql/schema.sql) se genera desde las migraciones en modo offline, sin
conectarse a ninguna base:

```bash
cd backend
uv run alembic upgrade head --sql > ../docs/sql/schema.sql
```

## Procedimiento para generar la base

**Opción A, recomendada (Docker):** `docker compose up -d`. El servicio `api` ejecuta
`alembic upgrade head` antes de arrancar y luego `python -m app.bootstrap`, que crea el
administrador, registra el dataset semilla y entrena y activa el modelo v1.

**Opción B, un PostgreSQL propio con el script SQL:**

```bash
createdb -U postgres depression_risk
psql -U postgres -d depression_risk -f docs/sql/schema.sql
```

El script deja registrada la revisión `0001` en `alembic_version`, así que después se puede seguir
con Alembic normalmente.

**Opción C, Alembic directo:** con `POSTGRES_*` en `.env`, ejecutar `cd backend && uv run alembic upgrade head`.

## Retención y respaldo

- Las predicciones se conservan; la retención propuesta es de 180 días mediante una purga manual
  documentada, no automática.
- Respaldo: `docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql`.
  Restauración: `psql … < backup.sql`. Los artefactos de modelos viven en el volumen `artifacts` y
  se respaldan junto con la base.

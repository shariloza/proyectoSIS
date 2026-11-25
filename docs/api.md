# API REST

- Documento Swagger/OpenAPI 3.1: [openapi.json](openapi.json). Se regenera con
  `cd backend && uv run python -m app.openapi ../docs/openapi.json`, y un test de contrato falla si
  queda desactualizado.
- Swagger interactivo: http://127.0.0.1:8000/docs (con el sistema levantado).
- Prefijo: `/api/v1`. Formato: JSON. Autenticación de administración: `Authorization: Bearer <JWT>`.

## Endpoints

| Método | Ruta | Acceso | Respuesta |
|---|---|---|---|
| POST | `/predictions` | Público (30/min por IP) | 201 predicción + aviso |
| GET | `/predictions?page&size&model_version_id` | Admin | Página del historial |
| GET | `/models/active` | Público | Versión activa con métricas y criterios |
| GET | `/models` | Admin | Versiones registradas |
| GET | `/models/{id}` | Admin | Detalle de una versión |
| POST | `/models/{id}/activate` | Admin | Activa una versión APPROVED/RETIRED |
| POST | `/models/rollback` | Admin | Vuelve a la versión activa anterior |
| POST | `/datasets` (multipart `file`) | Admin | 201 dataset validado y versionado |
| GET | `/datasets` | Admin | Datasets subidos |
| POST | `/training-jobs` `{dataset_id}` | Admin | 202 trabajo PENDING |
| GET | `/training-jobs` | Admin | Últimos 20 trabajos |
| GET | `/training-jobs/{id}` | Admin | Estado, error y modelo resultante |
| POST | `/auth/login` | Público (5/min por IP) | JWT y su duración |
| GET | `/health/live` · `/health/ready` | Público | Liveness · BD y modelo activo |

## Ejemplo: predicción

```http
POST /api/v1/predictions
Content-Type: application/json

{
  "gender": "Female", "age": 21, "grade_point_average": 7.5,
  "academic_pressure": 4, "study_satisfaction": 2, "work_study_hours": 9,
  "financial_stress": 4, "sleep_duration": "5-6 hours", "dietary_habits": "Moderate",
  "education_level": "undergraduate", "family_history": "No"
}
```

```json
{
  "id": "05c36489-a990-410e-b543-927e504ff4ab",
  "prediction": 1,
  "probability": 0.9383,
  "risk_band": "HIGH",
  "model_version": "v1",
  "disclaimer": "Este resultado es una estimación estadística con fines académicos y NO es un diagnóstico. …",
  "created_at": "2026-11-24T20:31:59.426219Z"
}
```

| Campo | Tipo | Valores |
|---|---|---|
| `gender` | enum | `Male`, `Female` |
| `age` | int | 18–60 |
| `grade_point_average` | float | 0,01–10 |
| `academic_pressure`, `study_satisfaction`, `financial_stress` | int | 1–5 |
| `work_study_hours` | int | 0–12 |
| `sleep_duration` | enum | `Less than 5 hours`, `5-6 hours`, `7-8 hours`, `More than 8 hours` |
| `dietary_habits` | enum | `Unhealthy`, `Moderate`, `Healthy` |
| `education_level` | enum | `secondary`, `undergraduate`, `postgraduate`, `doctorate`, `other` |
| `family_history` | enum | `No`, `Yes` |

Los campos adicionales se rechazan (`extra = forbid`). Así nadie puede enviar, por ejemplo, la
pregunta sobre pensamientos suicidas.

## Errores

Todas las respuestas de error usan el mismo formato:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Los datos enviados no son válidos.",
    "details": [{ "field": "age", "message": "Input should be greater than or equal to 18" }],
    "request_id": "f4775c86d97541758730f5fa441c596b"
  }
}
```

| HTTP | `code` | Cuándo |
|---|---|---|
| 401 | `UNAUTHORIZED` | Sin token, token inválido o expirado, credenciales incorrectas |
| 403 | `FORBIDDEN` | Token válido sin rol de administrador |
| 404 | `NOT_FOUND` | Recurso inexistente o sin modelo activo |
| 409 | `CONFLICT` | Dataset duplicado, re-entrenamiento en curso, activación no permitida |
| 413 | `PAYLOAD_TOO_LARGE` | Archivo mayor que `MAX_UPLOAD_MEGABYTES` |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | El archivo no es CSV |
| 422 | `VALIDATION_ERROR` | Entrada o dataset inválidos (`details` lista cada problema) |
| 429 | `RATE_LIMITED` | Límite de solicitudes superado |
| 503 | `SERVICE_UNAVAILABLE` | Sin modelo activo cargable o base de datos caída |
| 500 | `INTERNAL_ERROR` | Error no controlado; queda en el log con su `request_id` |

Cada respuesta incluye la cabecera `X-Request-ID`, que también aparece en los logs.

# Testing

Todas las cifras de esta página corresponden a ejecuciones reales del 23 al 25/11/2026.

| Suite | Herramienta | Tests | Contra | Comando |
|---|---|---|---|---|
| Unitarias + contrato | pytest | 30 + 4 | — | `uv run pytest tests/unit tests/contract` |
| ML | pytest | 25 | dataset real | `uv run pytest tests/machine_learning` |
| Integración + API | pytest + TestClient | 8 + 32 | **PostgreSQL real** (base temporal por suite) | `uv run pytest tests/integration tests/api` |
| **Total backend** | | **99** | | `uv run pytest` (≈ 4 min) |
| Frontend | Vitest + Testing Library | 11 | jsdom | `npm test` |
| End-to-end | Playwright (Chromium) | 8 | **sistema completo en Docker** | `npm run e2e` (≈ 2–5 min) |

## Qué se prueba

**Unitarias.** Configuración fail fast (variables faltantes o inválidas), bandas de riesgo,
transiciones de estado de los modelos, rate limiting, hash de contraseñas y JWT (firma, issuer,
audience y expiración). Que cada punto de entrada registre todas las tablas (regresión).

**ML.** Contrato del dataset (columnas faltantes, objetivo no binario, tipos, tamaño mínimo,
exceso de filas sucias y reporte de todos los problemas juntos), exclusión de la variable de
pensamientos suicidas, agrupación del título, preprocesamiento sin NaN y sin leakage (el escalado
se ajusta solo con los datos de entrenamiento), split estratificado y disjunto, reproducibilidad
con semilla fija, selección que nunca elige el Dummy, criterios de aceptación y C9, artefacto
(metadatos de la sección 6.2, ida y vuelta idéntica, inmutabilidad, detección de manipulación y de
versiones incompatibles).

**Integración y API (PostgreSQL real).** Migración y su reversión, coincidencia ORM y migraciones,
índices únicos parciales, CHECK y FK RESTRICT. Predicción guardada con su versión, 422 por campo,
campos extra rechazados, permisos (401 sin token o con token falsificado), paginación, login con
mensaje genérico, readiness, `X-Request-ID`, CORS, 404 con formato. Datasets: aceptado y
versionado, duplicado (409), columnas faltantes, no CSV (415), demasiado grande (413), ilegible.
**Ciclo de re-entrenamiento con el worker real:** el candidato no se activa solo, 409 ante un
segundo trabajo, C9 presente, activación, 409 al reactivar, rollback, un modelo rechazado no se
activa, un entrenamiento fallido deja el modelo activo intacto y el timeout se respeta. Todas las
rutas de administración exigen token.

**Contrato.** `docs/openapi.json` igual a la API real, operaciones requeridas presentes, errores
4xx y 5xx documentados con `ErrorResponse` y enums de categorías publicados. En el frontend, el CI
regenera `schema.d.ts` y falla si cambió.

**E2E.** Evaluación completa con el aviso, datos fuera de rango rechazados por la API aunque se
quite la validación del navegador, métricas públicas, pantallas de administración bloqueadas (UI y
API), contraseña incorrecta, historial con datos, resultado y versión, dataset inválido explicado y
ciclo completo subir → re-entrenar → comparar → activar → rollback.

## Bugs encontrados y su prueba de regresión

| Bug | Prueba |
|---|---|
| El worker no arrancaba: no registraba la tabla `admin_users` (FK sin resolver) | `tests/unit/test_entrypoints.py` (falla sin la corrección) |
| La subida leía el archivo completo antes de validar el tamaño | `test_oversized_file_is_rejected` |
| Open redirect después del login | `src/lib/safe-redirect.test.ts` |
| Sin memoria al entrenar con `n_jobs=-1` en una máquina de 6 GB | Suite completa (99 tests) estable con paralelismo acotado |
| Las gráficas se capturaban a mitad de su animación y desbordaban sus tarjetas | Capturas de las E2E |

## Limitaciones de las pruebas

- Las E2E dependen del entrenamiento real y tardan de 2 a 5 minutos según la máquina.
- Si el candidato del ciclo E2E no cumple los criterios, la prueba verifica que **no** pueda
  activarse en lugar de activar y hacer rollback. Ambos caminos son correctos.
- No hay pruebas de carga ni de concurrencia con varios workers.

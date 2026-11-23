# CLAUDE.md — Contexto del proyecto

## Qué es
Trabajo final de TALLERSISIA (Católica, semestre 2-2026): un sistema de **estimación de riesgo de depresión en estudiantes** formado por
- un modelo de clasificación binaria entrenado con CRISP-ML(Q),
- una API REST (FastAPI) con predicción, historial, métricas, subida del dataset y re-entrenamiento,
- un cliente web (React + Vite + TypeScript) que consume todos los endpoints.

El sistema **no es una herramienta de diagnóstico**. Toda salida dirigida al usuario lleva un aviso y una sugerencia de buscar apoyo profesional.

## Documentos que mandan
- `docs/base-ingenieria.md` es el estándar obligatorio de arquitectura, seguridad, ML y testing.
- `docs/analisis-arquitectura.md` contiene las decisiones aprobadas de la Fase 1 (arquitectura, BD, ciclo de vida del modelo, plan de PRs y cronograma).

## Dataset
`data/raw/student_depression_dataset.csv` (Kaggle "Student Depression Dataset")
- 27 901 filas y 18 columnas, objetivo `Depression` (1 = 58,55 %, 0 = 41,45 %), desbalance moderado
- SHA-256: `c867f72c4dd25a0e1b08ab809cf971baad76984daf0547c4d367f5ad162495e1`

### Hallazgos de calidad (verificados con pandas)
| # | Columna | Hallazgo | Tratamiento previsto |
|---|---------|----------|----------------------|
| 1 | `Have you ever had suicidal thoughts ?` | Muy correlacionada con el objetivo (79 % de depresión con "Yes" frente a 23 % con "No"). Es un dato extremadamente sensible y su uso es éticamente cuestionable | **Se excluye del modelo**. No se pide en el formulario ni se guarda |
| 2 | `Financial Stress` | 3 valores nulos | Imputar con la mediana dentro del Pipeline |
| 3 | `Profession` | 27 870 de 27 901 filas son "Student" (99,9 %) | Se descarta por varianza casi nula |
| 4 | `Work Pressure` | 27 898 filas valen 0 | Se descarta |
| 5 | `Job Satisfaction` | 27 893 filas valen 0 | Se descarta |
| 6 | `City` | 52 valores, de los cuales unos 22 son basura (nombres de persona como "Saanvi", "3.0", "M.Tech", "City", "Less Delhi") | Se descarta (alta cardinalidad, ruido y riesgo de sesgo geográfico) |
| 7 | `Sleep Duration` | Categoría "Others" con 18 filas | Se elimina la fila en entrenamiento; la API acepta solo las 4 categorías válidas, codificadas como ordinales |
| 8 | `Dietary Habits` | Categoría "Others" con 12 filas | Igual que el anterior |
| 9 | `Degree` | 28 valores, uno de ellos "Others" (35) | Se agrupa en nivel educativo (Secundaria, Pregrado, Posgrado, Doctorado, Otro) |
| 10 | `Academic Pressure` / `Study Satisfaction` | Valor 0 fuera de la escala 1–5 (9 y 10 filas) | Se eliminan esas filas en entrenamiento; la API valida 1–5 |
| 11 | `CGPA` | 9 filas con CGPA = 0 | Se eliminan (valor imposible para un estudiante activo) |
| 12 | `Age` | Rango 18–59, con 19 filas mayores de 40 | Se conservan; la API valida 18–60 |
| 13 | `id` | Identificador sin valor predictivo | Se descarta |
| — | General | Sin duplicados (ni por fila ni excluyendo `id`) | — |

## Reglas para el agente
- Seguir `docs/base-ingenieria.md` (sección 14). No improvisar arquitectura ni avanzar de fase sin aprobación del usuario.
- Flujo git: `main` ← `dev` ← `feature/*`. Un PR por fase hacia `dev`, y al final `dev` → `main`.
- Nunca commitear `.env`, secretos ni artefactos pesados sin decisión explícita.
- Nunca afirmar que un test pasó si no se ejecutó.
- Idioma: documentación y textos de la UI en español; código e identificadores en inglés.

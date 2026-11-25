# Datasets

## Dataset semilla

| Atributo | Valor |
|---|---|
| Fuente | Kaggle, "Student Depression Dataset" (encuesta a estudiantes de la India) |
| Archivo | [data/raw/student_depression_dataset.csv](../data/raw/student_depression_dataset.csv) |
| SHA-256 | `c867f72c4dd25a0e1b08ab809cf971baad76984daf0547c4d367f5ad162495e1` |
| Tamaño | 27 901 filas × 18 columnas (2,8 MB) |
| Objetivo | `Depression` (1 = 58,55 %, 0 = 41,45 %) |
| Duplicados | Ninguno |

El EDA es reproducible con `backend/scripts/figures.py` y genera las figuras de
[docs/figuras](figuras).

## Contrato (lo que se acepta para entrenar)

Definido en un único lugar: [backend/src/app/machine_learning/schema.py](../backend/src/app/machine_learning/schema.py).

| Columna original | Feature | Tipo | Dominio aceptado |
|---|---|---|---|
| `Gender` | `gender` | categórica | Male, Female |
| `Age` | `age` | numérica | 18–60 |
| `CGPA` | `grade_point_average` | numérica | 0,01–10 |
| `Academic Pressure` | `academic_pressure` | numérica | 1–5 |
| `Study Satisfaction` | `study_satisfaction` | numérica | 1–5 |
| `Work/Study Hours` | `work_study_hours` | numérica | 0–12 |
| `Financial Stress` | `financial_stress` | numérica | 1–5 (nulos imputados con la mediana) |
| `Sleep Duration` | `sleep_duration` | ordinal | 4 categorías (sin "Others") |
| `Dietary Habits` | `dietary_habits` | ordinal | Unhealthy, Moderate, Healthy |
| `Degree` | `education_level` | categórica | 28 títulos agrupados en 5 niveles |
| `Family History of Mental Illness` | `family_history` | binaria | No, Yes |
| `Depression` | objetivo | binaria | 0, 1 (sin vacíos) |

## Tratamiento de cada hallazgo de calidad

| Hallazgo | Decisión | Justificación |
|---|---|---|
| `Have you ever had suicidal thoughts ?` | **Excluida** | Altamente predictiva (79 % frente a 23 % de depresión), pero extremadamente sensible: pedirla en un formulario público no es ético y el modelo se apoyaría en ella |
| `Profession` (99,9 % "Student"), `Work Pressure` y `Job Satisfaction` (≈ 100 % en 0) | Excluidas | Varianza casi nula |
| `City` (52 valores, unos 22 basura) | Excluida | Ruido, alta cardinalidad y riesgo de sesgo geográfico |
| `id` | Excluida | Sin valor predictivo |
| `Degree` (28 valores) | Agrupada en secundaria, pregrado, posgrado, doctorado y otro | Muchos títulos con pocos casos generalizan mal |
| "Others" en sueño (18) y en alimentación (12) | Fila descartada | Categoría ambigua, imposible de pedir en el formulario |
| 0 en escalas 1–5 (presión 9, satisfacción 10) | Fila descartada | Fuera de la escala |
| CGPA = 0 (9) | Fila descartada | Imposible para un estudiante activo |
| `Financial Stress` nulo (3) | Imputado con la mediana **dentro del Pipeline** | Sin leakage: la mediana se calcula solo con train |
| Edades de 40 a 59 (19) | Conservadas | Valores posibles; la API valida 18–60 |

Resultado real: 27 901 filas → **27 857 utilizables** (44 descartadas), con el detalle por motivo
en el `validation_report` del dataset.

## Datasets subidos por administración

- Mismas columnas que el original; las columnas extra se ignoran y se reportan las excluidas.
- Se rechaza si falta una columna, si el objetivo no es 0/1 o tiene vacíos, si una columna numérica
  no lo es, si tiene menos de 500 filas o si más del 5 % de las filas cae fuera de dominio.
- Se guarda como `artifacts/datasets/<sha256>.csv`, inmutable. Un archivo idéntico se rechaza (409).
- Se registra en la tabla `datasets` con su hash, filas, tamaño y reporte de validación.

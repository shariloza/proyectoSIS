# Model card: estimador de riesgo de depresión estudiantil v1

| | |
|---|---|
| Versión | v1 (activo) · entrenado el 23/11/2026 |
| Algoritmo | Regresión logística (`C = 0.1`, `max_iter = 2000`) dentro de un Pipeline de scikit-learn 1.7.2 |
| Entrada | 11 variables: género, edad, promedio, presión académica, satisfacción con los estudios, horas de estudio/trabajo, estrés financiero, sueño, alimentación, nivel educativo y antecedentes familiares |
| Salida | Probabilidad de la clase "depresión" (0–1), clase con umbral 0,5 y banda de riesgo (< 0,40 bajo · < 0,70 moderado · resto alto) |
| Artefacto | `models/v1/model.joblib`, SHA-256 `518bf27e9ca3b548…` |

## Uso previsto

- **Sí:** herramienta académica de concientización y orientación, para que un estudiante
  reflexione sobre factores asociados al malestar y sepa cuándo buscar ayuda.
- **No:** diagnóstico clínico, decisiones sobre personas (becas, admisión, sanciones), tamizaje
  institucional obligatorio ni uso sin el aviso ético.

## Datos

Student Depression Dataset (Kaggle): 27 857 registros utilizables de estudiantes de la India, con
depresión **autoreportada**. Split estratificado 70/15/15 con semilla 42. Ver [datasets.md](datasets.md).

## Comparación de candidatos (validación)

| Algoritmo | Mejores hiperparámetros | ROC-AUC CV (5 pliegues) | ROC-AUC val | F1 macro val | Recall clase 1 val |
|---|---|---|---|---|---|
| Dummy (base) | — | 0,500 | 0,500 | 0,369 | 1,000 |
| **Regresión logística** | C = 0,1 | 0,873 | **0,869** | 0,784 | 0,848 |
| Random Forest | max_depth = 16, min_samples_leaf = 20 | 0,870 | 0,864 | 0,783 | 0,861 |
| HistGradientBoosting | learning_rate = 0,05, max_leaf_nodes = 15 | 0,873 | 0,869 | 0,786 | 0,853 |

Se eligió la regresión logística: empata con el boosting (diferencia menor que 0,005) y es más
simple, interpretable, rápida y liviana (un artefacto de 7 KB).

## Rendimiento en test (4 179 registros nunca vistos)

| Métrica | Valor |
|---|---|
| ROC-AUC | **0,870** |
| Exactitud | 0,797 |
| F1 macro | 0,788 |
| Clase 1 (con depresión): precisión / recall / F1 | 0,811 / **0,851** / 0,831 |
| Clase 0 (sin depresión): precisión / recall / F1 | 0,774 / 0,720 / 0,746 |
| Matriz de confusión [[VN, FP], [FN, VP]] | [[1247, 485], [364, 2083]] |
| Recall por género | hombres 0,849 · mujeres 0,854 (brecha 0,005) |
| Latencia p95 por predicción | 38,9 ms (en el contenedor) |

Cumple los 8 criterios de aceptación (C1–C8).

## Consideraciones éticas

- Se **excluyó** la pregunta sobre pensamientos suicidas aunque mejoraba las métricas: es un dato
  extremadamente sensible y no corresponde pedirlo en un formulario abierto.
- No se piden ni guardan datos identificables. El historial solo es visible para administración.
- El 8,7 % del test son falsos negativos: el modelo **no** detecta a todos los estudiantes en
  riesgo. Por eso la interfaz siempre recomienda buscar apoyo profesional ante el malestar, sin
  importar el resultado.
- Se monitorea la equidad por género (C6). No se evaluaron otros grupos (por ejemplo, edad o nivel
  socioeconómico) por falta de datos fiables.

## Limitaciones

- Población de un solo país con depresión autoreportada: no generaliza a otros contextos sin
  re-entrenar con datos locales.
- Las variables son percepciones subjetivas (escalas 1–5) y la causalidad no está establecida.
- El 11,6 % del test son falsos positivos, que pueden generar preocupación: se mitiga con el
  lenguaje de "estimación" y el aviso.
- La edad tiene pocos casos por encima de los 40 años.

# Guion del video demostrativo (5 minutos)

**Preparación (antes de grabar):**
1. `docker compose up -d --build --wait`, y comprobar que los 4 servicios figuren como *healthy*.
2. Abrir en pestañas: http://127.0.0.1:8080 · http://127.0.0.1:8080/metricas · http://127.0.0.1:8000/docs ·
   el repositorio en GitHub (pestaña Pull requests).
3. Tener a mano un CSV para subir: por ejemplo, una copia de `data/raw/student_depression_dataset.csv`
   con algunas filas menos, para que su hash sea distinto.
4. Grabar a 1080p y aumentar el zoom del navegador al 110 %.

| Tiempo | Pantalla | Qué decir (resumen) |
|---|---|---|
| **0:00 – 0:30** | Página de evaluación | "Este es un sistema que estima el riesgo de depresión en estudiantes con machine learning. Es una herramienta académica, **no un diagnóstico**. Lo construimos siguiendo CRISP-ML(Q)." |
| **0:30 – 1:10** | `docs/documento-final.md` (cronograma y figuras 01–03) | "Usamos un dataset de Kaggle de casi 28 000 estudiantes. En el análisis vimos que la presión académica y el estrés financiero son los factores más asociados. **Por ética excluimos la pregunta sobre pensamientos suicidas**, aunque mejoraba el modelo, y descartamos columnas sin variación o con basura." |
| **1:10 – 1:50** | Figura 04 y pestaña Métricas | "Comparamos un modelo base contra regresión logística, Random Forest y Gradient Boosting, con un Pipeline sin data leakage. Elegimos la regresión logística: ROC-AUC de 0,87 y un 85 % de los casos de riesgo detectados. Cumple los 8 criterios que definimos **antes** de entrenar." Mostrar la matriz de confusión, la curva ROC y la tabla de criterios. |
| **1:50 – 2:30** | Evaluación: completar y enviar | Completar el formulario con presión 5, sueño menor a 5 h y estrés 5 → "Riesgo alto". "El resultado siempre incluye el aviso y una recomendación de buscar apoyo." Cambiar a valores sanos → riesgo bajo. |
| **2:30 – 3:00** | Swagger (`/docs`) | "La API REST está documentada con Swagger. Por ejemplo, si envío una edad de 12, responde 422 con un error claro." Ejecutar `POST /predictions` con edad 12. |
| **3:00 – 3:20** | Login → Historial | "Las funciones de administración requieren login. El historial muestra los datos enviados, el resultado y la versión del modelo. Está restringido porque son datos de salud mental." |
| **3:20 – 4:20** | Datasets → Re-entrenamiento | Subir el CSV ("se valida antes de aceptarlo"), luego Re-entrenar y mostrar el estado *En cola → Entrenando → Terminado*. "El entrenamiento corre en un worker en segundo plano. El candidato **no se activa solo**: aquí lo comparamos con el modelo activo." Activarlo y luego pulsar **Volver a la versión anterior** (rollback). |
| **4:20 – 4:45** | Terminal: `docker compose ps` · GitHub: PR con la revisión de Copilot y el CI en verde | "Todo corre en Docker Compose: base de datos, API, worker y web. Trabajamos con ramas y Pull Requests revisados por IA, con un pipeline que ejecuta casi 120 pruebas automáticas, incluidas las end-to-end." |
| **4:45 – 5:00** | Página de evaluación | "En resumen: un modelo entrenado con CRISP-ML(Q), un servicio REST con re-entrenamiento controlado y una interfaz web, construidos con criterios de calidad y de ética. Gracias." |

**Consejo:** el re-entrenamiento tarda 1–2 minutos. Lánzalo, sigue hablando y corta en la edición
la espera hasta que figure como "Terminado".

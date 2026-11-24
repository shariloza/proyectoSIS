# Lista de verificación de entregables

| # | Entregable de la materia | Estado | Dónde |
|---|---|---|---|
| 1 | Código fuente del servicio de IA | ✅ Listo | [backend/](../backend) |
| 2 | Código fuente de la aplicación web cliente | ✅ Listo | [frontend/](../frontend) |
| 3 | Diagrama de base de datos | ✅ Mermaid listo · ⬜ **Tú:** exportar el ERD desde pgAdmin (opcional) | [base-de-datos.md](base-de-datos.md) |
| 4 | Script o procedimiento para generar la base | ✅ Listo | [sql/schema.sql](sql/schema.sql) y [procedimiento](base-de-datos.md#procedimiento-para-generar-la-base) |
| 5 | Documento Swagger de la API | ✅ Listo | [openapi.json](openapi.json) · http://127.0.0.1:8000/docs |
| 6 | Video demostrativo (5 min) | ⬜ **Tú:** grabarlo y subirlo | Guion: [guion-video.md](guion-video.md) |
| 7 | Documento de CRISP-ML(Q) y del desarrollo del servicio y el cliente | ✅ Listo · ⬜ **Tú:** exportarlo a PDF/Word si lo piden así | [documento-final.md](documento-final.md) |
| 8 | URL del repositorio GitHub **público** | ⬜ **Tú:** verificar que sea público | https://github.com/shariloza/proyectoSIS |
| 9 | Evidencia de IA de revisión de PR (plus) | ⬜ **Tú:** capturas de Copilot en cada PR | Pestaña *Pull requests* de GitHub |
| — | Cronograma CRISP-ML(Q) | ✅ Listo | [documento-final.md §2](documento-final.md#2-metodología-y-cronograma) |
| — | Modelo entrenado con métricas aceptables | ✅ v1: ROC-AUC 0,870, C1–C8 cumplidos | [model-card.md](model-card.md) |

## Pasos pendientes (en orden)

1. Subir las ramas y abrir los PR hacia `dev`, uno por fase, en este orden: `feature/modelo-ml` →
   `feature/api` → `feature/frontend` → `feature/pruebas-e2e` → `feature/documentacion`.
2. En **cada** PR: pedir la revisión de **Copilot**, esperar el CI en verde, **tomar captura** de
   los comentarios de Copilot y del CI, y hacer merge.
3. PR final `dev` → `main`.
4. Settings → General → *Change visibility* → **Public**.
5. Grabar el video siguiendo el guion.
6. Si piden un documento en Word o PDF: abrir `docs/documento-final.md` en VS Code, usar
   "Markdown PDF" o copiarlo a Word. Las imágenes están en `docs/figuras` y `docs/capturas`.
7. Entregar: URL del repo, video, documento final y capturas de Copilot.

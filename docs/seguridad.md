# Seguridad

Revisión según la sección 8 de [base-ingenieria.md](base-ingenieria.md), hecha sobre el código real
en la Fase 6.

## Controles implementados

| Área | Control | Dónde |
|---|---|---|
| Autenticación | JWT HS256 con firma, `exp` (60 min), `iss`, `aud` e `iat` obligatorios | `auth/infrastructure/security.py` |
| | Secreto de ≥ 32 caracteres validado al iniciar | `config.py` |
| | Contraseñas con Argon2; verificación ficticia si el correo no existe (evita enumeración por tiempo) | `PasswordHasher` |
| | Mensaje genérico ante credenciales incorrectas | `AuthService.login` |
| Autorización | Rol `admin` verificado en el backend en cada request (`require_admin`) | `api/dependencies.py` |
| | El usuario se vuelve a leer de la base: un admin desactivado pierde el acceso | `AuthService.authenticate` |
| | La guardia de rutas del frontend solo evita pantallas vacías | `RequireAdmin.tsx` |
| Datos sensibles | El historial (salud mental) solo es accesible para administradores | `GET /predictions` |
| | No se guardan nombre, ciudad, IP ni la pregunta de pensamientos suicidas | `StudentProfileIn` (`extra=forbid`) |
| | Logs JSON sin cuerpos de request ni secretos | `shared/logging.py` |
| Entradas | Validación de tipos, rangos y categorías del contrato | Pydantic + `ml/schema.py` |
| | CSV: extensión y tipo MIME, tamaño (lectura acotada), columnas, tipos y dominios antes de guardar | `DatasetService` |
| | Nombre de almacenamiento generado por el servidor (hash), nunca el del usuario | `DatasetService` |
| Abuso | Rate limiting: 30 predicciones/min y 5 logins/min por IP | `shared/rate_limit.py` |
| Infraestructura | PostgreSQL, API y web publicados solo en `127.0.0.1`; red interna de Docker | `docker-compose.yml` |
| | Secretos solo en `.env` (fuera de git); el CI genera secretos aleatorios propios | `.gitignore`, `ci.yml` |
| | Backend como usuario sin privilegios (`uid 1000`); imágenes con versión fija | `backend/Dockerfile` |
| | Límites de CPU y memoria por servicio | `docker-compose.yml` |
| | CORS con lista blanca; en Docker el frontend va por el mismo origen (proxy) | `main.py`, `nginx.conf` |
| | Cabeceras CSP, `X-Frame-Options`, `nosniff` y `Referrer-Policy` | `frontend/security-headers.conf` |
| Integridad del modelo | Hash SHA-256 y versiones de librerías verificados antes de cargar un artefacto | `ml/artifact.py` |
| | Versiones inmutables; activación explícita y auditada (`model_activation_events`) | `model_registry` |

## Hallazgos de la revisión y correcciones

| # | Hallazgo | Corrección | Prueba de regresión |
|---|---|---|---|
| 1 | La subida leía el archivo completo en memoria antes de validar el tamaño (por el puerto directo de la API) | Lectura acotada a `MAX_UPLOAD_MB + 1` byte | `test_oversized_file_is_rejected` |
| 2 | React Router < 6.30.3 con vulnerabilidades de open redirect (GHSA-2w69-qvjg-hvjx, GHSA-2j2x-hqr9-3h42) | Actualizado a 6.30.6 | `npm audit` |
| 3 | La redirección después del login usaba `state.from` sin validar | `safeInternalPath` solo permite rutas internas | `safe-redirect.test.ts` |
| 4 | El entrenamiento usaba `n_jobs=-1`, con riesgo de quedarse sin memoria (worker limitado a 2 GB) | Paralelismo acotado (`N_JOBS = 2`, `OPENBLAS_NUM_THREADS=1`) | Suite completa en una máquina de 6 GB |

Auditoría de dependencias (24/11/2026): `pip-audit` no encontró vulnerabilidades en las
dependencias de producción del backend. `npm audit --omit=dev` reporta 2 avisos **moderados** que
afectan a toda la rama 6.x de React Router (ver riesgos).

## Riesgos aceptados y pendientes

| Riesgo | Mitigación actual | Recomendación para producción |
|---|---|---|
| React Router 6.x: GHSA-wrjc-x8rr-h8h6 (barra invertida) y GHSA-337j-9hxr-rhxg (solo SSR) | `safeInternalPath` rechaza `\`; la app no usa SSR | Migrar a React Router 7.17.1 o superior |
| JWT en `sessionStorage` (accesible ante un XSS) | CSP estricta, sin HTML dinámico, el token se pierde al cerrar la pestaña | Cookie `HttpOnly` + protección CSRF |
| Sin refresh token: la sesión dura 60 min | Decisión deliberada (KISS) | — |
| Rate limiting en memoria (por instancia) | Hay una sola instancia | Redis o el limitador del proxy si se escala |
| HTTP sin TLS en local | Puertos solo en `127.0.0.1` | TLS en el proxy (Dokploy/Traefik) al desplegar |
| La API confía en `X-Forwarded-For` (`--forwarded-allow-ips=*`) | Solo se publica en localhost | Restringir a la IP del proxy |
| Swagger público | Útil para la materia | Desactivar `/docs` en producción |
| Dataset de origen de Kaggle con autoreporte | Documentado en la model card | — |

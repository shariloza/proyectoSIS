# BASE DE INGENIERÍA Y ARQUITECTURA
## Estándar para proyectos de Software con IA / Machine Learning

Una vez comprendido el propósito, los requisitos y el alcance del proyecto, desarrolla la solución siguiendo los siguientes principios y estándares.

El objetivo es construir un sistema profesional, mantenible, seguro, escalable y preparado para evolucionar, evitando tanto la improvisación arquitectónica como la complejidad innecesaria.

Esta base establece principios generales. Las tecnologías, herramientas, servicios y estructuras concretas deben seleccionarse según las necesidades reales del proyecto.

---

# 1. PRINCIPIOS RECTORES

Toda decisión técnica debe respetar los siguientes principios:

### 1.1. Separation of Concerns
Cada componente, módulo y servicio debe tener una responsabilidad claramente delimitada.

### 1.2. SOLID
Aplicar los principios SOLID para mantener componentes cohesionados, extensibles y desacoplados.

### 1.3. DRY
Evitar duplicación de lógica, reglas de negocio, validaciones y transformaciones.

### 1.4. KISS
Preferir soluciones simples, legibles y fáciles de mantener.

### 1.5. YAGNI
No implementar funcionalidades, abstracciones o infraestructura que todavía no estén justificadas.

### 1.6. Clean Architecture / Hexagonal Architecture
Separar las reglas de negocio de los detalles de infraestructura, persistencia, APIs y frameworks.

### 1.7. Domain-Driven Design
Utilizar conceptos, entidades, servicios y límites de dominio que representen correctamente el problema que resuelve el sistema.

No imponer DDD complejo cuando una estructura modular más sencilla sea suficiente.

### 1.8. Dependency Inversion
Las reglas de negocio no deben depender directamente de implementaciones concretas de infraestructura.

### 1.9. Explicit over Implicit
Preferir contratos, configuraciones y comportamientos explícitos. Evitar valores por defecto silenciosos, dependencias ocultas y fallbacks que puedan producir resultados incorrectos.

### 1.10. Fail Fast
Detectar errores de configuración, datos inválidos y estados inconsistentes lo antes posible.

### 1.11. Modularidad
Organizar el sistema en módulos independientes por responsabilidad y dominio, procurando que los cambios en un módulo no provoquen modificaciones innecesarias en otros.

### 1.12. Evolución progresiva
Diseñar para permitir crecimiento sin introducir complejidad prematura.

La arquitectura debe resolver las necesidades actuales y evitar decisiones que dificulten innecesariamente las necesidades previsibles.

---

# 2. ARQUITECTURA GENERAL

Evaluar y definir una arquitectura adecuada al proyecto.

Cuando existan frontend, backend, base de datos y componentes de procesamiento de IA, mantener sus responsabilidades separadas.

Considerar, según corresponda:

- Frontend: presentación, navegación y experiencia de usuario.
- Backend/API: reglas de negocio, validaciones, autorización y orquestación.
- Base de datos: persistencia, integridad y consistencia.
- Servicios de IA/ML: entrenamiento, inferencia y evaluación.
- Workers: procesamiento asíncrono.
- Servicios externos: integraciones y proveedores.
- Infraestructura: contenedores, redes, almacenamiento y despliegue.

No asumir que todos los componentes deben ser servicios independientes.

Elegir entre monolito modular, arquitectura híbrida o servicios independientes según las responsabilidades, los requisitos y los costos operativos.

La separación debe ser lógica y justificable, no una fragmentación artificial.

---

# 3. BACKEND Y LÓGICA DE NEGOCIO

El backend debe concentrar las reglas de negocio y actuar como autoridad sobre los datos y las operaciones del sistema.

### Reglas obligatorias

- Mantener responsabilidades delimitadas.
- Separar presentación, aplicación, dominio e infraestructura cuando corresponda.
- Validar todas las entradas.
- Centralizar reglas de negocio.
- Evitar controladores con demasiada lógica.
- Evitar repositorios que contengan reglas de negocio.
- Definir contratos explícitos entre módulos.
- Implementar manejo de errores consistente.
- Utilizar transacciones cuando una operación requiera atomicidad.
- Evitar dependencias circulares.
- No duplicar validaciones importantes entre módulos.

### Organización sugerida

```text
backend/
├── src/
│   ├── modules/
│   │   └── <module>/
│   │       ├── domain/
│   │       ├── application/
│   │       ├── infrastructure/
│   │       └── presentation/
│   │
│   ├── shared/
│   ├── config/
│   └── main
│
├── tests/
└── migrations/
```

Adaptar esta estructura al lenguaje y framework seleccionado.

No crear carpetas vacías ni capas artificiales sin una necesidad real.

---

# 4. FRONTEND

El frontend debe estar separado de las reglas de negocio y consumir las capacidades del backend mediante contratos definidos.

### Reglas obligatorias

- Organizar por funcionalidades o dominios.
- Separar componentes reutilizables de componentes específicos.
- Centralizar la comunicación con APIs.
- Mantener tipos y contratos sincronizados con el backend.
- Gestionar correctamente estados de carga, error y éxito.
- No confiar en validaciones exclusivamente visuales.
- No almacenar secretos en el cliente.
- No implementar permisos críticos únicamente en frontend.
- Evitar duplicar reglas de negocio.
- Mantener una interfaz consistente, accesible y responsive.

El frontend debe reflejar el estado real del sistema y no simular operaciones que el backend no haya confirmado.

---

# 5. BASE DE DATOS Y GESTIÓN DE DATOS

Utilizar una base de datos adecuada a la naturaleza del proyecto.

Preferir bases relacionales cuando existan entidades relacionadas, integridad referencial y operaciones transaccionales.

### Reglas obligatorias

- Definir correctamente entidades y relaciones.
- Utilizar claves primarias y foráneas reales.
- Aplicar restricciones UNIQUE, CHECK y NOT NULL cuando corresponda.
- Crear índices según los patrones reales de consulta.
- Evitar relaciones polimórficas débiles.
- Utilizar transacciones para operaciones atómicas.
- Evitar duplicación innecesaria de información.
- Definir políticas de retención e historial.
- Evitar eliminación de datos históricos sin una decisión explícita.
- Mantener integridad entre los módulos.

### Migraciones

Toda evolución del esquema debe realizarse mediante migraciones versionadas.

No depender exclusivamente de scripts de inicialización de bases de datos.

Las migraciones deben:
- Ser revisables.
- Mantener trazabilidad.
- Considerar compatibilidad con versiones anteriores cuando corresponda.
- Evitar pérdida de datos.
- Tener una estrategia de recuperación.
- Poder ejecutarse de forma controlada en producción.

### Multi-tenancy

Si el proyecto administra organizaciones, empresas o múltiples clientes, evaluar aislamiento por tenant desde el diseño inicial.

Toda entidad perteneciente a un tenant debe mantener una relación explícita con este.

Las consultas y operaciones deben respetar el contexto del tenant.

Evaluar Row Level Security cuando la base de datos y el modelo de amenazas lo justifiquen.

---

# 6. MACHINE LEARNING ENGINEERING

Esta sección aplica cuando el proyecto incorpora modelos de Machine Learning.

### 6.1. Separación entre entrenamiento e inferencia

Cuando las necesidades lo justifiquen, separar el ciclo de entrenamiento del servicio de inferencia.

- El servicio de inferencia utiliza modelos aprobados.
- El entrenamiento se ejecuta en un proceso controlado.
- Los modelos candidatos no reemplazan automáticamente a los modelos activos.
- Las nuevas versiones deben superar evaluaciones definidas.
- Los fallos durante la actualización no deben inutilizar la versión estable.

### 6.2. Versionado de modelos

Cada modelo debe tener una versión identificable e inmutable.

Registrar, cuando corresponda:

- Identificador de versión.
- Fecha de entrenamiento.
- Dataset utilizado.
- Algoritmo.
- Hiperparámetros.
- Métricas de evaluación.
- Versiones de dependencias.
- Hash del artefacto.
- Estado de aprobación.
- Estado de activación.

Nunca sobrescribir silenciosamente una versión existente.

### 6.3. Reproducibilidad

Todo entrenamiento debe mantener suficiente información para reconstruir su contexto.

- Versionar datasets.
- Registrar parámetros.
- Controlar semillas aleatorias cuando corresponda.
- Documentar transformaciones.
- Separar entrenamiento, validación y prueba.
- Evitar data leakage.
- Registrar dependencias y configuraciones.

### 6.4. Evaluación de modelos

Definir criterios de aceptación antes de aprobar un modelo.

Seleccionar métricas adecuadas al problema.

No evaluar exclusivamente mediante una métrica global cuando existan diferencias importantes entre clases, grupos o segmentos.

Considerar:
- Rendimiento predictivo.
- Generalización.
- Robustez.
- Sesgos y equidad cuando sean relevantes.
- Costos computacionales.
- Tiempo de inferencia.
- Tamaño del modelo.

Los criterios de aprobación deben estar documentados y justificados.

### 6.5. Gestión del ciclo de vida

Definir un flujo controlado:

```text
Dataset
   ↓
Validación
   ↓
Entrenamiento
   ↓
Evaluación
   ↓
Aprobación
   ↓
Registro de versión
   ↓
Activación
   ↓
Monitoreo
   ↓
Reevaluación
```

La activación de una nueva versión debe permitir recuperación o rollback.

### 6.6. Trazabilidad

Cuando sea relevante, cada predicción debe poder relacionarse con:

- Versión del modelo.
- Fecha de ejecución.
- Datos de entrada pertinentes.
- Versión del preprocesamiento.
- Resultado producido.

Evitar almacenar información sensible innecesaria.

---

# 7. PROCESAMIENTO ASÍNCRONO

Utilizar workers y colas para operaciones prolongadas o que no deban bloquear una solicitud HTTP.

Ejemplos:

- Entrenamiento de modelos.
- Procesamiento de archivos.
- Generación de reportes.
- Procesamiento masivo de datos.
- Integraciones externas.
- Tareas programadas.

### Reglas

- Registrar los trabajos.
- Mantener estados explícitos.
- Evitar ejecuciones duplicadas cuando puedan generar inconsistencias.
- Implementar idempotencia cuando corresponda.
- Definir timeouts.
- Implementar reintentos controlados.
- Registrar errores.
- Permitir seguimiento del estado.
- Evitar pérdida silenciosa de trabajos.

Elegir la tecnología de colas según el lenguaje, infraestructura y necesidades del proyecto.

No introducir Redis, Kafka u otros componentes únicamente por tendencia tecnológica.

---

# 8. SEGURIDAD

La seguridad debe formar parte de la arquitectura desde el inicio.

### Autenticación

Definir un mecanismo apropiado de autenticación.

Si se utilizan JWT:
- Validar firma.
- Validar expiración.
- Validar issuer y audience.
- Gestionar claves de forma segura.
- Definir duración de tokens.
- Proteger los mecanismos de renovación.
- No confiar en información no verificada.

### Autorización

Autenticación y autorización son responsabilidades diferentes.

Implementar roles, permisos y políticas de acceso en el backend.

No confiar en restricciones exclusivamente visuales.

### Seguridad de datos

- Aplicar mínimo privilegio.
- Proteger información sensible.
- Aislar datos entre usuarios, organizaciones o tenants.
- Utilizar cifrado en tránsito.
- Evaluar cifrado en reposo según el riesgo.
- Mantener auditoría de operaciones relevantes.

### Seguridad de infraestructura

- No exponer servicios internos innecesariamente.
- No publicar bases de datos directamente a Internet.
- Gestionar secretos fuera del repositorio.
- Configurar CORS de forma restrictiva.
- Implementar rate limiting cuando corresponda.
- Utilizar dependencias mantenidas.
- Revisar vulnerabilidades.
- Evitar registrar credenciales o tokens.

La seguridad no debe depender exclusivamente del frontend ni de una sola capa de protección.

---

# 9. COMUNICACIÓN E INTEGRACIONES

Las comunicaciones entre módulos, servicios y proveedores deben utilizar contratos explícitos.

### Reglas

- Definir formatos de entrada y salida.
- Establecer manejo de errores.
- Definir timeouts.
- Evitar reintentos infinitos.
- Evitar dependencias circulares.
- No utilizar credenciales compartidas innecesariamente.
- No asumir que un servicio externo siempre estará disponible.
- Implementar idempotencia para operaciones sensibles.
- Documentar integraciones.

Cuando existan múltiples proveedores, utilizar adaptadores y contratos específicos para sus capacidades.

No forzar implementaciones artificialmente idénticas entre proveedores diferentes.

---

# 10. TESTING Y CALIDAD

Todo proyecto debe tener una estrategia de pruebas definida.

Organizar los tests fuera del código productivo.

### Tipos de pruebas

**Unitarias**
- Reglas de negocio.
- Validaciones.
- Funciones.
- Transformaciones.
- Estados.

**Integración**
- Base de datos.
- Repositorios.
- Transacciones.
- Comunicación entre servicios.
- Integraciones.

**Contratos**
- APIs.
- Esquemas.
- Comunicación entre componentes.

**End-to-end**
- Flujos completos del usuario.
- Operaciones administrativas.
- Procesos principales.

**Pruebas específicas de IA/ML**
- Preprocesamiento.
- Reproducibilidad.
- Evaluación.
- Regresión de modelos.
- Validación de datasets.
- Compatibilidad de artefactos.

### Reglas

- Cada bug importante debe generar una prueba de regresión.
- No utilizar mocks para sustituir todas las pruebas de integración.
- Probar escenarios negativos y errores.
- Probar permisos y aislamiento.
- No afirmar que un test pasó si no fue ejecutado.
- No considerar suficiente una prueba que únicamente comprueba que un endpoint responde correctamente.

---

# 11. DEVOPS E INFRAESTRUCTURA

Utilizar Docker para mantener entornos reproducibles y facilitar el despliegue.

Cuando se utilice Dokploy, organizar los servicios mediante Docker Compose según las necesidades del proyecto.

### Reglas

- Definir un Dockerfile por servicio cuando corresponda.
- Utilizar imágenes y versiones controladas.
- Separar configuración de desarrollo y producción.
- Utilizar redes privadas para servicios internos.
- Mantener volúmenes persistentes para información importante.
- Configurar healthchecks.
- Definir límites de recursos razonables.
- Gestionar variables de entorno de forma segura.
- Evitar depender de la etiqueta `latest`.
- Mantener backups.
- Probar restauraciones.

### CI/CD

Implementar un pipeline que incluya, según el proyecto:

1. Lint.
2. Type checking.
3. Tests unitarios.
4. Tests de integración.
5. Validación de configuración.
6. Build de imágenes.
7. Despliegue controlado.
8. Healthchecks posteriores al despliegue.

Separar ambientes de desarrollo, pruebas y producción cuando el alcance lo justifique.

No asumir que un despliegue exitoso significa que el sistema funciona correctamente.

---

# 12. OBSERVABILIDAD

El sistema debe permitir entender su estado y diagnosticar problemas.

Implementar, según las necesidades:

- Logs estructurados.
- Métricas.
- Healthchecks.
- Identificadores de correlación.
- Seguimiento de errores.
- Monitoreo de recursos.
- Alertas para fallos importantes.

En sistemas de IA/ML también considerar:

- Tiempo de inferencia.
- Versión del modelo activo.
- Rendimiento de los modelos.
- Fallos de entrenamiento.
- Calidad de datos.
- Cambios en la distribución de entradas.
- Posible degradación del modelo.

Nunca registrar secretos ni información sensible innecesaria.

---

# 13. DOCUMENTACIÓN

Mantener documentación técnica actualizada.

Como mínimo, evaluar la creación de:

- README.md
- AGENTS.md
- docs/arquitectura.md
- docs/base-de-datos.md
- docs/api.md
- docs/seguridad.md
- docs/despliegue.md
- docs/testing.md

Para proyectos de IA/ML, agregar:
- docs/ml-lifecycle.md
- docs/model-card.md
- docs/datasets.md

Documentar las decisiones arquitectónicas relevantes mediante ADR cuando aporte valor.

La documentación debe describir el sistema real, no una arquitectura ideal que todavía no existe.

---

# 14. REGLAS DE IMPLEMENTACIÓN PARA AGENTES DE IA

Antes de implementar:

1. Analizar los requisitos.
2. Inspeccionar el repositorio existente.
3. Identificar tecnologías y dependencias.
4. Comprender la arquitectura actual.
5. Identificar riesgos.
6. Proponer una estructura coherente.
7. Explicar decisiones importantes.

Durante la implementación:

- No improvisar arquitectura.
- No reescribir módulos completos sin justificación.
- No introducir dependencias innecesarias.
- No duplicar lógica.
- No crear abstracciones prematuras.
- No modificar contratos sin evaluar impacto.
- No eliminar datos históricos sin autorización.
- No debilitar mecanismos de seguridad.
- No ocultar errores.
- No inventar funcionalidades no solicitadas.

Después de implementar:

1. Ejecutar las pruebas pertinentes.
2. Revisar los cambios.
3. Verificar la integración entre componentes.
4. Actualizar documentación.
5. Informar qué se implementó.
6. Indicar qué pruebas se ejecutaron.
7. Identificar limitaciones y riesgos pendientes.

---

# 15. METODOLOGÍA DE TRABAJO

No desarrollar todo el proyecto de una sola vez sin validar su arquitectura.

Trabajar por fases:

### Fase 0 — Descubrimiento y análisis
Comprender el problema, requisitos, restricciones y alcance.

### Fase 1 — Diseño arquitectónico
Definir componentes, responsabilidades, tecnologías, contratos y estructura.

### Fase 2 — Fundamentos
Configurar repositorio, infraestructura, base de datos, seguridad y convenciones.

### Fase 3 — Desarrollo del núcleo
Implementar las reglas de negocio y capacidades principales.

### Fase 4 — Integraciones y procesamiento
Incorporar servicios externos, workers, modelos y procesos asíncronos cuando correspondan.

### Fase 5 — Frontend
Construir la experiencia de usuario sobre contratos definidos.

### Fase 6 — Testing y validación
Validar flujos, seguridad, integridad y comportamiento ante fallos.

### Fase 7 — Despliegue
Preparar CI/CD, infraestructura, monitoreo, backups y producción.

### Fase 8 — Documentación y cierre
Verificar que el sistema y su documentación estén alineados.

No avanzar automáticamente a una fase de alto impacto si existen decisiones arquitectónicas fundamentales sin resolver.

---

# 16. CRITERIOS DE CALIDAD

Una implementación no se considera terminada únicamente porque funciona en el escenario ideal.

Debe cumplir, según su alcance, los siguientes criterios:

- Correctitud funcional.
- Responsabilidades bien delimitadas.
- Seguridad.
- Integridad de datos.
- Manejo explícito de errores.
- Pruebas apropiadas.
- Trazabilidad.
- Mantenibilidad.
- Documentación.
- Despliegue reproducible.
- Capacidad de recuperación ante fallos relevantes.

---

# 17. PRINCIPIO FINAL

Construir software para que pueda mantenerse y evolucionar durante años, no solamente para completar una entrega inmediata.

Priorizar:

- Correctitud antes que velocidad.
- Claridad antes que complejidad.
- Integridad antes que conveniencia.
- Seguridad antes que confianza implícita.
- Modularidad antes que acoplamiento.
- Evidencia antes que suposiciones.
- Calidad antes que cantidad de código.

La arquitectura debe responder al problema real.

No utilizar tecnologías, patrones o servicios solamente porque sean populares.

Justificar las decisiones importantes y mantener una solución tan sencilla como sea posible, pero tan robusta como sea necesario.

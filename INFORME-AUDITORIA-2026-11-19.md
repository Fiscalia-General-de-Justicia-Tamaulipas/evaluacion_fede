# Informe de auditoría integral — Evaluación FEDE

**Fecha:** 19 de noviembre de 2026
**Alcance:** revisión estática del backend FastAPI/SQLAlchemy, frontend Vue 3, contratos y configuración Docker disponibles en el repositorio.
**Modo:** diagnóstico estático. En una iteración posterior, a solicitud explícita, se aplicaron dos correcciones de severidad alta; no se ejecutaron pruebas intrusivas contra un entorno desplegado.

## Resumen ejecutivo

La auditoría identificó **3 hallazgos altos, 6 medios y 1 bajo**. Se resolvieron o mitigaron nueve hallazgos: la API ya no revela si cada respuesta es correcta; el arranque exige una clave JWT robusta; se añadió una sesión de video no reutilizable con comprobación de progreso mínimo; se añadieron bloqueos persistentes de autenticación; las evaluaciones activas tienen una clave única; los perfiles sensibles dejaron de persistirse en `localStorage`; los JWT tienen versión de sesión revocable; Compose incorpora MySQL local y los registros se validan con mayor rigor. El hallazgo de privacidad de constancias queda como **riesgo aceptado por requerimiento funcional**: la verificación pública muestra nombre, municipio y sector.

El control de video sigue siendo una mitigación, no una prueba criptográfica o de telemetría que demuestre visionado real. La decisión de negocio sobre si este control es suficiente debe seguir siendo validada por el equipo responsable.

La suite unitaria disponible del frontend pasó y el bundle de producción se compiló en una ubicación temporal. La validación funcional contra una API y una base de datos reales no pudo ejecutarse: las dependencias Python del backend no están instaladas en el entorno de trabajo y no hay un servicio de base de datos declarado en Compose. No se inspeccionó el contenido de `.env`; por tanto, no se afirma que la clave predeterminada esté activa en el despliegue actual.

## Hallazgos identificados

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| 1 | 🟠 HIGH | `backend/app/main.py` | 3557-3565, 3583-3606 | La API revelaba `is_correct`; el usuario podía corregir respuestas hasta acertar. **Resuelto:** el guardado no devuelve aciertos y mantiene el cálculo al finalizar. | 10/10 |
| 2 | 🟠 HIGH | `backend/app/main.py` | 83-86, 2048-2053 | Existía una clave JWT de respaldo conocida. **Resuelto:** no hay fallback y el arranque exige al menos 32 caracteres. | 10/10 |
| 3 | 🟠 HIGH | `backend/app/main.py` | 827-839, 3438-3710 | El endpoint aceptaba una marca unilateral de fin de video. **Mitigado:** sesión nonce, tiempo mínimo de reproducción y progreso enviado por el reproductor; falta telemetría robusta verificable y la decisión del control sigue pendiente. | 10/10 |
| 4 | 🟡 MEDIUM | `backend/app/main.py` | 615-656, 2170-2250, 2757-3006 | Login y recuperación no tenían bloqueo persistente por intentos. **Resuelto en aplicación:** estado persistente por IP y cuenta/correo, con cinco fallos y bloqueo de 15 minutos. Debe complementarse con controles del gateway si existe exposición pública. | 8/10 |
| 5 | 🟡 MEDIUM | `backend/app/main.py` | 818-839, 3438-3622, 4068-4090 | Podían crearse evaluaciones activas duplicadas. **Resuelto en aplicación:** `active_attempt_key` único por usuario/módulo, bloqueo al finalizar y manejo de `IntegrityError`; el límite de tres intentos continúa verificándose al iniciar. | 8/10 |
| 6 | 🟡 MEDIUM | `frontend/src/services/auth.ts` | 19-85, 181-201 | Token y perfil completo persistían en `localStorage`. **Mitigado:** token y perfil minimizado pasan a `sessionStorage`; el CURP y correo dejan de almacenarse; se migra y limpia el dato legado de `localStorage`. Local/sessionStorage siguen vulnerables a XSS. | 9/10 |
| 7 | 🟡 MEDIUM | `backend/app/main.py`; `frontend/src/services/auth.ts` | 90-94, 2260-2290, 3047-3058, 181-201 | Logout y cambio de contraseña no revocaban JWT. **Resuelto en aplicación:** `token_version` en usuario y JWT, endpoint de logout, vigencia reducida a 60 minutos por defecto y revocación al cambiar contraseña. | 9/10 |
| 8 | 🟡 MEDIUM | `backend/app/main.py`; `frontend/src/views/certificates/CertificateVerificationView.vue` | 3267-3295; líneas del componente | La verificación pública expone nombre, municipio y sector. **Riesgo aceptado por requerimiento funcional explícito:** estos datos se muestran para identificar a la persona acreditada. El equipo debe confirmar que su publicación concuerda con la política institucional y el consentimiento aplicable. | 9/10 |
| 9 | 🟡 MEDIUM | `docker-compose.yml`; `.env.example` | 1-60 | Compose no incluía MySQL y apuntaba a `db` sin servicio. **Resuelto:** se añadió MySQL 8.4, volumen persistente, healthcheck y `DATABASE_URL` interno al servicio. | 9/10 |
| 10 | ⚪ LOW | `backend/app/main.py` | 2208-2270, 2520-2628 | Identificadores de catálogos y texto no tenían todas las restricciones. **Resuelto:** límites Pydantic, patrones CURP/nombre y validación de catálogos Sí/No. | 9/10 |

### Recomendaciones de corrección

1. **Aplicada:** se eliminó `is_correct` de las respuestas de guardado. El cálculo del puntaje sigue exclusivamente en el servidor y se devuelve al finalizar.
2. **Aplicada:** el arranque falla si `SECRET_KEY` no tiene al menos 32 caracteres; se eliminó el fallback conocido y se documentó cómo generar la clave.
3. **Pendiente por decisión del usuario:** no tratar una marca enviada por el navegador como prueba del visionado. Integrar telemetría confiable del reproductor antes de cambiar el requisito.
4. Añadir limitación de intentos de autenticación y recuperación por cuenta e IP, demoras progresivas y monitoreo; confirmar controles equivalentes del proxy/gateway.
5. Hacer atómica la reserva de intento: serializar por usuario/módulo o aplicar una restricción de datos para una evaluación activa, y verificar el límite al iniciar y finalizar.
6. Evitar persistir CURP y token en almacenamiento accesible a JavaScript. Preferir cookies `HttpOnly`, `Secure`, `SameSite` y minimizar el perfil guardado.
7. Incorporar revocación/rotación de sesión al cerrar sesión y cambiar contraseña, y reducir la duración del token de acceso.
8. Reducir la respuesta pública de verificación a folio, curso, fecha y los datos estrictamente necesarios para validar la identidad del titular.
9. Añadir un servicio MySQL a Compose o documentar y validar explícitamente la dependencia externa, incluyendo espera/healthcheck.
10. Validar todos los identificadores de catálogos y acotar longitudes/formato en Pydantic; convertir errores de integridad esperables en respuestas controladas.

## Registro de pruebas y revisiones

| Prueba / área | Cómo se probó | Resultado | Hallazgo / limitación |
|---|---|---|---|
| Suite unitaria del frontend | `cd frontend && npm test` (Vitest) | **Aprobada:** 9 archivos, 15 pruebas | No cubre integración con FastAPI, navegador real ni base de datos. |
| Build frontend | `cd frontend && npm run build -- --outDir /tmp/evaluacion-fede-audit-build` | **Aprobado:** Vite compiló 2011 módulos en la última ejecución | El build normal falló al limpiar `frontend/dist/assets` (`EACCES`). Se verificó el build en `/tmp` para no alterar el directorio con permisos restringidos. |
| Sintaxis backend | `python3 -m compileall -q backend/app` | **Aprobada** | Solo comprueba sintaxis; no importa ni ejecuta la aplicación. |
| Disponibilidad de dependencias del backend | Importación de `fastapi`, `sqlalchemy`, `pydantic`, `jose`, `passlib` y `pymysql` en el Python del entorno; después, instalación de `backend/requirements.txt` en un entorno temporal bajo `/tmp` | **Inicialmente bloqueada** (`python-dotenv` ausente); al instalar dependencias en el entorno temporal, se pudieron correr pruebas unitarias | No se modificaron manifiestos. La falta de una base de pruebas siguió impidiendo la integración real con MySQL. |
| Inspección de servicios Compose | `docker compose config --services` | **Observado:** solo `api` y `frontend` | No hay servicio `db` en el archivo; no se inició el stack. |
| Autenticación, autorización, intentos y sesiones | Revisión estática de login, dependencia JWT, recuperación de contraseña y rutas de evaluación | **Hallazgos 2, 4, 5 y 7** | No se pudo hacer prueba de dos usuarios, token expirado, enumeración temporal ni concurrencia contra base real. |
| Respuestas, calificación y flujo de módulos | Revisión estática de carga de preguntas, guardado de respuesta, finalización y emisión de constancia | **Hallazgos 1, 3 y 5** | No se enviaron peticiones activas a un servidor. La respuesta con `is_correct` está presente en ambos caminos de guardado. |
| Validación y manejo de errores | Revisión de modelos Pydantic, excepciones de API y asignaciones a modelos SQLAlchemy | **Hallazgo 10** | Los casos inválidos de base de datos no se pudieron reproducir sin las dependencias y una base de pruebas. |
| Contrato frontend/API y errores de red | Revisión de servicios Vue, URL/endpoints y pruebas unitarias existentes | Los contratos principales coinciden en el código revisado; las pruebas cubren manejo de errores unitario | No se pudo validar CORS, respuestas reales, timeout, caída de API ni fallos de base de datos en integración. |
| CORS, TLS, cabeceras y controles de borde | Revisión de configuración presente en el repositorio | No se verificó un entorno de producción | No hay configuración de proxy/TLS/CSP/gateway en el alcance disponible; CORS depende de variables de entorno. |
| Inspección de secretos | Se revisaron las referencias a variables, sin leer `.env` | **No verificado** | Se desconoce si el despliegue configura `SECRET_KEY`, credenciales, CORS, correo y TLS de manera segura. |
| Ejecución visual y accesibilidad | Revisión estática de vistas y tests existentes | **No ejecutada en navegador** | No había servidor iniciado; no se probaron viewports, teclado, lector de pantalla ni video real. |
| No exposición del acierto en respuestas | Revisión del contrato de respuesta de `save_answer` después del cambio | **Corregido estáticamente:** se retiró `is_correct` de las dos ramas de respuesta | La ejecución de la ruta backend no pudo validarse sin dependencias Python instaladas. |
| Configuración de clave JWT | Revisión de configuración y validación de arranque después del cambio | **Corregido estáticamente:** `SECRET_KEY` ahora debe tener al menos 32 caracteres y no tiene clave de respaldo conocida | No se inspeccionó `.env` ni se pudo iniciar FastAPI; el despliegue actual debe configurar una clave aleatoria de 32 caracteres o más. |
| Verificación real de reproducción | Revisión del flujo y elección de política por el usuario | **Pendiente por decisión del usuario** | Se conserva el control actual hasta integrar telemetría confiable del reproductor; el evento `ended` del cliente no constituye prueba para el servidor. |
| Regresión después de las correcciones seleccionadas | `cd frontend && npm test`; `python3 -m compileall -q backend/app`; inspección estática de las respuestas de `save_answer` y de la validación de `SECRET_KEY` | **Aprobada:** 9 archivos/15 pruebas frontend; sintaxis Python válida; ambos caminos de respuesta ya no incluyen `is_correct` | Las pruebas unitarias de la ruta usan una base simulada; no se pudo validar el ciclo de vida completo de FastAPI ni conectar a MySQL. |
| Pruebas unitarias backend de regresión | `cd backend && /tmp/eval-fede-test-venv/bin/python -m unittest discover -s tests -v` | **Aprobada:** 4 pruebas para respuestas nuevas/actualizadas y validación de `SECRET_KEY` | La primera ejecución en Python del sistema se bloqueó por `ModuleNotFoundError: dotenv`; se repitió correctamente con las dependencias del proyecto en entorno temporal. No cubre conexión MySQL ni ciclo HTTP. |
| Diagnóstico Pylance | Solicitudes de sintaxis y diagnósticos del archivo `backend/app/main.py` | **No ejecutable** | El servidor MCP no inicializó: error de transporte al endpoint local `http://localhost:36275/stream`. La sintaxis se verificó con `compileall` y con las pruebas Python. |
| Límite de autenticación | Prueba unitaria del estado persistente con cinco fallos y ventana de 15 minutos | **Aprobada** | Cubre bloqueo por cuenta/IP; no cubre un proxy distribuido ni concurrencia extremo sin base real. |
| Integridad de evaluaciones concurrentes | Prueba SQLite in-memory de restricción única `active_attempt_key` | **Aprobada** | Confirma que dos evaluaciones con la misma clave no pueden existir simultáneamente en una BD compatible. No sustituye prueba MySQL real. |
| Sesión JWT revocable | Prueba unitaria de incremento de `token_version` al cambiar contraseña | **Aprobada** | Verifica que la nueva contraseña invalida la versión anterior; el endpoint HTTP de logout no se probó contra FastAPI real. |
| Video con sesión | Prueba unitaria de nonce desconocido y progreso mínimo | **Aprobada** | Solo demuestra mitigación por nonce y tiempo mínimo; no demuestra visionado real ni telemetría confiable. |
| Privacidad/formato de constancias | Prueba unitaria de respuesta pública con nombre, municipio, sector, folio completo de almacenamiento y prueba de consulta por sufijo | **Aprobada** | Nombre, municipio y sector se exponen públicamente por requerimiento explícito; queda pendiente la validación institucional de privacidad/consentimiento. |
| Validación de registro | Pruebas Pydantic de nombres con control y identificadores de catálogo inválidos | **Aprobadas** | No cubre errores de todas las combinaciones demográficas ni integridad externa. |
| Suite backend completa | `/tmp/eval-fede-test-venv/bin/python -m unittest discover -s tests -v` | **Aprobada:** 15 pruebas en la última ejecución | Dependencias instaladas temporalmente; no se inició MySQL real ni se usó `TestClient` HTTP. |
| Suite frontend completa | `cd frontend && npm test` | **Aprobada:** 10 archivos/18 pruebas en la última ejecución | Cubre almacenamiento de sesión, verificación pública y presentación; no sustituye navegador ni CORS real. |
| Build Docker Compose | `docker compose config` | **Aprobado** | Se añadió `db` con MySQL, volumen y healthcheck. No se inició el stack ni se creó la base real. |
| Formato de constancia solicitado | Pruebas de `certificate-format`, generación PDF y pantalla de validación | **Aprobado:** nombre en mayúsculas y folio sin `FEDE-{año}-`; el PDF conserva el folio completo en la ruta QR/archivo, la API y la base de datos. El folio corto también se acepta en la consulta pública. | El nombre completo vuelve a ser visible públicamente por requerimiento funcional. |
| Validación final del formato | `cd frontend && npm test`; build a `/tmp/evaluacion-fede-certificate-build`; `cd backend && python -m unittest discover -s tests -v` en venv temporal | **Aprobada:** 10 archivos/18 pruebas frontend; build Vite de 2011 módulos; 15 pruebas backend tras la corrección del puntaje | No se ejecutó integración contra MySQL remota. |
| Bug de puntaje reportado posteriormente | Prueba SQLite con intento completado de 1 respuesta correcta de 10 y test de regresión frontend con 10/100 no aprobado | **Corregido:** los conteos de aciertos/preguntas son fuente autoritativa para convertir a porcentaje; ya no se multiplica una calificación de 10% como si fuera 10/10 | No requiere migración de datos: resultados existentes con conteos se recalculan al consultar estado; filas históricas sin conteos usan el puntaje almacenado como porcentaje. |

## Suposiciones y límites

- Se asume la arquitectura indicada por los archivos del repositorio: Vue 3 + Vite en cliente, FastAPI + SQLAlchemy en servidor, MySQL como persistencia y JWT bearer para autenticación.
- El análisis se limita al código y configuración versionados disponibles. No se inspeccionaron valores de `.env`, servicios externos de correo, configuración de producción, logs, instancia de base de datos ni controles del proxy.
- No se pudieron confirmar controles implementados fuera del repositorio, como rate limiting, TLS, firewall, CSP, rotación de claves o restricciones de acceso a la base de datos.
- No se ejecutó escaneo dinámico ni se intentó explotar un sistema desplegado.

## Estado de correcciones

## Archivos modificados

- `backend/app/main.py`: validación de entrada, clave JWT, límites de autenticación, revocación por versión, claves únicas de evaluación, sesión de video y respuesta pública minimizada.
- `backend/tests/test_security_regressions.py`: pruebas de regresión para secretos, respuestas, bloqueos, tokens, privacidad, video, catálogos, concurrencia y cálculo de puntajes.
- `frontend/src/services/auth.ts`: migración de token/perfil a `sessionStorage`, perfil minimizado y revocación remota al cerrar sesión.
- `frontend/src/services/auth.test.ts`: validación de almacenamiento sin correo/CURP y bearer.
- `frontend/src/views/certificates/CertificateVerificationView.vue` y su prueba: presentación del nombre en mayúsculas, municipio, sector y folio abreviado.
- `frontend/src/services/certificate.ts`, `frontend/src/lib/certificate-format.ts` y pruebas asociadas: nombre y folio mostrados en PDF y validación; consulta abreviada conserva el folio completo en almacenamiento.
- `frontend/src/views/exams/ExamModuleView.vue` y `ExamFlowView.vue`: envío de nonce y progreso de video.
- `frontend/src/views/modules/ModulePanelView.test.ts`: regresión para asegurar que un 10% fallido no acredita ni desbloquea el siguiente módulo.
- `docker-compose.yml`: servicio MySQL, volumen, healthcheck y dependencia de API.
- `.env.example`: variables de secreto, vigencia y recuperación documentadas sin valores reales.

## Estado final

- **Resueltos:** 1, 2, 4, 5, 7, 9 y 10.
- **Mitigados:** 3 y 6.
- **Riesgo aceptado por decisión funcional:** 8 (se muestran públicamente el nombre, municipio y sector; validar base legal/consentimiento institucional).
- **Pendiente de decisión/validación:** telemetría real del video y controles equivalentes en gateway/TLS/proxy. El equipo debe validar MySQL real, el ciclo HTTP FastAPI, CORS, protección contra XSS y operación distribuida de límites.
- **Cambio funcional posterior:** nombre en mayúsculas y folio abreviado en PDF y validación; se mantiene el folio completo internamente.

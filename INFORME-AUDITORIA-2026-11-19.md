# Informe de auditoría integral — Evaluación FEDE

**Fecha:** 19 de noviembre de 2026
**Alcance:** revisión estática del backend FastAPI/SQLAlchemy, frontend Vue 3, contratos y configuración Docker disponibles en el repositorio.
**Modo:** diagnóstico estático. En una iteración posterior, a solicitud explícita, se aplicaron dos correcciones de severidad alta; no se ejecutaron pruebas intrusivas contra un entorno desplegado.

## Resumen ejecutivo

La auditoría identificó **3 hallazgos altos, 6 medios y 1 bajo**. Después de la revisión, y por selección explícita del usuario, se corrigieron dos hallazgos altos: la API ya no revela si cada respuesta es correcta y el backend rechaza iniciar con una clave JWT vacía o corta. El hallazgo del video permanece pendiente por decisión del usuario hasta integrar telemetría confiable del reproductor; el navegador por sí solo no puede probar que una persona vio el video.

La suite unitaria disponible del frontend pasó y el bundle de producción se compiló en una ubicación temporal. La validación funcional contra una API y una base de datos reales no pudo ejecutarse: las dependencias Python del backend no están instaladas en el entorno de trabajo y no hay un servicio de base de datos declarado en Compose. No se inspeccionó el contenido de `.env`; por tanto, no se afirma que la clave predeterminada esté activa en el despliegue actual.

## Hallazgos identificados

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| 1 | 🟠 HIGH | `backend/app/main.py` | 3557-3565, 3591-3606 | La API de respuestas revelaba `is_correct`; el usuario podía probar opciones y corregir respuestas antes de finalizar, alterando el resultado y pudiendo obtener una constancia sin demostrar conocimiento. **Corregido después de la auditoría.** | 10/10 |
| 2 | 🟠 HIGH | `backend/app/main.py` | 83-86, 2104-2116 | Se usaba `change-this-secret-key` como clave JWT de respaldo. Si faltaba `SECRET_KEY` en el entorno de producción, un atacante podía firmar tokens y suplantar usuarios. **Corregido después de la auditoría:** no hay fallback y el arranque exige 32 caracteres como mínimo. | 10/10 |
| 3 | 🟠 HIGH | `backend/app/main.py` | 3406-3445 | El endpoint de video solo verifica propiedad de la evaluación y acepta que el cliente marque el video como completado; no comprueba progreso ni una sesión de reproducción. Se puede omitir el requisito de capacitación. **Pendiente por decisión del usuario.** | 10/10 |
| 4 | 🟡 MEDIUM | `backend/app/main.py` | 2757-2789 | No se observa limitación de intentos ni espera progresiva en login. Sin un control equivalente en infraestructura, permite fuerza bruta y credential stuffing. La infraestructura externa no se pudo verificar. | 8/10 |
| 5 | 🟡 MEDIUM | `backend/app/main.py` | 3199-3219, 3313-3362, 3689-3717 | La creación de evaluaciones consulta intentos activos/completados y luego inserta sin bloqueo ni restricción que impida evaluaciones activas duplicadas. Solicitudes concurrentes pueden crear evaluaciones paralelas y superar el máximo de intentos, ya que el cierre no vuelve a imponer ese límite. | 8/10 |
| 6 | 🟡 MEDIUM | `frontend/src/services/auth.ts` | 19-20, 44-47 | El token bearer y el objeto de usuario completo se guardan en `localStorage`; el objeto incluye correo y CURP. Cualquier XSS o script de terceros ejecutado en el origen podría leerlos. No se confirmó una XSS en el código revisado. | 9/10 |
| 7 | 🟡 MEDIUM | `backend/app/main.py`; `frontend/src/services/auth.ts` | 90-94, 2116-2140, 2749-2750; 51-55 | Cerrar sesión solo borra el estado del navegador. Cambiar la contraseña tampoco revoca tokens ya emitidos; la API valida firma y expiración, con una vigencia predeterminada de 24 horas. Un token copiado puede seguir siendo válido durante ese periodo. | 9/10 |
| 8 | 🟡 MEDIUM | `backend/app/main.py` | 3029-3056 | La verificación pública de constancias revela nombre completo, municipio y sector. El folio aleatorio reduce la enumeración, pero la combinación expone datos personales que no son necesarios para comprobar autenticidad. | 9/10 |
| 9 | 🟡 MEDIUM | `docker-compose.yml`; `README.md` | 1-30; configuración local | Compose define `api` y `frontend`, pero no una base de datos; la configuración documentada apunta a un host `db`. El arranque local indicado no es autosuficiente salvo que exista una base externa accesible con esa configuración. | 9/10 |
| 10 | ⚪ LOW | `backend/app/main.py` | 2256-2262, 2621-2624 | Los identificadores de algunos catálogos demográficos se asignan sin comprobar que existan y algunos campos de texto no tienen límites Pydantic. Un valor inválido puede producir un error de integridad en `commit` y responder como fallo interno en vez de error de validación. | 9/10 |

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
| Build frontend | `cd frontend && npm run build -- --outDir /tmp/evaluacion-fede-audit-build` | **Aprobado:** Vite compiló 2010 módulos | El build normal falló al limpiar `frontend/dist/assets` (`EACCES`). Se verificó el build en `/tmp` para no alterar el directorio con permisos restringidos. |
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

## Suposiciones y límites

- Se asume la arquitectura indicada por los archivos del repositorio: Vue 3 + Vite en cliente, FastAPI + SQLAlchemy en servidor, MySQL como persistencia y JWT bearer para autenticación.
- El análisis se limita al código y configuración versionados disponibles. No se inspeccionaron valores de `.env`, servicios externos de correo, configuración de producción, logs, instancia de base de datos ni controles del proxy.
- No se pudieron confirmar controles implementados fuera del repositorio, como rate limiting, TLS, firewall, CSP, rotación de claves o restricciones de acceso a la base de datos.
- No se ejecutó escaneo dinámico ni se intentó explotar un sistema desplegado.

## Estado de correcciones

**Correcciones aplicadas en la iteración posterior solicitada:** hallazgo 1 (no devolver `is_correct`) y hallazgo 2 (rechazar arranque con `SECRET_KEY` ausente o menor a 32 caracteres). Se documentó la variable en `.env.example` y en `README.md`.

**Pendiente:** hallazgo 3 (validación del video), por decisión explícita de mantener el requisito actual hasta integrar telemetría confiable. Los hallazgos 4–10 también permanecen pendientes. La validación en runtime de las dos correcciones aplicadas queda pendiente porque las dependencias Python no están disponibles en este entorno.

# Informe de pruebas exploratorias E2E

**Aplicación:** Evaluación de Capacitación – Fiscalía Especializada en Delitos Electorales  
**Entorno:** QA local (`http://localhost:5174`). La URL indicada inicialmente (`http://localhost:5173`) rechazó la conexión; se continuó por el puerto local expuesto por el servicio activo.  
**Fecha:** 20 de noviembre de 2026  
**Perfil utilizado:** cuenta de prueba nueva; no se incluyen credenciales en este informe.  
**Alcance:** pruebas manuales guiadas por la interfaz del navegador. Las conclusiones se basan en lo visible y en el comportamiento observado; no se consultaron código ni base de datos.

## Resumen ejecutivo

**Retest:** 20 de noviembre de 2026, con una cuenta nueva.

| Severidad | No resueltos | Resueltos | Parciales |
|---|---:|---:|---:|
| Crítica | 0 | 1 | 0 |
| Alta | 0 | 1 | 0 |
| Media | 0 | 0 | 0 |
| Baja | 0 | 3 | 0 |
| **Total** | **0** | **5** | **0** |

**Conclusión del retest:** los cinco hallazgos están resueltos; E2E-001 y E2E-002 se confirmaron manualmente en esta pasada. Se completaron los tres módulos con 100/100 cada uno. La interfaz confirmó que la constancia se generó y se envió a la descarga del navegador, pero el navegador de pruebas no expuso el archivo para revisar sus datos y formato. La aprobación final de producción queda condicionada a esa inspección, además de las pruebas de sesión expirada y error de red.

**Validación automatizada posterior a los cambios:** 22 pruebas de backend y 24 de frontend aprobadas; compilación de producción del frontend aprobada.

## Hallazgos

### E2E-001 — El módulo 2 no finaliza pese a mostrar 10/10 respuestas

- **Severidad:** Crítica
- **Pantalla:** Evaluación / módulo 2
- **Estado de retest:** Resuelto; confirmado manualmente
- **Pasos para reproducir:**
  1. Crear una cuenta nueva y acreditar el módulo 1.
  2. Iniciar el módulo 2 y completar el requisito del video que muestra la interfaz.
  3. Contestar las 10 preguntas visibles y comprobar el indicador **10 de 10 contestadas**.
  4. Pulsar **Finalizar evaluación** y confirmar.
- **Resultado esperado:** La evaluación se finaliza y muestra el resultado del módulo cuando todas las preguntas visibles están contestadas.
- **Resultado obtenido en el retest original:** La pantalla muestra **Pregunta 10 de 10**, **10 de 10 contestadas** y **Avance: 100%**, pero al finalizar aparece HTTP 400 y el aviso “No se pudo completar la acción”. El detalle enumera 12 preguntas del banco que no están disponibles en la interfaz.
- **Corrección y validación:** El backend ahora normaliza cualquier orden heredado a 10 preguntas, valida pendientes solo contra los 10 IDs seleccionados y usa esos mismos IDs para calcular el total y la calificación. Una regresión con una evaluación heredada de 22 preguntas confirma que 10 respuestas bastan para finalizar con total 10; si falta una, el error identifica su posición visible (por ejemplo, **10**), no números del banco.
- **Resultado del retest actual:** En una cuenta recién creada, se completaron las 10 preguntas visibles. La finalización tuvo éxito y mostró **Módulo aprobado**, **100/100**, **10/10** e **Intento 1 de 3**; no apareció el HTTP 400 ni la lista de pendientes.
- **Estado de pantalla/evidencia:** Corrección confirmada en navegador y en pruebas automatizadas. El módulo 3 quedó desbloqueado.
- **Impacto observado antes de la corrección:** Bloqueaba la acreditación del módulo 2, impidiendo desbloquear el módulo 3 y obtener la constancia. En el primer ciclo se mostraron 22 preguntas y en el retest anterior de cuenta nueva se mostraron 10; la finalización seguía solicitando respuestas de preguntas no visibles.

### E2E-002 — El aviso de finalización fallida no permite una recuperación clara

- **Severidad:** Alta
- **Pantalla:** Evaluación / finalización del módulo 2
- **Estado de retest:** Resuelto; confirmado manualmente
- **Pasos para reproducir:** Seguir los pasos de E2E-001 y confirmar la finalización con las 10 preguntas visibles contestadas.
- **Resultado esperado:** Si falla la finalización, explicar una causa que concuerde con el estado mostrado y ofrecer una acción para reintentar o corregir las preguntas pendientes.
- **Resultado obtenido en el retest original:** Aparece un aviso genérico con preguntas pendientes que no existen en la navegación visible ni una acción para reintentar.
- **Corrección y validación:** La interfaz muestra el detalle devuelto por el backend y ofrece **Reintentar finalización** sin borrar las respuestas guardadas. Una prueba simula el HTTP 400, verifica el detalle visible y confirma que el reintento exitoso muestra el resultado.
- **Resultado del retest actual:** Al completar y finalizar el módulo 2 no se mostró el aviso de error. Se obtuvo el resultado de aprobado, 100/100.
- **Estado de pantalla/evidencia:** El error y su ruta de recuperación no se reprodujeron porque la finalización tuvo éxito; la corrección del mensaje y del reintento continúa cubierta por pruebas automatizadas.

### E2E-003 — El título del examen se comprime en móvil

- **Severidad:** Baja
- **Pantalla:** Evaluación del módulo 2, viewport de 375 × 812 px
- **Estado de retest:** Resuelto
- **Pasos para reproducir:** Abrir la evaluación y reducir el viewport a 375 × 812 px.
- **Resultado esperado:** El encabezado y el indicador de pregunta comparten el espacio sin forzar cortes excesivos en el título.
- **Resultado obtenido en retest:** El título se distribuye en tres líneas dentro de una tarjeta de progreso legible; el indicador y el avance no lo comprimen excesivamente. No se observó desplazamiento horizontal.
- **Estado de pantalla/evidencia:** Captura del retest a 375 × 812 px: la pregunta y las opciones se acomodan en tarjetas verticales y permanecen legibles.

### E2E-004 — Errores de ortografía y redacción en textos visibles

- **Severidad:** Baja
- **Pantallas:** Preguntas de los módulos 1 y 2; **Documentos de apoyo**
- **Estado de retest:** Resuelto; confirmado en retest móvil previo
- **Pasos para reproducir:** Revisar el texto de las preguntas y los títulos visibles durante los módulos.
- **Resultado esperado:** Preguntas y títulos con ortografía, acentuación y redacción correctas.
- **Resultado obtenido en el retest original:** Se observaron errores en el texto de preguntas y faltaban tildes en “Impugnación” y “Políticos” en los títulos de documentos.
- **Corrección y validación:** Se corrigieron los textos heredados de preguntas del banco en la inicialización, y una prueba de interfaz comprueba los títulos **Ley de Medios de Impugnación Electorales** y **Ley General de Partidos Políticos**. Las pruebas de backend verifican el contenido corregido de las preguntas sembradas.
- **Resultado del retest actual:** Las preguntas observadas en los tres módulos muestran acentos corregidos. En el panel de documentos se verificaron los títulos **Ley de Medios de Impugnación Electorales** y **Ley General de Partidos Políticos** con sus tildes.
- **Estado de pantalla/evidencia:** Corrección confirmada en navegador y cubierta por pruebas automatizadas.

### E2E-005 — Se muestra un aviso de registro después de cerrar sesión

- **Severidad:** Baja
- **Pantalla:** Inicio de sesión, después de cerrar sesión
- **Estado de retest:** Resuelto; confirmado manualmente
- **Pasos para reproducir:**
  1. Crear una cuenta nueva e iniciar sesión con ella.
  2. Cerrar sesión desde el panel del curso.
- **Resultado esperado:** Mostrar una confirmación de cierre de sesión o volver al formulario sin avisos ajenos a la acción realizada.
- **Resultado obtenido en el retest original:** Tras cerrar sesión, el formulario mostraba “Tu registro se completó. Ahora puedes iniciar sesión”.
- **Corrección y validación:** El aviso se limpia al cambiar el estado de autenticación a no autenticado. Una prueba de `App` reproduce registro, inicio y cierre de sesión y verifica que el aviso ya no aparezca.
- **Resultado del retest actual:** Después de cerrar sesión, el formulario de inicio de sesión no mostró el aviso de registro.
- **Estado de pantalla/evidencia:** Corrección confirmada en navegador y cubierta por prueba automatizada.

## Cobertura y resultados sin hallazgo

- **Registro:** se probaron campos vacíos, CURP con longitud incorrecta, correo inválido, contraseña menor de 8 caracteres, contraseñas distintas y correo ya registrado. Se mostraron mensajes de validación; el correo duplicado se rechazó con “El correo ya está registrado”.
- **Inicio de sesión:** credenciales vacías y contraseña incorrecta mostraron errores claros. Tras tres intentos incorrectos no se observó bloqueo ni aviso de espera. El inicio de sesión con la cuenta creada y el cierre de sesión funcionaron.
- **Módulo 1:** se contestaron 10 preguntas y se obtuvo **100/100 (10/10 correctas)**. Las respuestas seleccionadas coincidieron con el criterio visible del curso; no se observaron preguntas repetidas.
- **Módulo 2:** se mostraron 10 preguntas sin repetición; se contestaron las 10 y la evaluación finalizó con **100/100 (10/10)**. Se confirmó manualmente la resolución de E2E-001 y E2E-002.
- **Módulo 3:** se mostraron 10 preguntas sin repetición; se contestaron las 10 y la evaluación finalizó con **100/100 (10/10)**.
- **Navegación/validación:** no es posible avanzar desde una pregunta sin contestar; las preguntas posteriores aparecen deshabilitadas hasta responder la actual. La navegación atrás/adelante conservó las respuestas seleccionadas.
- **Doble clic:** al confirmar **Finalizar evaluación** del módulo 1 con doble clic, el resultado fue un único intento (intento 1 de 3), sin duplicación visible.
- **Sesión en módulo 2:** al cerrar sesión con 4 de 10 respuestas y volver a entrar, las respuestas 1–4 permanecieron seleccionadas y la evaluación reanudó en la pregunta 4.
- **Diseño adaptable:** se inspeccionaron pantallas en escritorio y a 375 × 812 px. No hubo desplazamiento horizontal; las tarjetas se apilaron en móvil. El título se muestra legible en el retest (E2E-003 resuelto).
- **Documentos:** el PDF “Elecciones y democracia” abrió y se visualizó correctamente.
- **Constancia:** tras acreditar los tres módulos, el panel mostró **Curso completo** y **Generar Constancia**. Después de pulsarlo, la interfaz confirmó: “La constancia se generó y se envió a la descarga del navegador”. La descarga y los datos/formato del archivo no se pudieron inspeccionar: el navegador de pruebas no reportó un archivo descargado.
- **Video de prueba:** su duración reducida no se reporta como defecto. Para habilitar la evaluación se siguió el indicador visible que pide acumular 10 segundos.
- **Feedback exitoso:** al acreditar el módulo 1, la pantalla confirmó “Módulo aprobado”, calificación, respuestas correctas e intento.

## Pruebas pendientes de verificación

Quedaron **sin verificar**:

- contenido, nombre, curso, fecha y formato del archivo de constancia descargado;
- sesión expirada y comportamiento ante una interrupción de red.

Estos puntos no se reportan como aprobados ni como defectos confirmados.

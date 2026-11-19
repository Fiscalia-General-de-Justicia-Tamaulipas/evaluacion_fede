# Sistema maestro de diseño — Evaluación FEDE

> Fuente global para las vistas y componentes de la plataforma. Construido para software técnico de evaluación académica: precisión operativa, lectura editorial y mínima decoración. Las reglas de este archivo gobiernan nuevos desarrollos y refactorizaciones.

**Producto:** plataforma institucional de capacitación, certificación y evaluación.  
**Stack:** Vue 3, TypeScript, Vite, Tailwind CSS y Lucide Vue Next.  
**Usuarios:** personas adultas que estudian contenidos y responden evaluaciones de alto enfoque.  
**Dirección visual:** retícula limpia, superficies planas, bordes de 1 px, tipografía legible y estados inequívocos. Referencia de calidad: precisión de una herramienta profesional y claridad editorial, sin copiar marcas o estilos propietarios.

## Principios

1. **Evaluación primero:** la pregunta, sus incisos, el tiempo y el avance se leen sin competir con navegación o decoración.
2. **Jerarquía editorial:** títulos, metadatos y cuerpo se separan por escala tipográfica, peso y espacio; evitar depender de color.
3. **Precisión:** alinear contenido a una retícula común, usar cifras tabulares y mantener dimensiones estables durante interacciones.
4. **Una acción principal por vista:** secundarias subordinadas; acciones destructivas separadas y confirmadas cuando proceda.
5. **Accesibilidad funcional:** contraste AA, teclado completo, foco visible, estados semánticos y movimiento reducido.

## Paleta institucional

La interfaz estructural usa estrictamente `#575756`, `#878787` y `#dadada` sobre `#ffffff` y `#f7f7f7`. No añadir otros acentos, tonos ni neutros. Los colores semánticos existentes son una excepción exclusiva para alertas y validación.

| Token | Valor | Función |
|---|---|---|
| `--color-primary` | `#575756` | Acción primaria, texto principal, selección, foco y progreso |
| `--color-ink` | `#575756` | Títulos y texto normal de alto contraste |
| `--color-secondary` | `#878787` | Metadatos grandes y elementos secundarios no textuales; no usar en texto pequeño sobre fondos claros |
| `--color-control-border` | `#878787` | Límites de opciones, campos y controles interactivos |
| `--color-line` | `#dadada` | Divisores y bordes de superficies no interactivas |
| `--color-surface` | `#ffffff` | Tarjetas, preguntas, campos y encabezados |
| `--color-paper` | `#f7f7f7` | Fondo de aplicación y selección neutral |
| `--color-accent` | `#575756` | Alias de compatibilidad; no es un color adicional |
| `--color-accent-soft` | `#f7f7f7` | Alias neutral de superficie |
| `--color-focus` | `#575756` | Indicador de foco visible |

### Alertas y validación

Conservar sin cambio los tokens y estilos semánticos `success`, `info`, `warning` y `error` ya presentes. Solo aparecen en alertas/notificaciones y mensajes de validación relacionados. No usar estos colores en botones regulares, navegación, progreso, selección, encabezados o decoración. Todo estado incluye etiqueta o icono además del color.

### Accesibilidad del color

- `#575756` sobre blanco ofrece contraste suficiente para texto normal y foco.
- `#878787` sobre blanco o `#f7f7f7` no alcanza 4.5:1 para texto normal; reservarlo para metadatos grandes (al menos 24 px regular o 18.7 px negrita), iconos/bordes con función y otros elementos no textuales. En texto auxiliar pequeño usar `#575756`.
- `#dadada` tiene bajo contraste frente a blanco; limitarlo a divisores no interactivos. Los límites de controles usan `#878787`.
- El foco debe tener indicador de al menos 2 px con separación visible y 3:1 frente al entorno; se usa anillo de 3 px en `#575756`.
- La selección también cambia borde y presenta indicador/icono visible con semántica (`aria-checked` o `aria-pressed`); no se expresa solo mediante color.

## Tipografía y datos

- **Familia:** Inter, seguida por `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`. Mantener fallback local; el examen no depende de Google Fonts ni de red.
- **Pesos:** 400 cuerpo, 500 etiquetas, 600 secciones y acciones, 700 título principal. Evitar fuentes display o serif ornamentales.
- **Escala:** 12 / 14 / 16 / 18 / 20 / 24 / 30 / 36 px. Texto de pregunta y respuesta desde 16 px; metadatos mínimos 12 px, siempre con contraste suficiente.
- **Interlineado:** cuerpo 1.5–1.65; encabezados 1.15–1.3; controles 1.25–1.4.
- Texto editorial en líneas de aproximadamente 60–75 caracteres. Evitar truncar preguntas, instrucciones o contenido jurídico.
- Temporizador, puntaje, posición y contador usan `font-variant-numeric: tabular-nums` para que sus cifras no cambien de ancho.

## Retícula, espaciado y forma

Usar una escala de 4 px, priorizando múltiplos de 8 px. Mantener columnas y alineación constantes entre encabezado, pregunta, respuestas y acciones.

| Token | Valor | Uso |
|---|---:|---|
| `--space-1` | 4 px | Ajuste fino e icono con etiqueta |
| `--space-2` | 8 px | Espacio compacto y separación mínima de controles |
| `--space-3` | 12 px | Padding compacto |
| `--space-4` | 16 px | Espacio/padding base y gutter móvil |
| `--space-6` | 24 px | Padding de panel y grupo de campos |
| `--space-8` | 32 px | Separación de secciones |
| `--space-12` | 48 px | Separación amplia |
| `--space-16` | 64 px | Inicio de sección en escritorio |

- Lectura y resolución de examen: columna centrada de **760 px máximo** (`--exam-reading-width: 47.5rem`), fluida al ancho disponible.
- Gutter: 16 px en móvil, 24 px en tablet y 32 px en escritorio.
- Radios: 6 px para campos y opciones; 8 px para tarjetas, botones y diálogos. No superar 8 px.
- Bordes sólidos de 1 px. Sin degradados, glassmorphism, bordes decorativos, sombras grandes ni superficies translúcidas. Las sombras existentes deben ser imperceptibles y solo apoyar capas superpuestas.
- Breakpoints de revisión: 375, 768, 1024 y 1440 px. Evitar scroll horizontal y regiones de scroll anidadas.
- Controles táctiles: mínimo 44 × 44 px y separación de 8 px.

## Patrones específicos de evaluación

### Encabezado y temporizador

- Usar encabezado blanco `position: sticky` arriba, con línea inferior de 1 px `#dadada` y altura de referencia de 64 px. Reservar su espacio en el desplazamiento para que no oculte el control enfocado.
- Mantener a la vista identificación breve del examen/módulo, avance textual y temporizador. En móvil, reordenar o envolver; no comprimir texto hasta hacerlo ilegible.
- Temporizador alineado a cifras tabulares, con etiqueta accesible (“Tiempo restante”) y lectura completa por tecnología asistiva. Si cambia de estado, anunciarlo con texto; el color de alerta solo se usa al notificar una condición relevante.
- No hacer que el encabezado dependa de hover; mantener controles alcanzables por teclado.

### Progreso

- Barra minimalista de **3 px**, pista `#dadada` y avance `#575756`, sin gradientes ni animación que distraiga.
- Acompañar la barra con texto (“Pregunta 4 de 12”, porcentaje o paso actual); usar `role="progressbar"` y valores accesibles cuando represente progreso computable.
- No usar colores semánticos de alerta para progreso.

### Columna de pregunta

- Centrar pregunta, instrucciones y respuestas en una medida máxima de 760 px.
- Presentar primero el número/etiqueta de pregunta en metadatos y luego el enunciado como encabezado de nivel apropiado, seguido de instrucciones cuando existan.
- Dar separación vertical clara entre enunciado y grupo de respuestas. En móvil usar gutters de 16 px y conservar cuerpo de 16 px.

### Tarjetas de incisos

- Superficie blanca, borde de 1 px `#878787` para asegurar una frontera perceptible, radio de 6 px y objetivo de al menos 44 px de altura.
- Reposo: texto `#575756`. Hover, solo donde hay puntero: borde `#575756` y fondo `#f7f7f7`, sin cambiar dimensiones.
- Seleccionado: `aria-checked="true"`/`aria-pressed="true"`, borde reforzado en `#575756`, fondo `#f7f7f7` e indicador visible de selección (radio o check).
- Foco de teclado: outline de 3 px `#575756`, offset de 2–3 px; no quitar el outline para ningún método de entrada.
- Deshabilitado: atributo nativo o estado semántico, ausencia de acción y texto aún legible. No comunicarlo solo mediante opacidad.
- Aceptar texto largo y opciones multilinea; no fijar altura ni truncar respuestas.

## Componentes globales

### Acciones

- Primaria: fondo `#575756`, texto blanco, radio 8 px y altura mínima 44 px. Hover/pressed usan cambio neutro sin desplazamiento de layout.
- Secundaria: fondo blanco, texto `#575756`, borde `#878787` y foco visible.
- Terciaria: texto `#575756`, sin caja decorativa; mantener foco y objetivo táctil amplio.
- Colores semánticos reservados para acciones explícitamente destructivas si el sistema ya lo requiere y para la confirmación/validación contextual.

### Campos

- Etiqueta visible persistente, mínimo 44 px de alto y borde `#878787`; placeholder como ejemplo, no sustituto de etiqueta.
- En error, mostrar texto de causa/solución al lado del campo y vincular con `aria-describedby`; para varios errores usar resumen enfocable y enlaces.
- Foco siempre visible. Permitir pegar y autocompletar credenciales.

### Alertas, carga y estados vacíos

- Mantener colores semánticos actuales solo dentro de alertas y validación, con título/texto/icono y contraste legible.
- Carga breve con indicador; carga prolongada con skeleton o estado persistente que reserve espacio.
- Vacíos explican qué falta y el siguiente paso. Error de red debe ofrecer recuperación o reintento.

## Movimiento e iconografía

- Movimiento funcional y corto, normalmente 120–180 ms; sin transiciones de tamaño ni animación ornamental durante un examen.
- Respetar `prefers-reduced-motion`; conservar feedback de estado con animación reducida o estática.
- Usar la familia Lucide Vue Next en trazo consistente. Iconos decorativos junto a texto se ocultan del árbol accesible; botones solo con icono reciben nombre accesible.

## Tokens e implementación

- Fuente de tokens: `frontend/src/styles/index.css`. Usar variables semánticas; no definir colores aislados en vistas.
- Primitivas de examen disponibles: `.exam-header`, `.exam-header__timer`, `.exam-progress`, `.exam-progress__value`, `.exam-reading-column`, `.exam-option` y `.exam-option__indicator`.
- Los alias `--color-accent` y `--color-accent-soft` se conservan por compatibilidad y resuelven a los tonos institucionales permitidos.
- No cambiar contratos de navegación/API al aplicar estas reglas visuales.

## Antipatrones

- Degradados, glassmorphism, grandes sombras, radios mayores a 8 px o mosaicos de tarjetas sin función.
- Colores inventados en estructura, progreso/selección semántica aplicada fuera de alertas y validación, o estados comunicados solo con color.
- `#878787` para texto pequeño y `#dadada` para texto, foco o límite único de un control.
- Temporizador sin cifras tabulares, barra sin equivalente textual, encabezado sticky que tapa foco o respuestas truncadas.
- Dependencia de hover, iconos sin nombre accesible, targets pequeños y cambios de layout al seleccionar.

## Checklist por vista

- [ ] Estructura usa solo `#575756`, `#878787`, `#dadada`, blanco y `#f7f7f7`.
- [ ] Estados semánticos aparecen únicamente en alertas y validación.
- [ ] Preguntas dentro de columna máxima de 760 px; retícula responde desde 375 px.
- [ ] En examen, encabezado sticky mantiene temporizador tabular y progreso de 3 px con texto equivalente.
- [ ] Incisos tienen borde, foco y selección inequívocos, con semántica e indicador visible.
- [ ] Contraste AA, teclado, lectura ampliada, movimiento reducido y foco no obstruido.

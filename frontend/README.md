# Frontend de Evaluación Institucional

Aplicación de capacitación y evaluación modular. La plataforma tiene un catálogo de cursos, permite acceder a los tres módulos del curso actual y emite una constancia única cuando se acreditan todos.

## Estructura

```text
src/
  components/
    exam/       Resultado reutilizable y sus pruebas
    layout/     Header institucional con ambos logotipos
    ui/         Botón, tarjeta, alerta y estados base
  services/     Sesión/API y generación de PDF con QR
  styles/       Tokens globales, tipografía, foco y movimiento
  views/
    auth/       Inicio de sesión y registro
    certificates/ Verificación pública por folio
    courses/    Catálogo de cursos con avance
    exams/      Flujos de evaluación de módulos
    modules/    Panel y estados de módulos
  App.vue       Flujo de sesión, catálogo, módulos y evaluación
  main.ts       Montaje de Vue y ruta pública de verificación
```

La navegación existente de autenticación, catálogo, panel y módulos sigue coordinada por `App.vue`; Vue Router se usa para la ruta pública `/verificar/:folio`, que no requiere sesión. La sesión vive en `services/auth.ts`. Los módulos 2 y 3 comparten `ExamModuleView`; el módulo 1 conserva su flujo particular con material de apoyo.

## Diseño y accesibilidad

- Escala institucional definida en `src/styles/index.css`: `#575756`, `#878787`, `#dadada`, blanco y `#f7f7f7`; no se añaden colores de interfaz.
- Tokens Tailwind existentes; tipografía sans-serif de sistema, jerarquía por tamaño y peso, bordes y sombras discretas.
- Cards del panel con altura uniforme de 320 px y pie alineado al fondo.
- Lucide Vue Next para iconos. Es la librería instalada; shadcn.io la documenta en su catálogo de bibliotecas de iconos: https://www.shadcn.io/icons/libraries.
- Foco visible, enlace para saltar al contenido, roles `alert`/`status`, cabeceras institucionales con texto alternativo y movimiento reducido mediante `prefers-reduced-motion`.
- Transiciones de vista y estados de resultado breves; sin animaciones de partículas.
- Alertas persistentes con el patrón de shadcn (icono, título, descripción y acción opcional) y confirmación accesible antes de finalizar: foco controlado, Escape para cancelar y botones explícitos. Los mensajes de guardado, errores de API, registro y estado de acreditación usan el mismo componente.

## Flujos actuales

1. Inicio de sesión: `POST /api/auth/login`, persistencia de token y usuario.
2. Registro: carga de catálogos y envío a la ruta existente de registro.
3. Panel: `GET /api/modules/status`, reintento ante fallo y entrada secuencial. Solo queda habilitado el siguiente módulo pendiente; acreditar uno lo bloquea y habilita el siguiente. Al acreditar el tercero, todos quedan bloqueados y no se pueden repetir.
4. Evaluación: carga/recuperación, video obligatorio, inicio, guardado de respuesta y finalización.
5. Resultado por módulo: acreditación con mínimo 70/100 y hasta tres intentos; no emite una constancia individual.
6. Al aprobar los tres módulos, `POST /api/certificates/generate` crea o recupera el folio del curso. `pdf-lib` compone el PDF desde la plantilla institucional adjunta y `qrcode` añade el QR público. Solo se conserva la metadata de emisión; el PDF se vuelve a generar y descargar en cada solicitud.
7. La ruta pública `/verificar/:folio` consulta `GET /api/certificates/verify/{folio}` sin autenticar y presenta validez, folio, fecha, curso y datos no sensibles del usuario.
8. Cierre de sesión y expiración 401 limpian la sesión local.

Para bases de datos existentes, aplicar `alembic upgrade head` en el contenedor `api` para agregar los campos de folio y los índices únicos por folio/curso.

## Desarrollo y pruebas

Requiere Node.js 22 o compatible con Vite actual.

```bash
npm install
npm run dev
npm run build
npm test
npm run test:watch
```

Configura `VITE_API_URL` si la API no está en el mismo origen, por ejemplo `http://localhost:8000`.

La suite Vitest usa Vue Test Utils y jsdom. Incluye pruebas del componente Alert, diálogo de confirmación, extracción de errores/sesión y 401, umbral de acreditación y disponibilidad de reintentos, y el flujo de recuperación de examen en curso, guardado y finalización. No sustituye una prueba de navegador contra un backend real.

## Verificación visual manual

Revisar con viewport de 375×812, 768×1024 y 1440×900: login y registro, catálogo y avance, panel de módulos, modal de video, pregunta, resultado, descarga del PDF, escaneo del QR y estados válido/no válido/error de verificación. Comprobar zoom 200%, navegación solo con teclado y movimiento reducido. Ejecutar un examen con cuenta de prueba en backend para validar los contratos reales antes de publicar.

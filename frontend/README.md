# Frontend de Evaluación Institucional

Aplicación de capacitación y evaluación modular. La interfaz consume la API FastAPI existente y conserva sus rutas y contratos. No contiene administración de módulos ni exámenes porque esos flujos no existen en el frontend actual.

## Estructura

```text
src/
  components/
    exam/       Resultado reutilizable y sus pruebas
    layout/     Header institucional con ambos logotipos
    ui/         Botón, tarjeta, alerta y estados base
  services/     Sesión/API y constancia imprimible
  styles/       Tokens globales, tipografía, foco y movimiento
  views/
    auth/       Inicio de sesión y registro
    exams/      Flujos de evaluación de módulos
    modules/    Panel y estados de módulos
  App.vue       Navegación de pantalla existente por eventos
  main.ts       Montaje de Vue
```

La app no tenía Vue Router ni store central; para conservar el comportamiento y evitar una migración de arquitectura, la navegación de autenticación, panel y módulo sigue coordinada por `App.vue`. La sesión vive en `services/auth.ts`. Los módulos 2 y 3 comparten `ExamModuleView`; el módulo 1 conserva su flujo particular con material de apoyo.

## Diseño y accesibilidad

- Escala neutral existente: tinta `#202020`, carbón `#3e3e3e`, gris `#575756`, línea `#d2d2d1` y papel `#f5f5f4`.
- Tokens Tailwind en `src/styles/index.css`; tipografía de sistema con jerarquía por tamaño y peso; tarjetas de radio 1rem y sombra discreta.
- Cards del panel con altura uniforme de 320 px y pie alineado al fondo.
- Lucide Vue Next para iconos. Es la librería instalada; shadcn.io la documenta en su catálogo de bibliotecas de iconos: https://www.shadcn.io/icons/libraries.
- Foco visible, enlace para saltar al contenido, roles `alert`/`status`, cabeceras institucionales con texto alternativo y movimiento reducido mediante `prefers-reduced-motion`.
- Transiciones de vista y estados de resultado breves; sin animaciones de partículas.
- Alertas persistentes con el patrón de shadcn (icono, título, descripción y acción opcional) y confirmación accesible antes de finalizar: foco controlado, Escape para cancelar y botones explícitos. Los mensajes de guardado, errores de API, registro y estado de acreditación usan el mismo componente.

## Flujos actuales

1. Inicio de sesión: `POST /api/auth/login`, persistencia de token y usuario.
2. Registro: carga de catálogos y envío a la ruta existente de registro.
3. Panel: `GET /api/modules/status`, reintento ante fallo y entrada al módulo.
4. Evaluación: carga/recuperación, video obligatorio, inicio, guardado de respuesta y finalización.
5. Resultado: acreditación con mínimo 70/100, hasta tres intentos y constancia borrador imprimible.
6. Cierre de sesión y expiración 401 limpian la sesión local.

No se alteraron endpoints ni backend. Cuando la API no devuelve una constancia institucional formal, la vista imprimible conserva los datos entregados por la API y marca el documento como borrador.

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

Revisar con viewport de 375×812, 768×1024 y 1440×900: login y registro, panel (tres tarjetas en escritorio, una columna en móvil), header y logos dentro del módulo, modal de video, pregunta, resultado acreditado/no acreditado, error de API, zoom 200% y navegación solo con teclado. Comprobar el movimiento reducido desde la configuración del sistema operativo. Ejecutar un examen con cuenta de prueba en backend para validar los contratos reales antes de publicar.

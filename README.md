# Evaluación FEDE — FGJ Tamaulipas

Plataforma institucional de capacitación y evaluación para el curso **Delitos Electorales y su investigación en el contexto de los Procesos Electorales Locales**, Módulo 1.

## Stack
- FastAPI + SQLAlchemy + PostgreSQL
- Vue 3 + TypeScript + Tailwind CSS + Vite
- Docker Compose

## Arranque

```bash
docker compose up --build
```

Abrir `http://localhost:5173`.

API: `http://localhost:8000/docs`

## Video real
Reemplaza `frontend/public/demo.mp4` por el video institucional real, conservando ese nombre, o modifica el `source` en `frontend/src/App.vue`.

## Funcionalidad
- Video introductorio obligatorio.
- Botón de evaluación bloqueado hasta `ended`.
- Captura de nombre completo.
- Examen tipo slides, una pregunta por pantalla.
- Regreso a preguntas anteriores y modificación de respuestas.
- Indicador de progreso y mapa de preguntas.
- Persistencia de evaluación y respuestas en PostgreSQL.
- Calificación automática.
- Registro de inicio/finalización.

## Producción
Para producción conviene servir el frontend compilado detrás de Nginx y limitar CORS al dominio institucional. También se recomienda agregar autenticación administrativa, catálogo de cursos/módulos y un panel de resultados.

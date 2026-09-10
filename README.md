# Evaluación FEDE — FGJ Tamaulipas

Plataforma institucional de capacitación y evaluación para el curso **Delitos Electorales y su investigación en el contexto de los Procesos Electorales Locales**, Módulo 1.

## Stack
- FastAPI + SQLAlchemy + MySQL
- Vue 3 + TypeScript + Tailwind CSS + Vite
- Docker Compose

## Configuración local

Crea un archivo `.env` en la raíz del proyecto con estos valores:

```env
MYSQL_DATABASE=evaluacion_fede
MYSQL_USER=evaluacion
MYSQL_PASSWORD=evaluacion_secret
MYSQL_ROOT_PASSWORD=root_secret
DATABASE_URL=mysql+pymysql://evaluacion:evaluacion_secret@db:3306/evaluacion_fede?charset=utf8mb4
CORS_ORIGINS=http://localhost:5173
```

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
- Persistencia de evaluación y respuestas en MySQL.
- Calificación automática.
- Registro de inicio/finalización.

## Producción
Para producción conviene servir el frontend compilado detrás de Nginx y limitar CORS al dominio institucional. También se recomienda agregar autenticación administrativa, catálogo de cursos/módulos y un panel de resultados.

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

## Frontend

La documentación de estructura, diseño, flujos, ejecución y pruebas del cliente está en [`frontend/README.md`](frontend/README.md). Los videos por módulo están en `frontend/public/curso-modulo1.mp4`, `curso-modulo2.mp4` y `curso-modulo3.mp4`.

## Producción
Para producción conviene servir el frontend compilado detrás de Nginx y limitar CORS al dominio institucional. También se recomienda agregar autenticación administrativa, catálogo de cursos/módulos y un panel de resultados.

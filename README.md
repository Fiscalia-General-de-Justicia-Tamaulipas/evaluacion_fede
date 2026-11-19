# Evaluación FEDE — FGJ Tamaulipas

Plataforma institucional de capacitación y evaluación para el curso **Delitos Electorales y su investigación en el Sistema Electoral Mexicano**, integrado por tres módulos.

## Stack
- FastAPI + SQLAlchemy + MySQL
- Vue 3 + TypeScript + Tailwind CSS + Vite
- Vue Router para la verificación pública; `pdf-lib` y `qrcode` para generar la constancia en el navegador
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

Si cambian las dependencias del frontend y Vite no encuentra un paquete incluido en `package-lock.json`, renueva el volumen anónimo de `node_modules` del contenedor:

```bash
docker compose up --build --force-recreate --renew-anon-volumes frontend
```

El volumen anterior puede persistir entre reconstrucciones y ocultar los paquetes instalados en la nueva imagen.

En instalaciones existentes, aplicar las migraciones de base de datos después de iniciar el servicio:

```bash
docker compose exec api alembic upgrade head
```

Después, cargar el catálogo de estados y municipios de México (32 estados y 2,478 municipios del INEGI):

```bash
docker compose exec api python -m app.seed_locations
```

El seeder es idempotente y se puede volver a ejecutar sin duplicar registros. En el registro, el municipio se carga al seleccionar el estado.

La constancia se habilita al acreditar los tres módulos. La API conserva el folio y la fecha de emisión; el PDF y su QR se componen de nuevo en el navegador en cada solicitud y no se almacenan. La ruta pública de verificación es `/verificar/<folio>`.

## Recuperación de contraseña

El backend envía el enlace con la API institucional de correo. Configura estas variables en `.env`; `FRONTEND_URL` debe ser el origen público donde se sirve la aplicación:

```env
MAIL_HOST=https://api-correos.fgjtam.gob.mx/api/v1/send-email
MAIL_FROM_ADDRESS=notificaciones@fgjtam.gob.mx
MAIL_JWT=<token-vigente-de-la-API-de-correo>
FRONTEND_URL=http://localhost:5174
PASSWORD_RESET_EXPIRE_MINUTES=30
```

El token de correo permanece únicamente en el backend. Los enlaces de recuperación vencen según `PASSWORD_RESET_EXPIRE_MINUTES` (30 minutos por defecto) y se pueden usar una sola vez.

## Frontend

La documentación de estructura, diseño, flujos, ejecución y pruebas del cliente está en [`frontend/README.md`](frontend/README.md). Los videos por módulo están en `frontend/public/curso-modulo1.mp4`, `curso-modulo2.mp4` y `curso-modulo3.mp4`.

## Producción
Para producción conviene servir el frontend compilado detrás de Nginx y limitar CORS al dominio institucional. Configura el fallback de la SPA (`try_files $uri /index.html;`) para que la ruta de verificación del QR funcione al abrirse directamente. También se recomienda agregar autenticación administrativa y un panel de resultados.

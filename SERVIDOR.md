# Guía del Servidor — Biblioteca Horas Sociales

El servidor corre exclusivamente sobre **Docker Compose**. No hay soporte para
instalación nativa (venv, systemd, etc.) — todo el ciclo de vida se maneja
con `docker compose`.

---

## Requisitos

- Docker
- Docker Compose (plugin `docker compose` o `docker-compose`)

---

## Configuración

Copiar el archivo de ejemplo y completar los valores:

```bash
cp .env.example .env
```

| Variable | Descripción |
| --- | --- |
| `SECRET_KEY` | Clave JWT — usar una cadena larga y aleatoria |
| `ADMIN_USER` | Usuario del panel |
| `ADMIN_PASS` | Contraseña del panel |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario de la base de datos |
| `DB_PASSWORD` | Contraseña del usuario de la base de datos |
| `MYSQL_ROOT_PASSWORD` | Contraseña root de MySQL (usada solo por el contenedor `db`) |

`.env` está en `.gitignore` — nunca se commitea.

> **Nota:** `SECRET_KEY` no está en `.env.example` pero sí se lee en
> `docker-compose.yml` y en `servidor/routers/auth.py`. Si no se define,
> el código cae en un valor por defecto inseguro — agregarla a `.env`
> antes de exponer el servicio a la red.

---

## Levantar el servidor

Desde la raíz del repo (donde está `docker-compose.yml`):

```bash
docker compose up -d --build
```

Esto levanta dos contenedores:

- `servidor`: la API FastAPI (puerto interno y de host 8000), construida desde
  `servidor/Dockerfile` (imagen `python:3.12-slim`)
- `db`: MySQL 8.4, expuesto en el puerto 3306 del host

**URLs (desde cualquier PC de la red local):**

- API: `http://<ip-del-servidor>:8000`
- Docs interactivos: `http://<ip-del-servidor>:8000/docs`
- Panel: `http://<ip-del-servidor>:8000/panel`

El puerto de host está fijado en `"8000:8000"` en `docker-compose.yml`
precisamente para que esta URL no cambie entre reinicios: es la dirección
que cada PC del laboratorio usa para llegar al panel, así que un puerto
aleatorio rompería el acceso desde todas ellas en cada `down`/`up`.

La IP del servidor sí puede cambiar si la asigna DHCP. Para evitar tener que
reconfigurar cada PC, reservar una IP fija para el servidor en el router
(DHCP reservation) o asignarle una IP estática en el host.

---

## Estructura del código (`servidor/`)

```
servidor/
├── main.py            # App FastAPI: monta routers, panel estático y /health
├── routers/            # auth, sync, estudiantes, reportes, estado
├── models/             # Esquemas Pydantic (request/response)
├── db/                 # Acceso a MySQL (PyMySQL) + creación de tablas
├── panel/               # Frontend estático (HTML/CSS/JS vanilla) servido en /panel
├── Dockerfile
└── requirements.txt
```

`db/connection.py` envuelve `pymysql` para exponer una interfaz tipo
`sqlite3` (`conn.execute`, `conn.executescript`). `db/schema.py` crea las
tablas (`CREATE TABLE IF NOT EXISTS`) en el evento `startup` de FastAPI —
no hay sistema de migraciones, los cambios de esquema se editan
directamente ahí.

---

## Endpoints

Login (JWT, `python-jose`, expira en 24h):

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/auth/login` | Devuelve `{access_token, token_type}` |

Sincronización desde las PCs del laboratorio:

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/sync` | Recibe `pc_id`, `pc_nombre`, `ip`, lista de `sesiones` |
| `POST` | `/estado` | Reporta estado en vivo de una PC (sesión activa, estudiante) |
| `GET` | `/estado` | Lista el último estado reportado por cada PC |

PCs y mantenimiento:

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/pcs` | Lista PCs con fecha del último mantenimiento y minutos de uso acumulados desde entonces (`minutos_uso_desde_mantenimiento`) |
| `POST` | `/pcs/{pc_id}/mantenimiento` | Marca que se realizó mantenimiento ahora (reinicia el contador de uso) |

CRUD de estudiantes:

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/estudiantes` | Crea (409 si el carnet ya existe) |
| `GET` | `/estudiantes` | Lista todos |
| `GET` | `/estudiantes/{carnet}` | Obtiene uno (404 si no existe) |
| `PUT` | `/estudiantes/{carnet}` | Actualiza |
| `DELETE` | `/estudiantes/{carnet}` | Elimina (409 si tiene sesiones registradas) |

Reportes para el panel:

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/reportes/sesiones` | Filtra por `fecha`, `pc_id`, `carnet`, `carrera`; paginado (`limit`/`offset`) |
| `GET` | `/reportes/pcs-activas` | PCs con sesión activa en este momento |
| `GET` | `/reportes/resumen-dia` | Totales del día (por defecto, hoy) |
| `GET` | `/reportes/estadisticas` | Estadísticas agregadas en un rango `desde`/`hasta` |

Otros:

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/health` | Usado para healthchecks |
| `GET` | `/panel` | Sirve el frontend estático (`panel/index.html`) |

Documentación interactiva completa (todos los esquemas de request/response)
en `/docs` (Swagger UI, autogenerado por FastAPI).

CORS está abierto a cualquier origen (`allow_origins=["*"]`) para que el
panel y los scripts de sincronización de las PCs puedan llamar a la API
desde cualquier dirección de la red local.

---

## Logs

```bash
docker compose logs -f servidor
```

---

## Detener / reiniciar

```bash
docker compose stop        # detener
docker compose restart     # reiniciar
docker compose down        # detener y eliminar contenedores (conserva el volumen db_data)
```

---

## Actualizar tras cambios de código

```bash
docker compose up -d --build
```

---

## Base de datos

MySQL, corriendo en el servicio `db` de `docker-compose.yml`, persistida en
el volumen nombrado `db_data` (ruta dentro del contenedor:
`/var/lib/mysql`). Credenciales y nombre de base definidos por `DB_NAME`,
`DB_USER`, `DB_PASSWORD` y `MYSQL_ROOT_PASSWORD` en `.env`.

Tablas: `estudiantes`, `pcs`, `sesiones`, `estado_pcs`.

`sesiones.carnet` acepta `NULL`: una sesión sin carnet es de un **invitado**
(alguien que no es estudiante) — solo se guardan `pc_id`, `hora_inicio` y
`hora_fin`, sin datos personales. `pcs.ultimo_mantenimiento` guarda la fecha
del último mantenimiento reportado vía `POST /pcs/{pc_id}/mantenimiento`;
`GET /pcs` calcula el tiempo de uso acumulado desde esa fecha (suma de
duraciones de sesiones, incluida la sesión activa si la hay) como referencia
para saber cuándo corresponde el próximo mantenimiento.

### Backup

```bash
docker compose exec db sh -c 'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > biblioteca.bak.sql
```

### Inspeccionar el volumen

```bash
docker volume inspect biblioteca_db_data
```

---

## Credenciales

Definidas por `ADMIN_USER` / `ADMIN_PASS` en `.env`. Si no se definen, el
código cae en defaults inseguros (`admin` / `biblioteca2026`,
`SECRET_KEY` de ejemplo) — **siempre** completar `.env` antes de exponer el
servicio a la red.

Endpoint de login:

```bash
curl -X POST http://<host>:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password"}'
```

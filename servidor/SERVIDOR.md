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
| `CLOUDFLARE_TUNNEL_TOKEN` | Token del túnel de Cloudflare (ver abajo) |

`.env` está en `.gitignore` — nunca se commitea.

---

## Levantar el servidor

Desde la raíz del repo (donde está `docker-compose.yml`):

```bash
docker compose up -d --build
```

Esto levanta dos contenedores:

- `servidor`: la API FastAPI (puerto interno 8000)
- `cloudflared`: túnel hacia internet usando `CLOUDFLARE_TUNNEL_TOKEN`

**URLs (dentro de la red del servidor o vía el hostname configurado en el
túnel):**

- API: `http://<host>:8000`
- Docs interactivos: `http://<host>:8000/docs`
- Panel: `http://<host>:8000/panel`

El puerto se publica sin fijar el puerto de host (`"8000"` en
`docker-compose.yml`), así que Docker asigna uno dinámico. Para exponerlo en
un puerto fijo del host, cambiar a `"8000:8000"` en `docker-compose.yml`.

---

## Logs

```bash
docker compose logs -f servidor
docker compose logs -f cloudflared
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

SQLite, persistida en el volumen nombrado `db_data` (ruta dentro del
contenedor: `/app/data/biblioteca.db`, definida por `DB_PATH`).

Tablas: `estudiantes`, `pcs`, `sesiones`.

### Backup

```bash
docker compose exec servidor cp /app/data/biblioteca.db /app/data/biblioteca.db.bak
docker cp $(docker compose ps -q servidor):/app/data/biblioteca.db.bak ./biblioteca.db.bak
```

### Inspeccionar el volumen

```bash
docker volume inspect bliblioteca_db_data
```

---

## Túnel Cloudflare (acceso externo)

El túnel corre como contenedor (`cloudflared`) usando autenticación por
token, no requiere `cloudflared` instalado en el host ni archivos de
configuración locales.

1. Crear el túnel desde el dashboard de Cloudflare Zero Trust
   (Networks → Tunnels → Create a tunnel → Docker).
2. Copiar el token generado a `CLOUDFLARE_TUNNEL_TOKEN` en `.env`.
3. Configurar el hostname público y la ruta al servicio interno
   (`http://servidor:8000`) desde el mismo dashboard — el enrutamiento se
   gestiona en Cloudflare, no en un archivo local.
4. `docker compose up -d` levanta el túnel automáticamente.

---

## Credenciales

Definidas por `ADMIN_USER` / `ADMIN_PASS` en `.env`. Si no se definen, el
código cae en defaults inseguros (`admin` / `biblioteca2024`,
`SECRET_KEY` de ejemplo) — **siempre** completar `.env` antes de exponer el
servicio a internet vía el túnel.

Endpoint de login:

```bash
curl -X POST http://<host>:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password"}'
```

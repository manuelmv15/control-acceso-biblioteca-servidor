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

`.env` está en `.gitignore` — nunca se commitea.

---

## Levantar el servidor

Desde la raíz del repo (donde está `docker-compose.yml`):

```bash
docker compose up -d --build
```

Esto levanta un contenedor:

- `servidor`: la API FastAPI (puerto interno y de host 8000)

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

### Backup

```bash
docker compose exec db sh -c 'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > biblioteca.bak.sql
```

### Inspeccionar el volumen

```bash
docker volume inspect bliblioteca_db_data
```

---

## Credenciales

Definidas por `ADMIN_USER` / `ADMIN_PASS` en `.env`. Si no se definen, el
código cae en defaults inseguros (`admin` / `biblioteca2024`,
`SECRET_KEY` de ejemplo) — **siempre** completar `.env` antes de exponer el
servicio a la red.

Endpoint de login:

```bash
curl -X POST http://<host>:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password"}'
```

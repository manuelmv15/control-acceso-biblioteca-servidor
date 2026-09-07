# Despliegue — Biblioteca Servidor

Documentación de desarrollo, parte 1 de 2. Para cómo está organizado el código, ver [`estructura.md`](./estructura.md). Para la guía de uso del panel, ver [`../usuario.md`](../usuario.md).

## Requisitos

- Docker + Docker Compose (recomendado), **o** Python 3.10+ y MySQL 8.4 accesible si se despliega sin Docker.
- Red local entre la PC maestra (donde corre este servidor) y las PCs hijas (kioscos de `biblioteca_cliente`).
- Opcional: túnel Cloudflare (`cloudflared/`, no incluido en este repo) para exponer el panel fuera de la red local sin abrir puertos.

## Opción recomendada: Docker Compose

Hay **dos archivos independientes**, ninguno se combina con el otro vía `-f`:

| Archivo | Uso | Diferencias clave |
|---|---|---|
| `docker-compose.yml` | Desarrollo (`docker compose up` por defecto) | Monta `./servidor` como volumen, `uvicorn --reload` (hot-reload sin rebuild), publica MySQL en `3307:3306` para conectarte con MySQL Workbench / `mysql` CLI |
| `docker-compose.prod.yml` | Producción (standalone) | No monta código (la imagen ya lo trae copiado), sin `--reload`, **no publica el puerto de MySQL** al host — `servidor` llega a `db` por la red interna de Compose |

Ambos levantan los mismos dos servicios:
- **`db`**: `mysql:8.4`, healthcheck vía `mysqladmin ping`, volumen persistente `db_data`, timezone `America/El_Salvador`.
- **`servidor`**: build desde `./servidor`, puerto `8000`, espera a que `db` esté `healthy`.

### Pasos

```bash
cp .env.example .env
```

Editar `.env` (ver tabla completa de variables más abajo). Como mínimo hay que rellenar:

- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `MYSQL_ROOT_PASSWORD`
- `SECRET_KEY` — **obligatoria**, viene vacía en el ejemplo (`openssl rand -hex 32`)
- `KIOSK_API_KEY` — **obligatoria**, compartida con todos los kioscos (`openssl rand -hex 32`)

`ADMIN_USER`/`ADMIN_PASS_HASH` ya traen un valor de ejemplo (contraseña inicial `cambiar-esta-contrasena`). Se puede dejar así y cambiar la contraseña desde el panel en el primer login, o generar un hash inicial propio sin exponer la contraseña a quien despliega:

```bash
python3 servidor/generar_hash_admin.py
```

Levantar los contenedores:

```bash
# desarrollo
docker compose up -d --build

# producción
docker compose -f docker-compose.prod.yml up -d --build
```

El backend queda disponible en `http://localhost:8000`, el panel en `http://localhost:8000/` o `/panel`.

### Datos de demostración (opcional)

Para poblar estudiantes, PCs, hardware, estado en vivo y sesiones históricas de ejemplo (útil para ver tablas/gráficos sin cargar datos reales):

```bash
docker compose exec -T servidor python seed_demo.py --reset
```

`--reset` repite la demo desde cero.

## Opción alternativa: local sin Docker

Requiere un MySQL accesible. Variables con default en `servidor/db/connection.py`: `DB_HOST=localhost`, `DB_PORT=3306`, usuario/contraseña `biblioteca`.

```bash
cd servidor
pip install -r requirements.txt
uvicorn main:app --reload
```

## Variables de entorno (`.env`)

| Variable | Obligatoria | Descripción |
|---|---|---|
| `ADMIN_USER` | Sí | Usuario admin inicial. Solo se usa una vez para sembrar el primer administrador en la BD si la tabla `admins` está vacía; después el admin cambia su contraseña desde el panel y este valor deja de importar. |
| `ADMIN_PASS_HASH` | Sí | Hash PBKDF2-HMAC-SHA256 (`pbkdf2_sha256$<iter>$<salt>$<hash>`, 600 000 iteraciones) de la contraseña inicial. **No es texto plano.** Generar con `python3 servidor/generar_hash_admin.py`. |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Sí | Credenciales de la base de datos MySQL. |
| `MYSQL_ROOT_PASSWORD` | Sí | Contraseña root del contenedor MySQL. |
| `SECRET_KEY` | Sí | Firma de los JWT. Viene vacía en `.env.example` — si se deja vacía, Docker Compose la expande como cadena vacía (no ausente) y el fallback hardcodeado del código **no** se activa: el JWT queda firmado con secreto vacío. Generar con `openssl rand -hex 32`. |
| `KIOSK_API_KEY` | Sí | API key compartida por todos los kioscos (header `X-Kiosk-Key`), distinta de `SECRET_KEY`. Debe coincidir con `[servidor] kiosk_key` en `config.ini` de cada `biblioteca_cliente`. Si queda vacía, esa vía de auth queda siempre cerrada. |
| `CORS_ORIGINS` | No | Orígenes separados por coma para acceso cross-origin. Vacío = sin CORS extra (el panel se sirve desde el mismo origen que la API). |
| `LOGIN_MAX_INTENTOS` | No | Default 5. Intentos fallidos de `/auth/login` antes de bloquear temporalmente la IP. |
| `LOGIN_BLOQUEO_MINUTOS` | No | Default 15. Minutos de bloqueo tras exceder `LOGIN_MAX_INTENTOS`. |
| `TRUSTED_PROXIES` | No | IPs separadas por coma de reverse proxies/túneles de confianza (p. ej. Cloudflare Tunnel) autorizados a fijar `X-Forwarded-For` con la IP real del cliente para el rate limiting de `/auth/login`. Vacío (default) = nunca se confía en el header, siempre se usa la IP de la conexión TCP directa. Solo hace falta si el servidor corre detrás de un proxy — si no, todas las conexiones legítimas compartirían la IP del proxy y un solo atacante podría bloquear a todos los administradores. |
| `MAX_BODY_SIZE_BYTES` | No | Default 5 000 000 (5MB). Límite de tamaño de body para `POST`/`PUT`/`PATCH`. |
| `SYNC_MAX_SESIONES` | No | Default 500. Máximo de sesiones por lote en `POST /sync`. |
| `TLS_CERT_PATH` / `TLS_KEY_PATH` | No (recomendado) | Rutas *dentro del contenedor* al certificado/clave del servidor. Vacías = uvicorn sirve HTTP plano. Ver sección **TLS** abajo. |
| `TLS_CERTS_DIR` | No | Default `./certs`. Carpeta en el **host** que `docker-compose.prod.yml` monta en `/certs` (solo lectura) dentro del contenedor — ahí es donde deben estar los archivos que apuntan `TLS_CERT_PATH`/`TLS_KEY_PATH`. |

## TLS (cifrado entre los kioscos y este servidor)

Sin TLS, la PII de estudiantes y el header `X-Kiosk-Key` que envían los kioscos viajan **en texto plano** por la LAN del laboratorio — cualquiera en la misma red puede leerlos o alterarlos en tránsito (hallazgo H1 del informe de auditoría de seguridad, `AUDITORIA.md`). `biblioteca_cliente` ya rehúsa arrancar con `SERVER_URL` en `http://` hacia un host que no es `localhost`, salvo que se asuma el riesgo a propósito — ver su `docs/desarrollo/despliegue.md`.

Como el servidor normalmente solo tiene una IP de LAN (sin dominio público), no aplica una CA pública tipo Let's Encrypt. `servidor/scripts/generar_ca.sh` genera una **CA interna propia** y un certificado para la IP del servidor:

```bash
cd servidor
./scripts/generar_ca.sh 192.168.x.x      # IP real de la PC maestra en la LAN
```

Esto crea, en `<raíz del repo>/certs/` (junto a este `docker-compose.prod.yml`, gitignored — **nunca se versiona**):

| Archivo | Qué es | A dónde va |
|---|---|---|
| `ca.key` | Clave privada de la CA | Guardarla offline (USB, gestor de contraseñas). No hace falta en el servidor una vez generado `server.pem`. |
| `ca.pem` | Certificado público de la CA | Copiar a `cliente/ca.pem` en **cada uno de los 16 kioscos** — `config.ini` → `[servidor] ca_cert`. |
| `server.key` | Clave privada del servidor | Queda en la PC maestra. `TLS_KEY_PATH` en el `.env`. |
| `server.pem` | Certificado del servidor, firmado por la CA | `TLS_CERT_PATH` en el `.env`. |

En el `.env` del servidor:

```
TLS_CERT_PATH=/certs/server.pem
TLS_KEY_PATH=/certs/server.key
```

(`/certs` es la ruta *dentro del contenedor* — `docker-compose.prod.yml` monta `TLS_CERTS_DIR`, default `./certs`, ahí adentro.) Al levantar `docker compose -f docker-compose.prod.yml up -d --build` con esas variables configuradas, `servidor/docker-entrypoint.sh` le agrega automáticamente `--ssl-certfile`/`--ssl-keyfile` a `uvicorn`.

El certificado del servidor vence en ~825 días (2.25 años) — no hay renovación automática como con una CA pública, calendarizarla (volver a correr `generar_ca.sh` reusando la misma CA, o el script completo si también hace falta rotar la CA).

`docker-compose.yml` (desarrollo) no necesita nada de esto: corre sobre `localhost`, que sí está permitido en `http://` sin restricción.

## Checklist de seguridad antes de producción

- [ ] `SECRET_KEY` rellena con un valor fuerte y aleatorio (no vacía).
- [ ] `KIOSK_API_KEY` rellena y coincide con la de cada kiosko desplegado.
- [ ] `ADMIN_PASS_HASH` cambiado desde el valor de ejemplo, o contraseña cambiada desde el panel en el primer login.
- [ ] Desplegado con `docker-compose.prod.yml`, no con el de desarrollo (evita `--reload` y exponer el puerto de MySQL).
- [ ] `CORS_ORIGINS` configurado solo si el panel se sirve desde un origen distinto a la API (no es necesario por defecto).
- [ ] `TLS_CERT_PATH`/`TLS_KEY_PATH` configuradas (ver sección **TLS**) y `ca.pem` distribuido a los 16 kioscos — si se decide operar sin TLS a propósito, confirmar que cada `config.ini` tiene `permitir_http_inseguro = true` fijado conscientemente, no por omisión.
- [ ] Si se expone fuera de la red local, hacerlo vía túnel Cloudflare (`cloudflared/`) en lugar de abrir puertos directamente.

Detalle completo del modelo de amenazas y remediaciones aplicadas: `AUDITORIA.md`, en la raíz del workspace (`~/Proyectos/blibliteca_project`, junto a este repo y a `biblioteca_cliente`) — ese es el único registro de amenazas que existe hoy; una referencia previa a un `servidor/docs/security-testing-log.md` que nunca llegó a comitearse fue retirada de esta guía y del README (hallazgo H10 de `AUDITORIA.md`).

## Orden de despliegue del sistema completo

Este servidor es la mitad "PC maestra" del sistema. El otro componente (`biblioteca_cliente`) se instala en cada PC hija:

```
1. Desplegar este servidor en la PC maestra (pasos de arriba)
2. Anotar la IP local de la PC maestra
3. En cada PC hija: clonar biblioteca_cliente, pip install -r requirements.txt, python setup.py
   (usar la IP de la PC maestra + la misma KIOSK_API_KEY configurada acá)
4. Probar con 2-3 PCs antes de desplegar todas
5. Verificar en el panel admin (pestaña "PCs") que llegan las sesiones y el heartbeat de hardware
6. (Opcional) túnel Cloudflare para acceso externo al panel
```

Guía de instalación del cliente: ver `biblioteca_cliente/docs/desarrollo/despliegue.md`.

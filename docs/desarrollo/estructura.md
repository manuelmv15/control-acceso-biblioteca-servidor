# Estructura del proyecto — Biblioteca Servidor

Documentación de desarrollo, parte 2 de 2. Para cómo desplegar, ver [`despliegue.md`](./despliegue.md). Para la guía de uso del panel, ver [`../usuario.md`](../usuario.md).

## Qué problema resuelve

- Saber **qué estudiante usa qué PC y durante cuánto tiempo**, incluyendo un modo "invitado" para personal no estudiantil (administrativo, docente, visitante) sin carnet.
- Permitir que los kioscos de cada PC funcionen **sin conexión continua**: acumulan sesiones localmente y las sincronizan por lotes cuando hay red (`/sync`).
- Mostrar en **tiempo real** qué PCs están libres o en uso (`/estado`).
- Recibir **telemetría de hardware** de cada PC (specs, temperatura, salud de disco, horas de encendido) para anticipar mantenimiento preventivo.
- Generar **reportes y estadísticas** de uso (día, hora, carrera, facultad, sexo, PC).
- Servir un **panel web** de administración para todo lo anterior.

## Arquitectura y stack

- **FastAPI** + **Pydantic** sobre **Uvicorn** (ASGI).
- **MySQL 8.4** accedido con **SQL crudo** vía `PyMySQL` (sin ORM).
- **JWT** (`python-jose`) para el login del panel administrativo.
- **Docker Compose** para orquestar servidor + base de datos.
- **Panel web**: HTML/CSS/JS vanilla sin build step, con **Chart.js** desde CDN solo en la vista de estadísticas.

Dependencias (`servidor/requirements.txt`): `fastapi`, `uvicorn[standard]`, `pydantic`, `python-jose[cryptography]`, `python-multipart`, `PyMySQL`.

## Estructura de carpetas

```
servidor/
├── main.py               # entry point: registra routers, CORS, monta el panel, /health
├── db/                    # acceso a datos (SQL crudo vía PyMySQL)
│   ├── connection.py       # ConnectionWrapper: envuelve PyMySQL con API estilo sqlite3
│   ├── schema.py            # DDL de todas las tablas + migraciones ad-hoc
│   ├── ESQUEMA.md            # diagrama ER y detalle de cada tabla (fuente de verdad: schema.py)
│   ├── estudiantes.py, pcs.py, sesiones.py, estado.py, hardware.py, reportes.py, umbrales.py, admins.py
├── models/                # esquemas Pydantic de entrada/salida
├── routers/               # endpoints FastAPI, uno por dominio
├── panel/                 # SPA estática (HTML/CSS/JS) servida en /panel y /
├── Dockerfile
└── requirements.txt
```

`servidor/routers/__init__.py` está vacío; los routers se importan explícitamente por submódulo en `main.py`.

## Modelo de datos

Diagrama ER completo y detalle campo por campo en [`servidor/db/ESQUEMA.md`](../../servidor/db/ESQUEMA.md) (dentro del código, fuente de verdad: `schema.py::init_db()`). Resumen de tablas, todas `ENGINE=InnoDB`:

| Tabla | Campos principales | Notas |
|---|---|---|
| `estudiantes` | `carnet` (PK), `nombre`, `fecha_nacimiento` (solo año, tipo `YEAR`), `carrera`, `facultad`, `sexo`, `fecha_registro` | El kiosko solo captura el año de nacimiento |
| `pcs` | `pc_id` (PK), `nombre`, `ultima_conexion`, `ip_reportada`, `ultimo_mantenimiento` | Identidad estable de cada PC física |
| `sesiones` | `id` (PK, **generado por el cliente**), `pc_id` (FK), `carnet` (FK, nullable → modo invitado), `hora_inicio`, `hora_fin` (NULL = en curso), `fecha`, `sincronizado`, `timestamp_sync` | Histórico autoritativo de uso |
| `estado_pcs` | `pc_id` (PK/FK), `pc_nombre`, `sesion_activa`, `carnet` (FK, `ON DELETE SET NULL`), `nombre`, `hora_inicio`, `ultima_actualizacion` | Snapshot en vivo, 1 fila por PC |
| `pcs_hardware` | `pc_id` (PK/FK), `hostname`, `mac_address`, `cpu`, `ram_total_mb`, `almacenamiento_total_gb`, `sistema_operativo`, `temperatura_cpu_c`, `disco_smart_ok`, `horas_uso_acumuladas`, `ultima_lectura` | Telemetría del agente de hardware del cliente |

`sesiones` no tiene `ON DELETE` en su FK a `estudiantes` — borrar un estudiante con sesiones asociadas falla con conflicto (`DELETE /estudiantes/{carnet}` → 409).

No hay sistema formal de migraciones (Alembic, etc.): los cambios de esquema son parches manuales idempotentes en `schema.py`, re-ejecutados en cada arranque del contenedor.

## Endpoints de la API

> 🔒 = requiere `Authorization: Bearer <token>` (obtenido en `/auth/login`), 401 si falta o es inválido. Los marcados **kiosko** son intencionalmente públicos porque el cliente de escritorio no maneja JWT.

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/auth/login` | pública | `{username, password}` → `{access_token, token_type}` |
| `PUT` | `/auth/password` | 🔒 | Cambiar contraseña propia del admin autenticado |
| `POST` | `/sync` | kiosko | Recibe lote de sesiones offline-first (upsert idempotente) |
| `POST` | `/estado` | kiosko | Heartbeat de estado en vivo de una PC |
| `GET` | `/estado` | 🔒 | Lista el estado en vivo de todas las PCs |
| `POST` | `/estudiantes` | 🔒 kiosko o admin | Registra estudiante (201, 409 si ya existe) |
| `GET` | `/estudiantes` | 🔒 solo admin | Lista completa |
| `GET` | `/estudiantes/{carnet}` | 🔒 kiosko o admin | 404 si no existe |
| `PUT` | `/estudiantes/{carnet}` | 🔒 kiosko o admin | Actualiza campos |
| `DELETE` | `/estudiantes/{carnet}` | 🔒 solo admin | 204, 409 si tiene sesiones (FK) |
| `GET` | `/pcs` | 🔒 | Lista de mantenimiento consolidada |
| `POST` | `/pcs/{pc_id}/mantenimiento` | 🔒 | Marca `ultimo_mantenimiento = now()` |
| `POST` | `/pcs/{pc_id}/hardware` | kiosko | Heartbeat de telemetría de hardware |
| `GET` | `/reportes/sesiones` | 🔒 | Filtros: `fecha`, `pc_id`, `carnet`, `carrera`, `limit` (≤5000), `offset` |
| `GET` | `/reportes/pcs-activas` | 🔒 | PCs con `ultima_conexion` en últimos 5 min |
| `GET` | `/reportes/resumen-dia` | 🔒 | Totales del día |
| `GET` | `/reportes/estadisticas` | 🔒 | Agregados por día/hora/carrera/facultad/sexo/PC, `desde`/`hasta` (default: últimos 30 días) |
| `GET` | `/health` | pública | `{"status": "ok"}` |
| `GET` | `/`, `/panel/*` | pública | Sirve el panel web estático |

Nota: `routers/pcs.py` y `routers/hardware.py` comparten el prefijo `/pcs` con tags distintos (intencional, las subrutas no colisionan). Solo `pcs.py` exige auth; `hardware.py` queda público (heartbeat del agente).

## Lógica de negocio no obvia

**Doble fuente de verdad para sesiones.** `estado_pcs` es un snapshot en vivo (se sobrescribe en cada heartbeat); `sesiones` es el histórico autoritativo, poblado async vía `/sync`. Una sesión puede estar activa en `estado_pcs` sin haberse sincronizado aún. Los reportes (`db/reportes.py`, `db/pcs.py::listar_mantenimiento`) hacen `UNION ALL` de ambas fuentes con `NOT EXISTS` para no contar dos veces una sesión ya cerrada en `sesiones`.

**Sincronización idempotente (`db/sesiones.py::registrar_sync`).** Cada sesión se inserta con `INSERT ... ON DUPLICATE KEY UPDATE`, donde `hora_fin`/`sincronizado`/`timestamp_sync` solo se sobrescriben si el nuevo `hora_fin` no es `NULL`. Permite reenviar la misma sesión (por su `id`, generado por el cliente) mientras sigue abierta, y cerrarla cuando llega con `hora_fin`. Fallos de upsert de estudiante se registran individualmente sin abortar el resto del lote.

**Upsert no destructivo de estudiantes.** `db/estudiantes.py::upsert_desde_sesion` (usado también en `db/estado.py`) usa `COALESCE(VALUES(x), x)` para no pisar datos existentes con valores nulos entrantes.

**Umbrales de mantenimiento (`db/umbrales.py`):**
- `< 300 h` → `"optimo"`
- `300–400 h` → `"pendiente"` (`UMBRAL_PENDIENTE_HORAS = 300`)
- `> 400 h` → `"critico"` (`UMBRAL_CRITICO_HORAS = 400`)

Estas horas son `horas_uso_acumuladas` (tiempo real de encendido, reportado por el agente de hardware del cliente), **distintas** de `minutos_uso_desde_mantenimiento` (suma de duraciones de sesiones desde el último mantenimiento) — el panel muestra ambas métricas juntas en la vista de PCs.

## Seguridad — resumen para desarrollo

Ver checklist operativo en [`despliegue.md`](./despliegue.md#checklist-de-seguridad-antes-de-producción). Puntos relevantes para quien toca código:

- `require_auth` (JWT, `routers/auth.py`) aplicado a nivel de router en `pcs.py`, `reportes.py`; solo a `GET` en `estado.py`; a `GET`/`DELETE` en `estudiantes.py`.
- `require_kiosk_or_admin` (`routers/auth.py`) acepta JWT de admin **o** header `X-Kiosk-Key` == `KIOSK_API_KEY`, usado en `POST/GET/PUT /estudiantes`.
- Credenciales de admin viven en la tabla `admins` (no en `.env`); `ADMIN_USER`/`ADMIN_PASS_HASH` solo siembran el primer admin si la tabla está vacía (`db/schema.py::_sembrar_admin_inicial`).
- `db/connection.py::ConnectionWrapper` envuelve PyMySQL con API estilo `sqlite3` (`.execute()`, `.executescript()`) para que el resto del código luzca uniforme. `executescript()` divide el SQL ingenuamente por `;` — suficiente para el DDL actual, no soportaría sentencias con `;` embebido.
- `sesiones.id` es generado y enviado por el cliente kiosko (no autoincremental), consistente con el patrón offline-first.
- `init_db()` corre en cada arranque (`@app.on_event("startup")`) y re-ejecuta las migraciones ligeras; están escritas para ser idempotentes.

## Panel web de administración (para quien lo modifica)

SPA sin build step servida como estáticos bajo `/panel` (y también en `/`). Login con usuario/contraseña de admin (token JWT en `sessionStorage`).

| Vista | Archivos | Contenido |
|---|---|---|
| Sesiones | `views/sesiones.html`, `js/sesiones.js` | Tabla del día con filtros, resumen, badge de PCs activas, export CSV, ticker de duración cada minuto, auto-refresh 30s. Invitados con badge amarillo |
| PCs | `views/pcs.html`, `js/pcs.js` | Grid de estado en vivo + tabla de mantenimiento con specs, badges óptimo/pendiente/crítico |
| Estudiantes | `views/estudiantes.html`, `js/estudiantes.js` | Tabla con búsqueda local, modal de alta/edición |
| Estadísticas | `views/estadisticas.html`, `js/estadisticas.js` | Chart.js desde CDN, rangos rápidos (7/30/90/365 días) o manuales |

`js/app.js` orquesta el ruteo entre tabs (fetch de fragmentos HTML) y el auto-refresh; `js/api.js` centraliza las llamadas HTTP con el token JWT y el manejo de 401. `js/cuenta.js` maneja el cambio de contraseña.

Paleta institucional UES en `style.css`: rojo escarlata `#8B0E13`, negro `#1A171B`.

## Otros detalles a tener en cuenta

- El archivo `biblioteca.db` en la raíz del repo está vacío, residuo de un prototipo anterior con SQLite — no forma parte del sistema activo (MySQL es el motor real).
- `.gitignore` revela piezas del ecosistema más amplio no incluidas en este repo: `cloudflared/` (túnel Cloudflare) y artefactos del cliente PyQt6 (`.pc_id`, `config.ini`, empaquetado Windows).
- El contrato de API completo (servidor ↔ cliente) también está documentado en el repo índice `biblioteca` (README), que enlaza ambos repos hermanos.

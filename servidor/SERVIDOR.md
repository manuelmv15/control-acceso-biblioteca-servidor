# Guía del Servidor — Biblioteca Horas Sociales

## Requisitos

```bash
pip install -r requirements.txt
```

---

## Levantar el servidor

### Desarrollo (con auto-reload)
```bash
cd servidor/
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Producción (sin reload)
```bash
cd servidor/
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Con credenciales personalizadas
```bash
ADMIN_USER=admin ADMIN_PASS=mi_password SECRET_KEY=clave_segura \
  python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**URLs:**
- API: http://localhost:8000
- Docs interactivos: http://localhost:8000/docs
- Panel (si existe): http://localhost:8000/panel

---

## Matar el servidor

### Si corre en terminal (foreground)
`Ctrl+C`

### Si corre en background
```bash
# encontrar PID
lsof -i :8000

# matar
kill <PID>

# o matar todo lo que usa el puerto 8000
kill $(lsof -t -i:8000)
```

---

## Restart

```bash
# matar
kill $(lsof -t -i:8000)

# esperar un momento y levantar de nuevo
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Instalar como servicio systemd (Linux — producción)

Instala el servidor para que arranque automáticamente con el sistema.

```bash
sudo bash instalar_servicio.sh
```

### Controlar el servicio
```bash
sudo systemctl start biblioteca      # levantar
sudo systemctl stop biblioteca       # apagar
sudo systemctl restart biblioteca    # restart
sudo systemctl status biblioteca     # ver estado y logs recientes
```

### Ver logs en tiempo real
```bash
journalctl -u biblioteca -f
```

### Cambiar credenciales en producción
Editar `/etc/systemd/system/biblioteca.service` y agregar/modificar:
```ini
Environment=ADMIN_USER=admin
Environment=ADMIN_PASS=password_seguro
Environment=SECRET_KEY=clave_muy_larga_y_aleatoria
```
Luego:
```bash
sudo systemctl daemon-reload
sudo systemctl restart biblioteca
```

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ADMIN_USER` | `admin` | Usuario del panel |
| `ADMIN_PASS` | `biblioteca2024` | Contraseña del panel |
| `SECRET_KEY` | `biblioteca-secret-key-change-in-production` | Clave JWT — **cambiar en producción** |
| `DB_PATH` | `biblioteca.db` | Ruta de la base de datos SQLite |

---

## Credenciales por defecto

```
Usuario: admin
Contraseña: biblioteca2024
```

Endpoint de login:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "biblioteca2024"}'
```

---

## Túnel Cloudflare (acceso externo)

Para exponer el servidor a internet:

```bash
bash setup_tunnel.sh
```

Requiere cuenta de Cloudflare. Abrirá el navegador para autenticación.

---

## Base de datos

SQLite en `biblioteca.db` (mismo directorio donde se ejecuta el servidor).

Tablas: `estudiantes`, `pcs`, `sesiones`.

Backup:
```bash
cp biblioteca.db biblioteca.db.bak
```

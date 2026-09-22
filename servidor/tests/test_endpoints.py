"""Tests end-to-end de las rutas HTTP reales de `main.py` vía `TestClient` —
a diferencia del resto de la suite, que llama funciones internas
directamente, estos hacen requests HTTP completos contra la app de FastAPI
(headers, cookies, códigos de estado, middlewares incluidos). La capa
`db.*` que cada router usa se reemplaza por dobles de prueba (monkeypatch):
ningún test de este archivo abre una conexión real a MySQL.

`TestClient` sin usarse como context manager (`with TestClient(app) as c`)
no dispara el evento `startup` de la app (no llama a `init_db()`) — por eso
`client()` no lo necesita como context manager. Igual se monkeypatchea
`main.init_db` como defensa en profundidad, para que un cambio futuro de
FastAPI/Starlette en ese comportamiento no le abra una conexión real a
MySQL a esta suite."""

from datetime import datetime

import main
import pytest
from db import admins as db_admins
from db import estado as db_estado
from db import hardware as db_hardware
from db import pcs as db_pcs
from db import sesiones as db_sesiones
from fastapi.testclient import TestClient
from routers import auth as auth_module

ADMIN_PASSWORD = "clave-correcta-del-admin"
ADMIN_HASH = auth_module.generar_hash(ADMIN_PASSWORD)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    return TestClient(main.app)


@pytest.fixture
def admin_sin_revocacion(monkeypatch):
    """`obtener_actualizado` con una fecha bien vieja: ningún token emitido en
    el test queda revocado por un cambio de password posterior (ver
    `_token_revocado` en routers/auth.py)."""
    monkeypatch.setattr(db_admins, "obtener_actualizado", lambda username: datetime(2000, 1, 1))


def _login(client, username="admin", password=ADMIN_PASSWORD):
    return client.post("/auth/login", json={"username": username, "password": password})


# --- SecurityHeadersMiddleware --------------------------------------------

def test_respuestas_incluyen_cabeceras_de_seguridad(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'self'" in r.headers["Content-Security-Policy"]
    # Ninguna de estas la usa el panel — se deshabilitan todas.
    assert "camera=()" in r.headers["Permissions-Policy"]
    assert "microphone=()" in r.headers["Permissions-Policy"]
    assert "geolocation=()" in r.headers["Permissions-Policy"]
    # No hay TLS en los tests (TLS_CERT_PATH/TLS_KEY_PATH no están seteadas):
    # anunciar HSTS acá sería una promesa falsa al navegador.
    assert "Strict-Transport-Security" not in r.headers


# --- POST /auth/login / logout / me --------------------------------------

def test_login_exitoso_devuelve_token_y_cookies_httponly_con_samesite(client, monkeypatch):
    monkeypatch.setattr(db_admins, "obtener_hash", lambda username: ADMIN_HASH)
    r = _login(client)
    assert r.status_code == 200
    assert r.json()["access_token"]

    set_cookie = r.headers.get_list("set-cookie")
    access_cookie = next(c for c in set_cookie if c.startswith("access_token="))
    csrf_cookie = next(c for c in set_cookie if c.startswith("csrf_token="))
    assert "HttpOnly" in access_cookie
    assert "samesite=strict" in access_cookie.lower()
    assert "HttpOnly" not in csrf_cookie  # el panel necesita leerla para reenviarla (X-CSRF-Token)


def test_login_con_password_incorrecta_devuelve_401(client, monkeypatch):
    monkeypatch.setattr(db_admins, "obtener_hash", lambda username: ADMIN_HASH)
    r = _login(client, password="incorrecta")
    assert r.status_code == 401


def test_login_bloquea_tras_max_intentos_fallidos_via_http(client, monkeypatch):
    monkeypatch.setattr(db_admins, "obtener_hash", lambda username: ADMIN_HASH)
    for _ in range(auth_module.LOGIN_MAX_INTENTOS):
        assert _login(client, password="incorrecta").status_code == 401
    r = _login(client, password=ADMIN_PASSWORD)  # ya ni una contraseña correcta la salva
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_me_sin_token_devuelve_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_con_bearer_token_devuelve_username(client, admin_sin_revocacion):
    token = auth_module.create_token({"sub": "admin", "role": "admin", "csrf": "x"})
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_flujo_cookie_login_me_logout(client, monkeypatch, admin_sin_revocacion):
    monkeypatch.setattr(db_admins, "obtener_hash", lambda username: ADMIN_HASH)
    assert _login(client).status_code == 200

    # El TestClient conserva las cookies entre requests: /auth/me debe
    # aceptar la sesión sin mandar ningún header Authorization a mano.
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == "admin"

    r = client.post("/auth/logout")
    assert r.status_code == 200
    assert client.get("/auth/me").status_code == 401


# --- PUT /auth/password: CSRF de doble-submit solo para sesión por cookie -

def test_cambiar_password_por_cookie_sin_csrf_header_da_403(client, monkeypatch, admin_sin_revocacion):
    monkeypatch.setattr(db_admins, "obtener_hash", lambda username: ADMIN_HASH)
    _login(client)
    r = client.put("/auth/password", json={"password_actual": ADMIN_PASSWORD, "password_nueva": "otra-clave-larga"})
    assert r.status_code == 403


def test_cambiar_password_por_cookie_con_csrf_header_correcto_funciona(client, monkeypatch, admin_sin_revocacion):
    monkeypatch.setattr(db_admins, "obtener_hash", lambda username: ADMIN_HASH)
    monkeypatch.setattr(db_admins, "actualizar_password", lambda username, nuevo_hash: None)
    _login(client)
    csrf = client.cookies.get("csrf_token")
    r = client.put(
        "/auth/password",
        json={"password_actual": ADMIN_PASSWORD, "password_nueva": "otra-clave-larga"},
        headers={"X-CSRF-Token": csrf},
    )
    assert r.status_code == 200


def test_cambiar_password_por_bearer_no_exige_csrf(client, monkeypatch, admin_sin_revocacion):
    monkeypatch.setattr(db_admins, "obtener_hash", lambda username: ADMIN_HASH)
    monkeypatch.setattr(db_admins, "actualizar_password", lambda username, nuevo_hash: None)
    token = auth_module.create_token({"sub": "admin", "role": "admin", "csrf": "irrelevante-por-bearer"})
    r = client.put(
        "/auth/password",
        json={"password_actual": ADMIN_PASSWORD, "password_nueva": "otra-clave-larga"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


# --- POST /sync: X-Kiosk-Key + X-PC-Id, y A1 (verificar_pc_id) -----------

def test_sync_sin_credencial_da_401(client):
    r = client.post("/sync", json={"pc_id": "PC-01", "sesiones": []})
    assert r.status_code == 401


def test_sync_con_api_key_de_otra_pc_da_403(client, monkeypatch):
    monkeypatch.setattr(auth_module.db_pcs, "obtener_api_key_hash", lambda pc_id: auth_module.hash_api_key("clave-pc01"))
    r = client.post(
        "/sync",
        json={"pc_id": "PC-02", "sesiones": []},  # reporta datos de OTRA pc
        headers={"X-Kiosk-Key": "clave-pc01", "X-PC-Id": "PC-01"},
    )
    assert r.status_code == 403


def test_sync_con_api_key_propia_funciona(client, monkeypatch):
    monkeypatch.setattr(auth_module.db_pcs, "obtener_api_key_hash", lambda pc_id: auth_module.hash_api_key("clave-pc01"))
    monkeypatch.setattr(db_sesiones, "registrar_sync", lambda payload, ip: {"ok": True, "insertados": 0})
    r = client.post(
        "/sync",
        json={"pc_id": "PC-01", "sesiones": []},
        headers={"X-Kiosk-Key": "clave-pc01", "X-PC-Id": "PC-01"},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True, "insertados": 0}


# --- POST /estado: mismas reglas de autorización que /sync ---------------

def test_estado_con_api_key_de_otra_pc_da_403(client, monkeypatch):
    monkeypatch.setattr(auth_module.db_pcs, "obtener_api_key_hash", lambda pc_id: auth_module.hash_api_key("clave-pc01"))
    r = client.post(
        "/estado",
        json={"pc_id": "PC-02", "sesion_activa": False},
        headers={"X-Kiosk-Key": "clave-pc01", "X-PC-Id": "PC-01"},
    )
    assert r.status_code == 403


def test_estado_con_api_key_propia_funciona(client, monkeypatch):
    monkeypatch.setattr(auth_module.db_pcs, "obtener_api_key_hash", lambda pc_id: auth_module.hash_api_key("clave-pc01"))
    monkeypatch.setattr(db_estado, "actualizar_estado", lambda payload: "2026-01-01T00:00:00")
    r = client.post(
        "/estado",
        json={"pc_id": "PC-01", "sesion_activa": True},
        headers={"X-Kiosk-Key": "clave-pc01", "X-PC-Id": "PC-01"},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True, "timestamp": "2026-01-01T00:00:00"}


def test_estado_get_requiere_admin(client):
    assert client.get("/estado").status_code == 401


# --- POST /pcs/{pc_id}/hardware: estado_mantenimiento con calcular_estado
#     REAL (no mockeado) sobre los umbrales de 300h/400h ------------------

@pytest.mark.parametrize(
    "horas,estado_esperado",
    [
        (0, "optimo"),
        (299.9, "optimo"),
        (300, "pendiente"),
        (400, "pendiente"),  # límite superior de "pendiente" es inclusive
        (400.1, "critico"),
        (1000, "critico"),
    ],
)
def test_reportar_hardware_calcula_estado_mantenimiento_real(client, monkeypatch, horas, estado_esperado):
    monkeypatch.setattr(auth_module.db_pcs, "obtener_api_key_hash", lambda pc_id: auth_module.hash_api_key("clave-pc01"))
    monkeypatch.setattr(db_hardware, "upsert_lectura", lambda pc_id, payload: None)
    monkeypatch.setattr(db_hardware, "obtener_ultimo_mantenimiento", lambda pc_id: None)
    r = client.post(
        "/pcs/PC-01/hardware",
        json={"horas_uso_acumuladas": horas},
        headers={"X-Kiosk-Key": "clave-pc01", "X-PC-Id": "PC-01"},
    )
    assert r.status_code == 200
    assert r.json()["estado_mantenimiento"] == estado_esperado


def test_reportar_hardware_de_otra_pc_da_403(client, monkeypatch):
    monkeypatch.setattr(auth_module.db_pcs, "obtener_api_key_hash", lambda pc_id: auth_module.hash_api_key("clave-pc01"))
    r = client.post(
        "/pcs/PC-02/hardware",
        json={"horas_uso_acumuladas": 10},
        headers={"X-Kiosk-Key": "clave-pc01", "X-PC-Id": "PC-01"},
    )
    assert r.status_code == 403


# --- /pcs/* (panel admin): requieren JWT de admin -------------------------

def test_listar_pcs_sin_token_da_401(client):
    assert client.get("/pcs").status_code == 401


def test_listar_pcs_con_token_admin_devuelve_lo_que_da_la_capa_db(client, monkeypatch, admin_sin_revocacion):
    monkeypatch.setattr(db_pcs, "listar_mantenimiento", lambda: [{"pc_id": "PC-01"}])
    token = auth_module.create_token({"sub": "admin", "role": "admin", "csrf": "x"})
    r = client.get("/pcs", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == [{"pc_id": "PC-01"}]


def test_registrar_mantenimiento_pc_inexistente_da_404(client, monkeypatch, admin_sin_revocacion):
    monkeypatch.setattr(db_pcs, "registrar_mantenimiento", lambda pc_id: False)
    token = auth_module.create_token({"sub": "admin", "role": "admin", "csrf": "x"})
    r = client.post("/pcs/PC-99/mantenimiento", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_generar_api_key_pc_devuelve_la_key_en_texto_plano_una_vez(client, monkeypatch, admin_sin_revocacion):
    monkeypatch.setattr(db_pcs, "obtener_api_key_hash", lambda pc_id: None)
    monkeypatch.setattr(db_pcs, "fijar_api_key", lambda pc_id, hash_: None)
    token = auth_module.create_token({"sub": "admin", "role": "admin", "csrf": "x"})
    r = client.post("/pcs/PC-01/api-key", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["pc_id"] == "PC-01"
    assert r.json()["api_key"]  # no vacía


def test_revocar_api_key_pc_inexistente_da_404(client, monkeypatch, admin_sin_revocacion):
    monkeypatch.setattr(db_pcs, "revocar_api_key", lambda pc_id: False)
    token = auth_module.create_token({"sub": "admin", "role": "admin", "csrf": "x"})
    r = client.delete("/pcs/PC-99/api-key", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404

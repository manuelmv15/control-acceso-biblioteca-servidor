"""Tests de `verificar_pc_id` (A1: una PC solo puede reportar sus propios
datos de estado/sesiones/hardware) y de las vías de `require_kiosk_or_admin`
que determinan qué `actor` recibe — en particular si trae o no un "pc_id"
propio, que es justo lo que `verificar_pc_id` mira. No se levanta base de
datos real: donde hace falta `db_pcs`/`db_admins`, se reemplaza (monkeypatch)
por un doble de prueba, igual que en test_auth.py."""

from datetime import datetime

import pytest
from _helpers import make_request
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from routers import auth


def _bearer(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


# --- verificar_pc_id -------------------------------------------------------

def test_verificar_pc_id_permite_si_la_pc_coincide():
    actor = {"role": "kiosk", "pc_id": "PC-01"}
    auth.verificar_pc_id(actor, "PC-01")  # no debe lanzar


def test_verificar_pc_id_bloquea_pc_ajena():
    actor = {"role": "kiosk", "pc_id": "PC-01"}
    with pytest.raises(HTTPException) as exc:
        auth.verificar_pc_id(actor, "PC-02")
    assert exc.value.status_code == 403


def test_verificar_pc_id_no_restringe_a_un_admin():
    actor = {"role": "admin", "sub": "admin"}
    auth.verificar_pc_id(actor, "PC-cualquiera")  # no debe lanzar, no es kiosko


def test_verificar_pc_id_no_restringe_a_la_key_compartida_sin_pc_propia():
    # Un actor autenticado con KIOSK_API_KEY (compatibilidad) no tiene un
    # "pc_id" propio asignado por require_kiosk_or_admin (ver más abajo), así
    # que no hay nada contra qué comparar y no debe bloquearse.
    actor = {"role": "kiosk", "sub": "kiosko"}
    auth.verificar_pc_id(actor, "PC-cualquiera")  # no debe lanzar


# --- require_kiosk_or_admin: qué actor produce cada vía de autenticación --

def test_require_kiosk_or_admin_con_api_key_propia_de_pc_da_pc_id(monkeypatch):
    monkeypatch.setattr(auth.db_pcs, "obtener_api_key_hash", lambda pc_id: auth.hash_api_key("secreta-de-pc01"))
    actor = auth.require_kiosk_or_admin(
        make_request(), credentials=None, x_kiosk_key="secreta-de-pc01", x_pc_id="PC-01",
    )
    assert actor == {"sub": "PC-01", "role": "kiosk", "pc_id": "PC-01"}


def test_require_kiosk_or_admin_rechaza_api_key_de_pc_incorrecta(monkeypatch):
    monkeypatch.setattr(auth.db_pcs, "obtener_api_key_hash", lambda pc_id: auth.hash_api_key("secreta-de-pc01"))
    monkeypatch.setattr(auth, "KIOSK_API_KEY", "")  # sin vía de compatibilidad
    with pytest.raises(HTTPException) as exc:
        auth.require_kiosk_or_admin(make_request(), credentials=None, x_kiosk_key="otra-cosa", x_pc_id="PC-01")
    assert exc.value.status_code == 401


def test_require_kiosk_or_admin_con_key_compartida_no_da_pc_id_propio(monkeypatch):
    monkeypatch.setattr(auth.db_pcs, "obtener_api_key_hash", lambda pc_id: None)  # PC sin key propia
    monkeypatch.setattr(auth, "KIOSK_API_KEY", "compartida-legacy")
    actor = auth.require_kiosk_or_admin(
        make_request(), credentials=None, x_kiosk_key="compartida-legacy", x_pc_id="PC-02",
    )
    assert actor == {"sub": "kiosko", "role": "kiosk"}
    assert "pc_id" not in actor  # por eso verificar_pc_id no la restringe (ver arriba)


def test_require_kiosk_or_admin_acepta_jwt_de_admin(monkeypatch):
    monkeypatch.setattr(auth.db_admins, "obtener_actualizado", lambda username: datetime(2000, 1, 1))
    token = auth.create_token({"sub": "admin", "role": "admin"})
    actor = auth.require_kiosk_or_admin(
        make_request(), credentials=_bearer(token), x_kiosk_key=None, x_pc_id=None,
    )
    assert actor["sub"] == "admin"
    assert actor["role"] == "admin"


def test_require_kiosk_or_admin_401_sin_ninguna_credencial():
    with pytest.raises(HTTPException) as exc:
        auth.require_kiosk_or_admin(make_request(), credentials=None, x_kiosk_key=None, x_pc_id=None)
    assert exc.value.status_code == 401

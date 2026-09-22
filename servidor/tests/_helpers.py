"""Utilidades compartidas entre archivos de test (no es un módulo de tests en
sí — no lleva el prefijo `test_`, así que pytest no lo colecciona).

`make_request` construye un `Request` real de Starlette a partir de un scope
ASGI mínimo, sin necesidad de un TestClient ni una app completa. Sirve para
las funciones de `routers/auth.py` que reciben un `Request` (`_client_ip`,
`limitar_lecturas_estudiante`, `limitar_escrituras_kiosko`,
`require_kiosk_or_admin`) y a las que los tests llaman directamente."""

from starlette.requests import Request


def make_request(ip="203.0.113.10", headers=None, cookies=None, method="GET", path="/"):
    header_list = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in (headers or {}).items()]
    if cookies:
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        header_list.append((b"cookie", cookie_header.encode("latin-1")))
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": header_list,
        "client": (ip, 12345),
    }
    return Request(scope)

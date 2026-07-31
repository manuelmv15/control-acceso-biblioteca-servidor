import hmac
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from models import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("uvicorn.error")


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(
            f"La variable de entorno {name} es obligatoria y no puede estar vacía. "
            f"Configúrala en tu .env antes de iniciar el servidor."
        )
    return value


SECRET_KEY = _require_env("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

ADMIN_USER = _require_env("ADMIN_USER")
ADMIN_PASS = _require_env("ADMIN_PASS")

KIOSK_API_KEY = os.environ.get("KIOSK_API_KEY", "")

LOGIN_MAX_INTENTOS = int(os.environ.get("LOGIN_MAX_INTENTOS") or 5)
LOGIN_BLOQUEO_SEGUNDOS = int(os.environ.get("LOGIN_BLOQUEO_MINUTOS") or 15) * 60

_intentos_fallidos: dict[str, dict] = {}


def _segundos_bloqueado(ip: str) -> Optional[int]:
    """Devuelve los segundos restantes de bloqueo para `ip`, o None si puede intentar login.
    Si el bloqueo ya expiró, limpia el registro (nueva ventana de intentos desde cero)."""
    entrada = _intentos_fallidos.get(ip)
    if not entrada:
        return None
    restante = entrada["bloqueado_hasta"] - time.time()
    if restante > 0:
        return int(restante) + 1
    if entrada["bloqueado_hasta"]:
        _intentos_fallidos.pop(ip, None)
    return None


def _registrar_intento_fallido(ip: str) -> None:
    entrada = _intentos_fallidos.setdefault(ip, {"fallos": 0, "bloqueado_hasta": 0.0})
    entrada["fallos"] += 1
    log.warning("Login fallido desde %s (intento %d/%d)", ip, entrada["fallos"], LOGIN_MAX_INTENTOS)
    if entrada["fallos"] >= LOGIN_MAX_INTENTOS:
        entrada["bloqueado_hasta"] = time.time() + LOGIN_BLOQUEO_SEGUNDOS
        log.warning("IP %s bloqueada por %d minutos tras exceder intentos de login", ip, LOGIN_BLOQUEO_SEGUNDOS // 60)


def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


_bearer_scheme = HTTPBearer(auto_error=False)


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> dict:
    """Dependencia FastAPI: exige `Authorization: Bearer <token>` válido, 401 si falta o no verifica."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    return verify_token(credentials.credentials)


def require_kiosk_or_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    x_kiosk_key: Optional[str] = Header(None, alias="X-Kiosk-Key"),
) -> dict:
    """Dependencia FastAPI: acepta JWT de admin (`Authorization: Bearer`) o la API key
    compartida de kiosko (`X-Kiosk-Key`). Si `KIOSK_API_KEY` no está configurada, esa vía
    queda siempre cerrada (nunca cae a un valor por defecto adivinable)."""
    if KIOSK_API_KEY and x_kiosk_key and hmac.compare_digest(x_kiosk_key, KIOSK_API_KEY):
        return {"sub": "kiosko", "role": "kiosk"}
    if credentials is not None:
        return verify_token(credentials.credentials)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere JWT de admin o API key de kiosko")


@router.post("/login", response_model=Token)
def login(req: LoginRequest, request: Request):
    ip = request.client.host if request.client else "desconocida"

    restante = _segundos_bloqueado(ip)
    if restante is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Intenta de nuevo en {restante // 60 + 1} minuto(s).",
            headers={"Retry-After": str(restante)},
        )

    if req.username != ADMIN_USER or req.password != ADMIN_PASS:
        _registrar_intento_fallido(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    _intentos_fallidos.pop(ip, None)
    token = create_token({"sub": req.username, "role": "admin"})
    return Token(access_token=token, token_type="bearer")

import hashlib
import hmac
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from db import admins as db_admins
from models import LoginRequest, Token, CambiarPasswordRequest

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


def _parsear_hash(hash_almacenado: str) -> tuple[int, bytes, str]:
    """Descompone un hash `pbkdf2_sha256$<iteraciones>$<salt_hex>$<hash_hex>`. Lanza ValueError si
    el formato no es válido (algoritmo distinto, número de campos incorrecto, hex inválido, etc.)."""
    algoritmo, iteraciones_s, salt_hex, hash_hex = hash_almacenado.split("$")
    if algoritmo != "pbkdf2_sha256":
        raise ValueError(f"algoritmo desconocido: {algoritmo}")
    return int(iteraciones_s), bytes.fromhex(salt_hex), hash_hex


def verificar_password(password: str, hash_almacenado: str) -> bool:
    """Verifica `password` contra un hash generado con `generar_hash()` (o con el script
    standalone `servidor/generar_hash_admin.py`). Nunca compara contraseñas en texto plano:
    así ni el `.env` ni la base de datos guardan la contraseña real, solo su hash."""
    try:
        iteraciones, salt, hash_hex = _parsear_hash(hash_almacenado)
    except (ValueError, AttributeError):
        return False
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iteraciones)
    return hmac.compare_digest(derivado.hex(), hash_hex)


PBKDF2_ITERACIONES = 600_000  # recomendación OWASP (2023+) para PBKDF2-HMAC-SHA256


def generar_hash(password: str) -> str:
    """Genera un hash `pbkdf2_sha256$<iteraciones>$<salt_hex>$<hash_hex>` para guardar en la
    tabla `admins`. Usado por `PUT /auth/password`; el script `generar_hash_admin.py` tiene su
    propia copia de esta lógica porque corre standalone, fuera del paquete de la app."""
    salt = secrets.token_bytes(16)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERACIONES)
    return f"pbkdf2_sha256${PBKDF2_ITERACIONES}${salt.hex()}${derivado.hex()}"


SECRET_KEY = _require_env("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

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

    hash_almacenado = db_admins.obtener_hash(req.username)
    if hash_almacenado is None or not verificar_password(req.password, hash_almacenado):
        _registrar_intento_fallido(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    _intentos_fallidos.pop(ip, None)
    token = create_token({"sub": req.username, "role": "admin"})
    return Token(access_token=token, token_type="bearer")


@router.put("/password")
def cambiar_password(req: CambiarPasswordRequest, usuario: dict = Depends(require_auth)):
    """Permite al administrador ya autenticado cambiar su propia contraseña. Así quien
    despliega la app puede fijar unas credenciales iniciales (`ADMIN_USER`/`ADMIN_PASS_HASH`
    en el `.env`, ver `db/schema.py`) sin que sean las que se usan a largo plazo: el
    administrador real las cambia acá después de su primer login, y desde ese momento el
    `.env` queda obsoleto — las credenciales viven solo en la base de datos."""
    username = usuario["sub"]
    hash_almacenado = db_admins.obtener_hash(username)
    if hash_almacenado is None or not verificar_password(req.password_actual, hash_almacenado):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña actual incorrecta")
    if len(req.password_nueva) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La nueva contraseña debe tener al menos 8 caracteres",
        )
    db_admins.actualizar_password(username, generar_hash(req.password_nueva))
    log.info("Contraseña de administrador '%s' actualizada", username)
    return {"ok": True}

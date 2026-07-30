import hmac
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from models import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.environ.get("SECRET_KEY", "biblioteca-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "biblioteca2026")

KIOSK_API_KEY = os.environ.get("KIOSK_API_KEY", "")


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
def login(req: LoginRequest):
    if req.username != ADMIN_USER or req.password != ADMIN_PASS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    token = create_token({"sub": req.username, "role": "admin"})
    return Token(access_token=token, token_type="bearer")

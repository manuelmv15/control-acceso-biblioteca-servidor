from fastapi import APIRouter, Depends
from db import estado as db_estado
from models import EstadoPayload
from routers.auth import require_auth, require_kiosk_or_admin

router = APIRouter(prefix="/estado", tags=["estado"])


@router.post("", dependencies=[Depends(require_kiosk_or_admin)])
def actualizar_estado(payload: EstadoPayload):
    timestamp = db_estado.actualizar_estado(payload)
    return {"ok": True, "timestamp": timestamp}


@router.get("", dependencies=[Depends(require_auth)])
def obtener_estados():
    return db_estado.listar_estados()

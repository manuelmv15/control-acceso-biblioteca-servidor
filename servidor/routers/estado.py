from db import estado as db_estado
from fastapi import APIRouter, Depends
from models import EstadoPayload

from routers.auth import limitar_escrituras_kiosko, require_auth, verificar_pc_id

router = APIRouter(prefix="/estado", tags=["estado"])


@router.post("")
def actualizar_estado(payload: EstadoPayload, actor: dict = Depends(limitar_escrituras_kiosko)):
    verificar_pc_id(actor, payload.pc_id)
    timestamp = db_estado.actualizar_estado(payload)
    return {"ok": True, "timestamp": timestamp}


@router.get("", dependencies=[Depends(require_auth)])
def obtener_estados():
    return db_estado.listar_estados()

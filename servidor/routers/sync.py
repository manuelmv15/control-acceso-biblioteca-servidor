from fastapi import APIRouter, Depends, Request
from db import sesiones as db_sesiones
from models import SyncPayload
from routers.auth import limitar_escrituras_kiosko, verificar_pc_id

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("")
def recibir_sync(payload: SyncPayload, request: Request, actor: dict = Depends(limitar_escrituras_kiosko)):
    verificar_pc_id(actor, payload.pc_id)
    ip = request.client.host if request.client else payload.ip
    return db_sesiones.registrar_sync(payload, ip)

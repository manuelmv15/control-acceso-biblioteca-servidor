from db import sesiones as db_sesiones
from fastapi import APIRouter, Depends, HTTPException, Request
from models import SyncPayload

from routers.auth import limitar_escrituras_kiosko, verificar_pc_id

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("")
def recibir_sync(payload: SyncPayload, request: Request, actor: dict = Depends(limitar_escrituras_kiosko)):
    verificar_pc_id(actor, payload.pc_id)
    # verificar_pc_id solo mira payload.pc_id, pero cada sesión se guarda con
    # su propio pc_id: sin esta comprobación una PC podría registrar sesiones
    # a nombre de otra.
    if any(s.pc_id != payload.pc_id for s in payload.sesiones):
        raise HTTPException(status_code=422, detail="Todas las sesiones deben pertenecer a payload.pc_id")
    ip = request.client.host if request.client else payload.ip
    return db_sesiones.registrar_sync(payload, ip)

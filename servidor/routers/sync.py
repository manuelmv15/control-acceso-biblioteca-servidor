from db import sesiones as db_sesiones
from fastapi import APIRouter, Depends, HTTPException, Request
from models import SyncPayload

from routers.auth import cobrar_escrituras_kiosko, limitar_escrituras_kiosko, verificar_pc_id

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
    resultado = db_sesiones.registrar_sync(payload, ip)
    # El request ya se contó como una escritura; cada estudiante dado de alta
    # cuenta como una más, igual que si se hubiera creado con POST /estudiantes.
    cobrar_escrituras_kiosko(request, actor, resultado.get("estudiantes_creados", 0))
    return resultado

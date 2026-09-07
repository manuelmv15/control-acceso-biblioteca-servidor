from fastapi import APIRouter, Depends, Request
from db import sesiones as db_sesiones
from models import SyncPayload
from routers.auth import require_kiosk_or_admin

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", dependencies=[Depends(require_kiosk_or_admin)])
def recibir_sync(payload: SyncPayload, request: Request):
    ip = request.client.host if request.client else payload.ip
    return db_sesiones.registrar_sync(payload, ip)

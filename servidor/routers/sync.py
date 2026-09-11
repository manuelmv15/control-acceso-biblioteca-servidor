from fastapi import APIRouter, Depends, Request
from db import sesiones as db_sesiones
from models import SyncPayload
from routers.auth import limitar_escrituras_kiosko

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", dependencies=[Depends(limitar_escrituras_kiosko)])
def recibir_sync(payload: SyncPayload, request: Request):
    ip = request.client.host if request.client else payload.ip
    return db_sesiones.registrar_sync(payload, ip)

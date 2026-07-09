from fastapi import APIRouter, Request
from db import sesiones as db_sesiones
from models import SyncPayload

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("")
def recibir_sync(payload: SyncPayload, request: Request):
    ip = request.client.host if request.client else payload.ip
    return db_sesiones.registrar_sync(payload, ip)

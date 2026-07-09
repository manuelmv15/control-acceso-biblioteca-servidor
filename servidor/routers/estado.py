from fastapi import APIRouter
from db import estado as db_estado
from models import EstadoPayload

router = APIRouter(prefix="/estado", tags=["estado"])


@router.post("")
def actualizar_estado(payload: EstadoPayload):
    timestamp = db_estado.actualizar_estado(payload)
    return {"ok": True, "timestamp": timestamp}


@router.get("")
def obtener_estados():
    return db_estado.listar_estados()

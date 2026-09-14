from fastapi import APIRouter, Depends
from db import hardware as db_hardware
from models import HardwarePayload
from routers.auth import limitar_escrituras_kiosko, verificar_pc_id

router = APIRouter(prefix="/pcs", tags=["hardware"])


@router.post("/{pc_id}/hardware")
def reportar_hardware(pc_id: str, payload: HardwarePayload, actor: dict = Depends(limitar_escrituras_kiosko)):
    """Recibe el heartbeat del agente de hardware del cliente. La lista
    consolidada (con specs y estado_mantenimiento) se sirve vía GET /pcs,
    ya extendido en db/pcs.py::listar_mantenimiento()."""
    verificar_pc_id(actor, pc_id)
    db_hardware.upsert_lectura(pc_id, payload)
    return {
        "ok": True,
        "ultimo_mantenimiento": db_hardware.obtener_ultimo_mantenimiento(pc_id),
        "estado_mantenimiento": db_hardware.calcular_estado(payload.horas_uso_acumuladas),
    }

from fastapi import APIRouter, HTTPException
from db import pcs as db_pcs

router = APIRouter(prefix="/pcs", tags=["pcs"])


@router.get("")
def listar_pcs():
    return db_pcs.listar_mantenimiento()


@router.post("/{pc_id}/mantenimiento")
def registrar_mantenimiento(pc_id: str):
    if not db_pcs.registrar_mantenimiento(pc_id):
        raise HTTPException(status_code=404, detail="PC no encontrada")
    return {"ok": True}

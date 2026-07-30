from fastapi import APIRouter, Depends, HTTPException
from db import pcs as db_pcs
from routers.auth import require_auth

router = APIRouter(prefix="/pcs", tags=["pcs"], dependencies=[Depends(require_auth)])


@router.get("")
def listar_pcs():
    return db_pcs.listar_mantenimiento()


@router.post("/{pc_id}/mantenimiento")
def registrar_mantenimiento(pc_id: str):
    if not db_pcs.registrar_mantenimiento(pc_id):
        raise HTTPException(status_code=404, detail="PC no encontrada")
    return {"ok": True}

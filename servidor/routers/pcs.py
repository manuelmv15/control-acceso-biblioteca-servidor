import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from db import pcs as db_pcs
from routers.auth import require_auth

router = APIRouter(prefix="/pcs", tags=["pcs"], dependencies=[Depends(require_auth)])
log = logging.getLogger("uvicorn.error")


@router.get("")
def listar_pcs():
    return db_pcs.listar_mantenimiento()


@router.post("/{pc_id}/mantenimiento")
def registrar_mantenimiento(pc_id: str, request: Request, actor: dict = Depends(require_auth)):
    ip = request.client.host if request.client else "desconocida"
    if not db_pcs.registrar_mantenimiento(pc_id):
        log.warning("Mantenimiento en PC %s rechazado (no encontrada) — %s (%s) desde %s", pc_id, actor.get("sub"), actor.get("role"), ip)
        raise HTTPException(status_code=404, detail="PC no encontrada")
    log.info("Mantenimiento registrado en PC %s — %s (%s) desde %s", pc_id, actor.get("sub"), actor.get("role"), ip)
    return {"ok": True}

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from db import pcs as db_pcs
from routers.auth import require_auth, generar_api_key, hash_api_key

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


@router.post("/{pc_id}/api-key")
def generar_api_key_pc(pc_id: str, request: Request, actor: dict = Depends(require_auth)):
    """Genera (o rota) la API key dedicada de una PC. El valor en texto plano
    se devuelve una única vez en esta respuesta — el servidor solo guarda su
    hash (`hash_api_key`) y no hay forma de recuperarlo después; si se
    pierde, hay que generar uno nuevo. Rotar invalida de inmediato la key
    anterior de esa PC sin tocar la de las demás."""
    accion = "rotada" if db_pcs.obtener_api_key_hash(pc_id) else "generada"
    api_key = generar_api_key()
    db_pcs.fijar_api_key(pc_id, hash_api_key(api_key))
    ip = request.client.host if request.client else "desconocida"
    log.info("API key %s para PC %s — %s (%s) desde %s", accion, pc_id, actor.get("sub"), actor.get("role"), ip)
    return {"pc_id": pc_id, "api_key": api_key}


@router.delete("/{pc_id}/api-key", status_code=204)
def revocar_api_key_pc(pc_id: str, request: Request, actor: dict = Depends(require_auth)):
    """Revoca la key de una PC (queda sin key configurada hasta que se
    genere una nueva). No borra la PC ni su historial."""
    ip = request.client.host if request.client else "desconocida"
    if not db_pcs.revocar_api_key(pc_id):
        raise HTTPException(status_code=404, detail="PC no encontrada")
    log.warning("API key revocada para PC %s — %s (%s) desde %s", pc_id, actor.get("sub"), actor.get("role"), ip)

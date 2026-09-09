import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from db import estudiantes as db_estudiantes
from models import Estudiante
from routers.auth import require_auth, require_kiosk_or_admin, limitar_lecturas_estudiante

router = APIRouter(prefix="/estudiantes", tags=["estudiantes"])
log = logging.getLogger("uvicorn.error")


def _actor_ip(request: Request, actor: dict) -> str:
    ip = request.client.host if request.client else "desconocida"
    return f"{actor.get('sub')} ({actor.get('role')}) desde {ip}"


@router.post("", status_code=201)
def registrar_estudiante(
    est: Estudiante, request: Request, actor: dict = Depends(require_kiosk_or_admin)
):
    try:
        db_estudiantes.crear(est)
    except db_estudiantes.CarnetYaRegistrado:
        log.warning("Alta de estudiante %s rechazada (carnet ya registrado) — %s", est.carnet, _actor_ip(request, actor))
        raise HTTPException(status_code=409, detail="Carnet ya registrado")
    log.info("Alta de estudiante %s — %s", est.carnet, _actor_ip(request, actor))
    return {"carnet": est.carnet}


@router.get("", dependencies=[Depends(require_auth)])
def listar_estudiantes():
    return db_estudiantes.listar()


@router.get("/{carnet}", dependencies=[Depends(limitar_lecturas_estudiante)])
def obtener_estudiante(carnet: str):
    try:
        return db_estudiantes.obtener(carnet)
    except db_estudiantes.EstudianteNoEncontrado:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")


@router.put("/{carnet}")
def actualizar_estudiante(
    carnet: str, est: Estudiante, request: Request, actor: dict = Depends(require_kiosk_or_admin)
):
    try:
        db_estudiantes.actualizar(carnet, est)
    except db_estudiantes.EstudianteNoEncontrado:
        log.warning("Actualización de estudiante %s rechazada (no encontrado) — %s", carnet, _actor_ip(request, actor))
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    log.info("Actualización de estudiante %s — %s", carnet, _actor_ip(request, actor))
    return {"ok": True, "carnet": carnet}


@router.delete("/{carnet}", status_code=204)
def eliminar_estudiante(carnet: str, request: Request, actor: dict = Depends(require_auth)):
    try:
        db_estudiantes.eliminar(carnet)
    except db_estudiantes.EstudianteNoEncontrado:
        log.warning("Baja de estudiante %s rechazada (no encontrado) — %s", carnet, _actor_ip(request, actor))
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    except db_estudiantes.TieneSesionesRegistradas:
        log.warning("Baja de estudiante %s rechazada (tiene sesiones registradas) — %s", carnet, _actor_ip(request, actor))
        raise HTTPException(status_code=409, detail="No se puede eliminar: tiene sesiones registradas")
    log.info("Baja de estudiante %s — %s", carnet, _actor_ip(request, actor))

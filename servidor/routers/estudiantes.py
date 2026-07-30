from fastapi import APIRouter, Depends, HTTPException
from db import estudiantes as db_estudiantes
from models import Estudiante
from routers.auth import require_auth, require_kiosk_or_admin

router = APIRouter(prefix="/estudiantes", tags=["estudiantes"])


@router.post("", status_code=201, dependencies=[Depends(require_kiosk_or_admin)])
def registrar_estudiante(est: Estudiante):
    try:
        db_estudiantes.crear(est)
    except db_estudiantes.CarnetYaRegistrado:
        raise HTTPException(status_code=409, detail="Carnet ya registrado")
    return {"carnet": est.carnet}


@router.get("", dependencies=[Depends(require_auth)])
def listar_estudiantes():
    return db_estudiantes.listar()


@router.get("/{carnet}", dependencies=[Depends(require_kiosk_or_admin)])
def obtener_estudiante(carnet: str):
    try:
        return db_estudiantes.obtener(carnet)
    except db_estudiantes.EstudianteNoEncontrado:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")


@router.put("/{carnet}", dependencies=[Depends(require_kiosk_or_admin)])
def actualizar_estudiante(carnet: str, est: Estudiante):
    try:
        db_estudiantes.actualizar(carnet, est)
    except db_estudiantes.EstudianteNoEncontrado:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return {"ok": True, "carnet": carnet}


@router.delete("/{carnet}", status_code=204, dependencies=[Depends(require_auth)])
def eliminar_estudiante(carnet: str):
    try:
        db_estudiantes.eliminar(carnet)
    except db_estudiantes.EstudianteNoEncontrado:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    except db_estudiantes.TieneSesionesRegistradas:
        raise HTTPException(status_code=409, detail="No se puede eliminar: tiene sesiones registradas")

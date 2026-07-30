from typing import Optional
from fastapi import APIRouter, Depends, Query
from db import reportes as db_reportes
from routers.auth import require_auth

router = APIRouter(prefix="/reportes", tags=["reportes"], dependencies=[Depends(require_auth)])


@router.get("/sesiones")
def listar_sesiones(
    fecha: Optional[str] = Query(None),
    pc_id: Optional[str] = Query(None),
    carnet: Optional[str] = Query(None),
    carrera: Optional[str] = Query(None),
    limit: int = Query(500, le=5000),
    offset: int = Query(0, ge=0),
):
    return db_reportes.listar_sesiones(fecha, pc_id, carnet, carrera, limit, offset)


@router.get("/pcs-activas")
def pcs_activas():
    return db_reportes.pcs_activas()


@router.get("/resumen-dia")
def resumen_dia(fecha: Optional[str] = Query(None)):
    return db_reportes.resumen_dia(fecha)


@router.get("/estadisticas")
def estadisticas(
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
):
    return db_reportes.estadisticas(desde, hasta)

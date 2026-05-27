from datetime import date
from typing import Optional
from fastapi import APIRouter, Query
from database import get_connection

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/sesiones")
def listar_sesiones(
    fecha: Optional[str] = Query(None),
    pc_id: Optional[str] = Query(None),
    carnet: Optional[str] = Query(None),
    carrera: Optional[str] = Query(None),
    limit: int = Query(500, le=5000),
    offset: int = Query(0, ge=0),
):
    where = []
    params = []

    if fecha:
        where.append("s.fecha = ?")
        params.append(fecha)
    else:
        where.append("s.fecha = ?")
        params.append(date.today().isoformat())

    if pc_id:
        where.append("s.pc_id = ?")
        params.append(pc_id)
    if carnet:
        where.append("s.carnet = ?")
        params.append(carnet)
    if carrera:
        where.append("e.carrera = ?")
        params.append(carrera)

    where_sql = "WHERE " + " AND ".join(where) if where else ""
    params += [limit, offset]

    conn = get_connection()
    rows = conn.execute(f"""
        SELECT s.id, s.pc_id, s.carnet, s.hora_inicio, s.hora_fin, s.fecha,
               e.nombre, e.carrera, e.facultad,
               ROUND((JULIANDAY(COALESCE(s.hora_fin, datetime('now'))) - JULIANDAY(s.hora_inicio)) * 1440) AS minutos
        FROM sesiones s
        LEFT JOIN estudiantes e ON e.carnet = s.carnet
        {where_sql}
        ORDER BY s.hora_inicio DESC
        LIMIT ? OFFSET ?
    """, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/pcs-activas")
def pcs_activas():
    conn = get_connection()
    rows = conn.execute("""
        SELECT pc_id, nombre, ultima_conexion, ip_reportada
        FROM pcs
        WHERE ultima_conexion >= datetime('now', '-5 minutes')
        ORDER BY nombre
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/resumen-dia")
def resumen_dia(fecha: Optional[str] = Query(None)):
    target = fecha or date.today().isoformat()
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*) AS total_sesiones,
            COUNT(DISTINCT carnet) AS estudiantes_unicos,
            COUNT(DISTINCT pc_id) AS pcs_usadas,
            ROUND(AVG(ROUND((JULIANDAY(COALESCE(hora_fin, datetime('now'))) - JULIANDAY(hora_inicio)) * 1440))) AS minutos_promedio
        FROM sesiones WHERE fecha = ?
    """, (target,)).fetchone()
    conn.close()
    return dict(row)

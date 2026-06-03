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
    target_date = fecha or date.today().isoformat()

    where_s = ["s.fecha = ?"]
    params_s = [target_date]
    if pc_id:
        where_s.append("s.pc_id = ?")
        params_s.append(pc_id)
    if carnet:
        where_s.append("s.carnet = ?")
        params_s.append(carnet)
    if carrera:
        where_s.append("e.carrera = ?")
        params_s.append(carrera)
    where_sql = "WHERE " + " AND ".join(where_s)

    where_e = [
        "ep.sesion_activa = 1",
        "ep.carnet IS NOT NULL",
        "ep.hora_inicio IS NOT NULL",
        "date(ep.hora_inicio) = ?",
        "NOT EXISTS (SELECT 1 FROM sesiones sx WHERE sx.pc_id = ep.pc_id AND sx.hora_inicio = ep.hora_inicio AND sx.hora_fin IS NULL)",
    ]
    params_e = [target_date]
    if pc_id:
        where_e.append("ep.pc_id = ?")
        params_e.append(pc_id)
    if carnet:
        where_e.append("ep.carnet = ?")
        params_e.append(carnet)
    where_estado_sql = "WHERE " + " AND ".join(where_e)

    all_params = params_s + params_e + [limit, offset]

    conn = get_connection()
    rows = conn.execute(f"""
        SELECT s.id, s.pc_id, s.carnet, s.hora_inicio, s.hora_fin, s.fecha,
               e.nombre, e.carrera, e.facultad,
               ROUND((JULIANDAY(COALESCE(s.hora_fin, datetime('now'))) - JULIANDAY(s.hora_inicio)) * 1440) AS minutos
        FROM sesiones s
        LEFT JOIN estudiantes e ON e.carnet = s.carnet
        {where_sql}

        UNION ALL

        SELECT
            ep.pc_id || '_' || ep.hora_inicio AS id,
            ep.pc_id,
            ep.carnet,
            ep.hora_inicio,
            NULL AS hora_fin,
            date(ep.hora_inicio) AS fecha,
            ep.nombre,
            e2.carrera,
            e2.facultad,
            ROUND((JULIANDAY(datetime('now')) - JULIANDAY(ep.hora_inicio)) * 1440) AS minutos
        FROM estado_pcs ep
        LEFT JOIN estudiantes e2 ON e2.carnet = ep.carnet
        {where_estado_sql}

        ORDER BY hora_inicio DESC
        LIMIT ? OFFSET ?
    """, all_params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/pcs-activas")
def pcs_activas():
    conn = get_connection()
    rows = conn.execute("""
        SELECT pc_id, nombre, ultima_conexion, ip_reportada
        FROM pcs
        WHERE ultima_conexion >= datetime('now', 'localtime', '-5 minutes')
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
        FROM (
            SELECT carnet, pc_id, hora_inicio, hora_fin FROM sesiones WHERE fecha = ?
            UNION ALL
            SELECT carnet, pc_id, hora_inicio, NULL AS hora_fin
            FROM estado_pcs
            WHERE sesion_activa = 1 AND carnet IS NOT NULL AND hora_inicio IS NOT NULL
              AND date(hora_inicio) = ?
              AND NOT EXISTS (
                  SELECT 1 FROM sesiones sx WHERE sx.pc_id = estado_pcs.pc_id AND sx.hora_inicio = estado_pcs.hora_inicio AND sx.hora_fin IS NULL
              )
        )
    """, (target, target)).fetchone()
    conn.close()
    return dict(row)

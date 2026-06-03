from datetime import datetime
from fastapi import APIRouter
from database import get_connection
from models import EstadoPayload

router = APIRouter(prefix="/estado", tags=["estado"])


@router.post("")
def actualizar_estado(payload: EstadoPayload):
    conn = get_connection()
    ahora = datetime.utcnow().isoformat()

    conn.execute("""
        INSERT INTO estado_pcs (pc_id, pc_nombre, sesion_activa, carnet, nombre, hora_inicio, ultima_actualizacion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(pc_id) DO UPDATE SET
            pc_nombre            = excluded.pc_nombre,
            sesion_activa        = excluded.sesion_activa,
            carnet               = excluded.carnet,
            nombre               = excluded.nombre,
            hora_inicio          = excluded.hora_inicio,
            ultima_actualizacion = excluded.ultima_actualizacion
    """, (
        payload.pc_id,
        payload.pc_nombre,
        int(payload.sesion_activa),
        payload.carnet,
        payload.nombre,
        payload.hora_inicio,
        ahora,
    ))

    conn.commit()
    conn.close()
    return {"ok": True, "timestamp": ahora}


@router.get("")
def obtener_estados():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM estado_pcs ORDER BY pc_nombre"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

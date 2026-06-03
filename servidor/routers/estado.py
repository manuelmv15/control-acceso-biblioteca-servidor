import uuid
from datetime import datetime
from fastapi import APIRouter
from database import get_connection
from models import EstadoPayload

router = APIRouter(prefix="/estado", tags=["estado"])


@router.post("")
def actualizar_estado(payload: EstadoPayload):
    conn = get_connection()
    ahora = datetime.now().isoformat()

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

    if payload.sesion_activa and payload.carnet and payload.nombre:
        fecha_hoy = datetime.now().date().isoformat()
        conn.execute("""
            INSERT INTO estudiantes (id, nombre, carnet, carrera, facultad, departamento, sexo, fecha_nacimiento, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(carnet) DO UPDATE SET
                nombre        = excluded.nombre,
                carrera       = COALESCE(excluded.carrera,       estudiantes.carrera),
                facultad      = COALESCE(excluded.facultad,      estudiantes.facultad),
                departamento  = COALESCE(excluded.departamento,  estudiantes.departamento),
                sexo          = COALESCE(excluded.sexo,          estudiantes.sexo),
                fecha_nacimiento = COALESCE(excluded.fecha_nacimiento, estudiantes.fecha_nacimiento)
        """, (str(uuid.uuid4()), payload.nombre, payload.carnet,
              payload.carrera, payload.facultad, payload.departamento,
              payload.sexo, payload.fecha_nacimiento, fecha_hoy))

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

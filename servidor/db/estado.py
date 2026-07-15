from datetime import datetime
from .connection import conexion
from . import pcs as db_pcs
from .estudiantes import upsert_desde_sesion


def actualizar_estado(payload):
    with conexion() as conn:
        ahora = datetime.now().isoformat()

        db_pcs.asegurar(conn, payload.pc_id, payload.pc_nombre)

        if payload.carnet:
            fecha_hoy = datetime.now().date().isoformat()
            upsert_desde_sesion(
                conn, payload.carnet, payload.nombre, payload.carrera,
                payload.facultad, payload.sexo,
                payload.fecha_nacimiento, fecha_hoy,
            )

        conn.execute("""
            INSERT INTO estado_pcs (pc_id, pc_nombre, sesion_activa, carnet, nombre, hora_inicio, ultima_actualizacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                pc_nombre            = VALUES(pc_nombre),
                sesion_activa        = VALUES(sesion_activa),
                carnet               = VALUES(carnet),
                nombre               = VALUES(nombre),
                hora_inicio          = VALUES(hora_inicio),
                ultima_actualizacion = VALUES(ultima_actualizacion)
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
        return ahora


def listar_estados():
    with conexion() as conn:
        rows = conn.execute(
            "SELECT * FROM estado_pcs ORDER BY pc_nombre"
        ).fetchall()
        return [dict(r) for r in rows]

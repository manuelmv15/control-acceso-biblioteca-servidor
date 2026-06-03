import uuid
from datetime import datetime
from fastapi import APIRouter, Request
from database import get_connection
from models import SyncPayload

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("")
def recibir_sync(payload: SyncPayload, request: Request):
    conn = get_connection()
    cursor = conn.cursor()
    ahora = datetime.now().isoformat()
    ip = request.client.host if request.client else payload.ip

    cursor.execute("""
        INSERT INTO pcs (pc_id, nombre, ultima_conexion, ip_reportada)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(pc_id) DO UPDATE SET
            nombre = excluded.nombre,
            ultima_conexion = excluded.ultima_conexion,
            ip_reportada = excluded.ip_reportada
    """, (payload.pc_id, payload.pc_nombre, ahora, ip))

    insertados = 0
    fecha_hoy = datetime.now().date().isoformat()
    for s in payload.sesiones:
        cursor.execute("""
            INSERT INTO sesiones
                (id, pc_id, carnet, hora_inicio, hora_fin, fecha, sincronizado, timestamp_sync)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(id) DO UPDATE SET
                hora_fin       = excluded.hora_fin,
                sincronizado   = 1,
                timestamp_sync = excluded.timestamp_sync
            WHERE excluded.hora_fin IS NOT NULL
        """, (s.id, s.pc_id, s.carnet, s.hora_inicio, s.hora_fin, s.fecha, ahora))
        insertados += cursor.rowcount

        if s.nombre and s.carnet:
            cursor.execute("""
                INSERT INTO estudiantes (id, nombre, carnet, carrera, facultad, departamento, sexo, fecha_nacimiento, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(carnet) DO UPDATE SET
                    nombre       = excluded.nombre,
                    carrera      = COALESCE(excluded.carrera,      estudiantes.carrera),
                    facultad     = COALESCE(excluded.facultad,     estudiantes.facultad),
                    departamento = COALESCE(excluded.departamento, estudiantes.departamento),
                    sexo         = COALESCE(excluded.sexo,         estudiantes.sexo),
                    fecha_nacimiento = COALESCE(excluded.fecha_nacimiento, estudiantes.fecha_nacimiento)
            """, (str(uuid.uuid4()), s.nombre, s.carnet,
                  s.carrera, s.facultad, s.departamento,
                  s.sexo, s.fecha_nacimiento, fecha_hoy))

    conn.commit()
    conn.close()
    return {"recibidos": len(payload.sesiones), "insertados": insertados, "timestamp": ahora}

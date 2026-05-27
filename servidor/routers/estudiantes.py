import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from database import get_connection
from models import Estudiante

router = APIRouter(prefix="/estudiantes", tags=["estudiantes"])


@router.post("", status_code=201)
def registrar_estudiante(est: Estudiante):
    conn = get_connection()
    cursor = conn.cursor()
    existe = cursor.execute("SELECT id FROM estudiantes WHERE carnet = ?", (est.carnet,)).fetchone()
    if existe:
        conn.close()
        raise HTTPException(status_code=409, detail="Carnet ya registrado")

    nuevo_id = est.id or str(uuid.uuid4())
    fecha_reg = est.fecha_registro or datetime.utcnow().date().isoformat()
    cursor.execute("""
        INSERT INTO estudiantes (id, nombre, carnet, fecha_nacimiento, carrera, departamento, facultad, sexo, fecha_registro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nuevo_id, est.nombre, est.carnet, est.fecha_nacimiento, est.carrera, est.departamento, est.facultad, est.sexo, fecha_reg))
    conn.commit()
    conn.close()
    return {"id": nuevo_id, "carnet": est.carnet}


@router.get("/{carnet}")
def obtener_estudiante(carnet: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM estudiantes WHERE carnet = ?", (carnet,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return dict(row)

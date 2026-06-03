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


@router.get("")
def listar_estudiantes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM estudiantes ORDER BY nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{carnet}")
def obtener_estudiante(carnet: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM estudiantes WHERE carnet = ?", (carnet,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return dict(row)


@router.put("/{carnet}")
def actualizar_estudiante(carnet: str, est: Estudiante):
    conn = get_connection()
    existe = conn.execute("SELECT id FROM estudiantes WHERE carnet = ?", (carnet,)).fetchone()
    if not existe:
        conn.close()
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    conn.execute("""
        UPDATE estudiantes
        SET nombre=?, fecha_nacimiento=?, carrera=?, departamento=?, facultad=?, sexo=?
        WHERE carnet=?
    """, (est.nombre, est.fecha_nacimiento, est.carrera, est.departamento, est.facultad, est.sexo, carnet))
    conn.commit()
    conn.close()
    return {"ok": True, "carnet": carnet}


@router.delete("/{carnet}", status_code=204)
def eliminar_estudiante(carnet: str):
    conn = get_connection()
    existe = conn.execute("SELECT id FROM estudiantes WHERE carnet = ?", (carnet,)).fetchone()
    if not existe:
        conn.close()
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    conn.execute("DELETE FROM estudiantes WHERE carnet = ?", (carnet,))
    conn.commit()
    conn.close()

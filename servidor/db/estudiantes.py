import pymysql
from datetime import datetime
from .connection import conexion


class CarnetYaRegistrado(Exception):
    pass


class EstudianteNoEncontrado(Exception):
    pass


class TieneSesionesRegistradas(Exception):
    pass


def _normalizar_fecha_nacimiento(valor):
    """Solo se captura el año de nacimiento; una cadena vacía debe guardarse
    como NULL en la columna YEAR."""
    return valor or None


def crear(est):
    with conexion() as conn:
        existe = conn.execute("SELECT carnet FROM estudiantes WHERE carnet = %s", (est.carnet,)).fetchone()
        if existe:
            raise CarnetYaRegistrado()

        fecha_reg = est.fecha_registro or datetime.utcnow().date().isoformat()
        conn.execute("""
            INSERT INTO estudiantes (carnet, nombre, fecha_nacimiento, carrera, facultad, sexo, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (est.carnet, est.nombre, _normalizar_fecha_nacimiento(est.fecha_nacimiento), est.carrera, est.facultad, est.sexo, fecha_reg))
        conn.commit()


def listar():
    with conexion() as conn:
        rows = conn.execute("SELECT * FROM estudiantes ORDER BY nombre IS NULL, nombre").fetchall()
        return [dict(r) for r in rows]


def obtener(carnet):
    with conexion() as conn:
        row = conn.execute("SELECT * FROM estudiantes WHERE carnet = %s", (carnet,)).fetchone()
        if not row:
            raise EstudianteNoEncontrado()
        return dict(row)


def actualizar(carnet, est):
    with conexion() as conn:
        existe = conn.execute("SELECT carnet FROM estudiantes WHERE carnet = %s", (carnet,)).fetchone()
        if not existe:
            raise EstudianteNoEncontrado()
        conn.execute("""
            UPDATE estudiantes
            SET nombre=%s, fecha_nacimiento=%s, carrera=%s, facultad=%s, sexo=%s
            WHERE carnet=%s
        """, (est.nombre, _normalizar_fecha_nacimiento(est.fecha_nacimiento), est.carrera, est.facultad, est.sexo, carnet))
        conn.commit()


def eliminar(carnet):
    with conexion() as conn:
        existe = conn.execute("SELECT carnet FROM estudiantes WHERE carnet = %s", (carnet,)).fetchone()
        if not existe:
            raise EstudianteNoEncontrado()
        try:
            conn.execute("DELETE FROM estudiantes WHERE carnet = %s", (carnet,))
            conn.commit()
        except pymysql.err.IntegrityError:
            raise TieneSesionesRegistradas()


def upsert_desde_sesion(conn, carnet, nombre, carrera, facultad, sexo, fecha_nacimiento, fecha_registro):
    conn.execute("""
        INSERT INTO estudiantes (carnet, nombre, carrera, facultad, sexo, fecha_nacimiento, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            nombre       = COALESCE(VALUES(nombre),       nombre),
            carrera      = COALESCE(VALUES(carrera),      carrera),
            facultad     = COALESCE(VALUES(facultad),     facultad),
            sexo         = COALESCE(VALUES(sexo),         sexo),
            fecha_nacimiento = COALESCE(VALUES(fecha_nacimiento), fecha_nacimiento)
    """, (carnet, nombre, carrera, facultad, sexo, _normalizar_fecha_nacimiento(fecha_nacimiento), fecha_registro))

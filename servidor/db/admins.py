from datetime import datetime

from .connection import conexion


def obtener_hash(username):
    with conexion() as conn:
        row = conn.execute("SELECT password_hash FROM admins WHERE username = %s", (username,)).fetchone()
        return row["password_hash"] if row else None


def obtener_actualizado(username):
    """Fecha (UTC, ver `actualizar_password`) del último cambio de contraseña de `username`,
    o None si el usuario no existe. La usa `routers/auth.py::verify_token` para rechazar
    JWTs de admin emitidos antes de ese cambio, aunque todavía no hayan expirado."""
    with conexion() as conn:
        row = conn.execute("SELECT actualizado FROM admins WHERE username = %s", (username,)).fetchone()
        return row["actualizado"] if row else None


def actualizar_password(username, nuevo_hash):
    """`actualizado` se fija en UTC calculado acá en Python, no con el `NOW()` de MySQL: así
    queda en el mismo reloj que el `iat` de los JWT (también `datetime.utcnow()`, ver
    `routers/auth.py::create_token`) y la comparación en `verify_token` no depende de qué
    zona horaria tenga configurada el servidor de MySQL."""
    with conexion() as conn:
        conn.execute(
            "UPDATE admins SET password_hash = %s, actualizado = %s WHERE username = %s",
            (nuevo_hash, datetime.utcnow(), username),
        )
        conn.commit()

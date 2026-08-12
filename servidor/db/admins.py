from .connection import conexion


def obtener_hash(username):
    with conexion() as conn:
        row = conn.execute("SELECT password_hash FROM admins WHERE username = %s", (username,)).fetchone()
        return row["password_hash"] if row else None


def actualizar_password(username, nuevo_hash):
    with conexion() as conn:
        conn.execute(
            "UPDATE admins SET password_hash = %s, actualizado = NOW() WHERE username = %s",
            (nuevo_hash, username),
        )
        conn.commit()

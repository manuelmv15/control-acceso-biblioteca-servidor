from datetime import datetime
from .connection import conexion


def upsert_conexion(conn, pc_id, nombre, ultima_conexion, ip):
    conn.execute("""
        INSERT INTO pcs (pc_id, nombre, ultima_conexion, ip_reportada)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            nombre = VALUES(nombre),
            ultima_conexion = VALUES(ultima_conexion),
            ip_reportada = VALUES(ip_reportada)
    """, (pc_id, nombre, ultima_conexion, ip))


def asegurar(conn, pc_id, nombre):
    conn.execute("""
        INSERT INTO pcs (pc_id, nombre)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            nombre = COALESCE(VALUES(nombre), nombre)
    """, (pc_id, nombre))


def registrar_mantenimiento(pc_id):
    with conexion() as conn:
        cursor = conn.execute(
            "UPDATE pcs SET ultimo_mantenimiento = %s WHERE pc_id = %s",
            (datetime.now().isoformat(), pc_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def listar_mantenimiento():
    """PCs con su fecha de último mantenimiento y el tiempo de uso (suma de
    duraciones de sesiones) acumulado desde entonces, como referencia para
    saber a cuáles les toca mantenimiento."""
    with conexion() as conn:
        rows = conn.execute("""
            SELECT p.pc_id, p.nombre, p.ultima_conexion, p.ultimo_mantenimiento,
                   COALESCE(SUM(TIMESTAMPDIFF(MINUTE, t.hora_inicio, COALESCE(t.hora_fin, NOW()))), 0)
                       AS minutos_uso_desde_mantenimiento
            FROM pcs p
            LEFT JOIN (
                SELECT pc_id, hora_inicio, hora_fin FROM sesiones
                UNION ALL
                SELECT pc_id, hora_inicio, NULL AS hora_fin
                FROM estado_pcs
                WHERE sesion_activa = 1 AND hora_inicio IS NOT NULL
            ) t ON t.pc_id = p.pc_id
               AND t.hora_inicio >= COALESCE(p.ultimo_mantenimiento, '1970-01-01 00:00:00')
            GROUP BY p.pc_id, p.nombre, p.ultima_conexion, p.ultimo_mantenimiento
            ORDER BY p.nombre
        """).fetchall()
        return [dict(r) for r in rows]

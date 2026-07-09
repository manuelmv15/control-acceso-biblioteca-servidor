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

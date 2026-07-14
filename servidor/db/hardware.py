from .connection import conexion
from . import pcs as db_pcs
from .umbrales import calcular_estado


def upsert_lectura(pc_id, payload):
    with conexion() as conn:
        db_pcs.asegurar(conn, pc_id, None)
        conn.execute("""
            INSERT INTO pcs_hardware
                (pc_id, hostname, mac_address, cpu, ram_total_mb, almacenamiento_total_gb,
                 sistema_operativo, temperatura_cpu_c, disco_smart_ok, horas_uso_acumuladas, ultima_lectura)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                hostname                 = VALUES(hostname),
                mac_address               = VALUES(mac_address),
                cpu                       = VALUES(cpu),
                ram_total_mb              = VALUES(ram_total_mb),
                almacenamiento_total_gb   = VALUES(almacenamiento_total_gb),
                sistema_operativo         = VALUES(sistema_operativo),
                temperatura_cpu_c         = VALUES(temperatura_cpu_c),
                disco_smart_ok            = VALUES(disco_smart_ok),
                horas_uso_acumuladas      = VALUES(horas_uso_acumuladas),
                ultima_lectura            = VALUES(ultima_lectura)
        """, (
            pc_id, payload.hostname, payload.mac, payload.cpu, payload.ram_total_mb,
            payload.almacenamiento_total_gb, payload.sistema_operativo,
            payload.temperatura_cpu_c, payload.disco_smart_ok,
            payload.horas_uso_acumuladas, payload.ultima_lectura,
        ))
        conn.commit()


def obtener_ultimo_mantenimiento(pc_id):
    """Usado por el router para que el agente del cliente sepa si debe
    reiniciar su acumulador local de horas."""
    with conexion() as conn:
        row = conn.execute(
            "SELECT ultimo_mantenimiento FROM pcs WHERE pc_id = %s", (pc_id,)
        ).fetchone()
        return row["ultimo_mantenimiento"].isoformat() if row and row["ultimo_mantenimiento"] else None

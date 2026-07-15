from .connection import conexion


def _tiene_columna(conn, tabla, columna):
    row = conn.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s
    """, (tabla, columna)).fetchone()
    return row is not None


def init_db():
    with conexion() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS estudiantes (
                carnet VARCHAR(30) PRIMARY KEY,
                nombre VARCHAR(255),
                fecha_nacimiento DATE,
                carrera VARCHAR(255),
                facultad VARCHAR(255),
                sexo VARCHAR(20),
                fecha_registro DATE NOT NULL
            ) ENGINE=InnoDB;

            CREATE TABLE IF NOT EXISTS pcs (
                pc_id VARCHAR(100) PRIMARY KEY,
                nombre VARCHAR(255),
                ultima_conexion DATETIME,
                ip_reportada VARCHAR(45),
                ultimo_mantenimiento DATETIME
            ) ENGINE=InnoDB;

            CREATE TABLE IF NOT EXISTS sesiones (
                id VARCHAR(100) PRIMARY KEY,
                pc_id VARCHAR(100) NOT NULL,
                carnet VARCHAR(30),
                hora_inicio DATETIME NOT NULL,
                hora_fin DATETIME,
                fecha DATE NOT NULL,
                sincronizado TINYINT(1) DEFAULT 0,
                timestamp_sync DATETIME,
                INDEX idx_sesiones_fecha (fecha),
                INDEX idx_sesiones_carnet (carnet),
                INDEX idx_sesiones_pc_id (pc_id),
                CONSTRAINT fk_sesiones_pc FOREIGN KEY (pc_id) REFERENCES pcs(pc_id),
                CONSTRAINT fk_sesiones_estudiante FOREIGN KEY (carnet) REFERENCES estudiantes(carnet)
            ) ENGINE=InnoDB;

            CREATE TABLE IF NOT EXISTS estado_pcs (
                pc_id VARCHAR(100) PRIMARY KEY,
                pc_nombre VARCHAR(255),
                sesion_activa TINYINT(1) DEFAULT 0,
                carnet VARCHAR(30),
                nombre VARCHAR(255),
                hora_inicio DATETIME,
                ultima_actualizacion DATETIME,
                CONSTRAINT fk_estado_pcs_pc FOREIGN KEY (pc_id) REFERENCES pcs(pc_id),
                CONSTRAINT fk_estado_pcs_estudiante FOREIGN KEY (carnet) REFERENCES estudiantes(carnet) ON DELETE SET NULL
            ) ENGINE=InnoDB;

            CREATE TABLE IF NOT EXISTS pcs_hardware (
                pc_id VARCHAR(100) PRIMARY KEY,
                hostname VARCHAR(255),
                mac_address VARCHAR(20),
                cpu VARCHAR(255),
                ram_total_mb INT,
                almacenamiento_total_gb INT,
                sistema_operativo VARCHAR(255),
                temperatura_cpu_c DECIMAL(5,1),
                disco_smart_ok TINYINT(1),
                horas_uso_acumuladas DECIMAL(8,2) NOT NULL DEFAULT 0,
                ultima_lectura DATETIME,
                CONSTRAINT fk_pcs_hardware_pc FOREIGN KEY (pc_id) REFERENCES pcs(pc_id)
            ) ENGINE=InnoDB;
        """)
        conn.commit()

        # Migraciones ligeras para bases ya existentes (no hay sistema de
        # migraciones formal; los cambios de esquema se aplican aquí).
        if not _tiene_columna(conn, "pcs", "ultimo_mantenimiento"):
            conn.execute("ALTER TABLE pcs ADD COLUMN ultimo_mantenimiento DATETIME NULL")
        conn.execute("ALTER TABLE sesiones MODIFY COLUMN carnet VARCHAR(30) NULL")
        if _tiene_columna(conn, "estudiantes", "departamento"):
            conn.execute("ALTER TABLE estudiantes DROP COLUMN departamento")
        conn.commit()

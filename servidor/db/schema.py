from .connection import conexion


def init_db():
    with conexion() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS estudiantes (
                carnet VARCHAR(30) PRIMARY KEY,
                nombre VARCHAR(255),
                fecha_nacimiento DATE,
                carrera VARCHAR(255),
                departamento VARCHAR(255),
                facultad VARCHAR(255),
                sexo VARCHAR(20),
                fecha_registro DATE NOT NULL
            ) ENGINE=InnoDB;

            CREATE TABLE IF NOT EXISTS pcs (
                pc_id VARCHAR(100) PRIMARY KEY,
                nombre VARCHAR(255),
                ultima_conexion DATETIME,
                ip_reportada VARCHAR(45)
            ) ENGINE=InnoDB;

            CREATE TABLE IF NOT EXISTS sesiones (
                id VARCHAR(100) PRIMARY KEY,
                pc_id VARCHAR(100) NOT NULL,
                carnet VARCHAR(30) NOT NULL,
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
        """)
        conn.commit()

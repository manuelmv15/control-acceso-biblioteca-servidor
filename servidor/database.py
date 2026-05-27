import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "biblioteca.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            carnet TEXT UNIQUE NOT NULL,
            fecha_nacimiento TEXT,
            carrera TEXT,
            departamento TEXT,
            facultad TEXT,
            sexo TEXT,
            fecha_registro TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pcs (
            pc_id TEXT PRIMARY KEY,
            nombre TEXT,
            ultima_conexion TEXT,
            ip_reportada TEXT
        );

        CREATE TABLE IF NOT EXISTS sesiones (
            id TEXT PRIMARY KEY,
            pc_id TEXT NOT NULL,
            carnet TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT,
            fecha TEXT NOT NULL,
            sincronizado INTEGER DEFAULT 0,
            timestamp_sync TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_sesiones_fecha ON sesiones(fecha);
        CREATE INDEX IF NOT EXISTS idx_sesiones_carnet ON sesiones(carnet);
        CREATE INDEX IF NOT EXISTS idx_sesiones_pc_id ON sesiones(pc_id);
    """)
    conn.commit()
    conn.close()

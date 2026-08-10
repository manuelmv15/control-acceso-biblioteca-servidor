#!/usr/bin/env python3
"""Genera datos de demostración para visualizar el panel.

Uso:
  python seed_demo.py --reset

Se puede ejecutar dentro del contenedor `servidor` o desde el host, siempre
que las variables de entorno de conexión a MySQL estén configuradas.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from db.connection import conexion
from db.schema import init_db


SEED = 20260807
RNG = random.Random(SEED)


FACULTADES = {
    "Ing. de Sistemas": ["Ingeniería de Sistemas y Computación", "Ciencias de la Computación"],
    "Ciencias Económicas": ["Administración de Empresas", "Contaduría Pública"],
    "Ciencias y Humanidades": ["Psicología", "Comunicación"],
    "Ingeniería y Arquitectura": ["Ingeniería Civil", "Arquitectura"],
}

SEXO_OPCIONES = ["Masculino", "Femenino", "No especificado"]
NOMBRES = [
    "Ana", "Brenda", "Carlos", "Daniel", "Elena", "Fernando", "Gabriela", "Hugo",
    "Ingrid", "José", "Karla", "Luis", "María", "Nelson", "Olga", "Pedro",
    "Raúl", "Sofía", "Tomás", "Valeria", "Walter", "Ximena",
]
APELLIDOS = [
    "Alvarado", "Bonilla", "Castro", "Díaz", "Escobar", "Flores", "García", "Hernández",
    "Ibarra", "Jiménez", "López", "Mena", "Núñez", "Ortiz", "Pérez", "Quintanilla",
    "Ramos", "Sánchez", "Torres", "Urbina", "Vásquez", "Zelaya",
]

PCS = [
    ("PC-01", "Biblioteca Norte 01", "b8:27:eb:01:00:01", "Intel Core i5-8500", 8192, 256, "Ubuntu 22.04", 48.2, 1, 1200.5),
    ("PC-02", "Biblioteca Norte 02", "b8:27:eb:01:00:02", "Intel Core i5-8500", 8192, 256, "Ubuntu 22.04", 51.3, 1, 980.0),
    ("PC-03", "Biblioteca Norte 03", "b8:27:eb:01:00:03", "Intel Core i7-8700", 16384, 512, "Ubuntu 22.04", 46.7, 1, 305.2),
    ("PC-04", "Biblioteca Norte 04", "b8:27:eb:01:00:04", "Intel Core i5-7500", 8192, 240, "Windows 11", 54.1, 0, 412.9),
    ("PC-05", "Biblioteca Sur 01", "b8:27:eb:01:00:05", "AMD Ryzen 5 5600G", 16384, 512, "Windows 11", 43.8, 1, 240.0),
    ("PC-06", "Biblioteca Sur 02", "b8:27:eb:01:00:06", "AMD Ryzen 5 5600G", 16384, 512, "Windows 11", 44.2, 1, 180.4),
    ("PC-07", "Biblioteca Sala 01", "b8:27:eb:01:00:07", "Intel Core i3-9100", 8192, 240, "Ubuntu 22.04", 49.0, 1, 75.3),
    ("PC-08", "Biblioteca Sala 02", "b8:27:eb:01:00:08", "Intel Core i3-9100", 8192, 240, "Ubuntu 22.04", 47.9, 1, 60.1),
]


@dataclass(frozen=True)
class Student:
    carnet: str
    nombre: str
    fecha_nacimiento: int
    carrera: str | None
    facultad: str | None
    sexo: str | None
    fecha_registro: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera datos de demostración para el panel")
    parser.add_argument("--reset", action="store_true", help="Vacía las tablas antes de insertar datos")
    parser.add_argument("--students", type=int, default=36, help="Cantidad de estudiantes a generar")
    parser.add_argument("--sessions", type=int, default=120, help="Cantidad de sesiones históricas a generar")
    return parser.parse_args()


def choose_faculty_and_career() -> tuple[str, str]:
    facultad = RNG.choice(list(FACULTADES))
    carrera = RNG.choice(FACULTADES[facultad])
    return facultad, carrera


def build_students(count: int) -> list[Student]:
    students: list[Student] = []
    used_carnets: set[str] = set()
    for index in range(count):
        primer_nombre = RNG.choice(NOMBRES)
        apellido = RNG.choice(APELLIDOS)
        segundo_apellido = RNG.choice(APELLIDOS)
        nombre = f"{primer_nombre} {apellido} {segundo_apellido}"
        carnet = f"2026{index:04d}"
        while carnet in used_carnets:
            index += 1
            carnet = f"2026{index:04d}"
        used_carnets.add(carnet)
        facultad, carrera = choose_faculty_and_career()
        students.append(
            Student(
                carnet=carnet,
                nombre=nombre,
                fecha_nacimiento=RNG.randint(1997, 2007),
                carrera=carrera,
                facultad=facultad,
                sexo=RNG.choice(SEXO_OPCIONES),
                fecha_registro=(datetime.now() - timedelta(days=RNG.randint(1, 320))).date().isoformat(),
            )
        )
    return students


def build_session_rows(students: list[Student], count: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    now = datetime.now()
    for index in range(count):
        student = RNG.choice(students)
        pc_id, pc_nombre, *_ = RNG.choice(PCS)
        inicio = now - timedelta(days=RNG.randint(0, 29), hours=RNG.randint(0, 8), minutes=RNG.randint(0, 59))
        duration_minutes = RNG.randint(10, 60)  # ninguna sesión dura más de una hora
        hora_fin = inicio + timedelta(minutes=duration_minutes)
        sincronizado = 1
        timestamp_sync = (hora_fin + timedelta(minutes=RNG.randint(1, 120))).isoformat(sep=" ", timespec="seconds")
        rows.append(
            {
                "id": f"demo-{pc_id.lower()}-{index:04d}",
                "pc_id": pc_id,
                "pc_nombre": pc_nombre,
                "carnet": student.carnet,
                "nombre": student.nombre,
                "carrera": student.carrera,
                "facultad": student.facultad,
                "sexo": student.sexo,
                "fecha_nacimiento": str(student.fecha_nacimiento),
                "hora_inicio": inicio.isoformat(sep=" ", timespec="seconds"),
                "hora_fin": hora_fin.isoformat(sep=" ", timespec="seconds"),
                "fecha": inicio.date().isoformat(),
                "sincronizado": sincronizado,
                "timestamp_sync": timestamp_sync,
            }
        )
    return rows


def reset_database(conn) -> None:
    for table in ("estado_pcs", "pcs_hardware", "sesiones", "pcs", "estudiantes"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def seed_students(conn, students: Iterable[Student]) -> None:
    for student in students:
        conn.execute(
            """
            INSERT INTO estudiantes (carnet, nombre, fecha_nacimiento, carrera, facultad, sexo, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                student.carnet,
                student.nombre,
                student.fecha_nacimiento,
                student.carrera,
                student.facultad,
                student.sexo,
                student.fecha_registro,
            ),
        )


def seed_pcs(conn) -> None:
    for pc_id, nombre, *_ in PCS:
        conn.execute("INSERT INTO pcs (pc_id, nombre, ultima_conexion, ip_reportada, ultimo_mantenimiento) VALUES (%s, %s, %s, %s, %s)", (pc_id, nombre, datetime.now().isoformat(sep=" ", timespec="seconds"), f"192.168.10.{RNG.randint(10, 80)}", (datetime.now() - timedelta(days=RNG.randint(10, 50))).isoformat(sep=" ", timespec="seconds")))


def seed_hardware(conn) -> None:
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    for pc_id, _, mac, cpu, ram, storage, os_name, temp, smart_ok, hours in PCS:
        conn.execute(
            """
            INSERT INTO pcs_hardware
                (pc_id, hostname, mac_address, cpu, ram_total_mb, almacenamiento_total_gb,
                 sistema_operativo, temperatura_cpu_c, disco_smart_ok, horas_uso_acumuladas, ultima_lectura)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pc_id,
                f"biblioteca-{pc_id.lower()}",
                mac,
                cpu,
                ram,
                storage,
                os_name,
                temp,
                smart_ok,
                hours,
                now,
            ),
        )


def seed_estado(conn, students: list[Student]) -> None:
    now = datetime.now()
    active_pcs = {"PC-01", "PC-03", "PC-05"}
    for index, (pc_id, pc_nombre, *_rest) in enumerate(PCS):
        active = pc_id in active_pcs
        student = students[index % len(students)] if active else None
        conn.execute(
            """
            INSERT INTO estado_pcs (pc_id, pc_nombre, sesion_activa, carnet, nombre, hora_inicio, ultima_actualizacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pc_id,
                pc_nombre,
                1 if active else 0,
                student.carnet if student else None,
                student.nombre if student else None,
                (now - timedelta(minutes=RNG.randint(5, 55))).isoformat(sep=" ", timespec="seconds") if active else None,
                now.isoformat(sep=" ", timespec="seconds"),
            ),
        )


def seed_sessions(conn, rows: list[dict[str, object]]) -> None:
    for row in rows:
        conn.execute(
            """
            INSERT INTO sesiones
                (id, pc_id, carnet, hora_inicio, hora_fin, fecha, sincronizado, timestamp_sync)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row["id"],
                row["pc_id"],
                row["carnet"],
                row["hora_inicio"],
                row["hora_fin"],
                row["fecha"],
                row["sincronizado"],
                row["timestamp_sync"],
            ),
        )


def main() -> None:
    args = parse_args()
    init_db()

    students = build_students(args.students)
    session_rows = build_session_rows(students, args.sessions)

    with conexion() as conn:
        if args.reset:
            reset_database(conn)

        seed_students(conn, students)
        seed_pcs(conn)
        seed_hardware(conn)
        seed_estado(conn, students)
        seed_sessions(conn, session_rows)
        conn.commit()

    print(
        f"Seed completado: {len(students)} estudiantes, {len(PCS)} PCs, "
        f"{len(session_rows)} sesiones y estado/hardware de demostración."
    )


if __name__ == "__main__":
    main()
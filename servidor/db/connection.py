import os
from contextlib import contextmanager

import pymysql
import pymysql.cursors

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "biblioteca")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "biblioteca")
DB_NAME = os.environ.get("DB_NAME", "biblioteca")

# Ruta (dentro del contenedor) a un certificado CA para cifrar la conexión a
# MySQL. Vacío = conexión en texto plano, sin impacto mientras "db" y
# "servidor" compartan la red interna de Docker (caso por defecto de este
# repo). Solo hace falta fijarla si la base de datos se aloja fuera de esa
# red (managed DB en la nube, otra máquina): apuntarla al CA cert que dé el
# proveedor de la base de datos.
DB_SSL_CA = os.environ.get("DB_SSL_CA") or None


class ConnectionWrapper:
    """Envuelve la conexion de pymysql para exponer conn.execute(), como sqlite3."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        return cursor

    def executescript(self, script):
        cursor = self._conn.cursor()
        for statement in script.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_connection():
    ssl_args = {"ssl_ca": DB_SSL_CA, "ssl_verify_cert": True} if DB_SSL_CA else {}
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        **ssl_args,
    )
    return ConnectionWrapper(conn)


@contextmanager
def conexion():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

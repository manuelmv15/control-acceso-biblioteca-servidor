#!/usr/bin/env python3
"""Genera el hash de la contraseña INICIAL del panel de administración.

`ADMIN_USER`/`ADMIN_PASS_HASH` del `.env` solo se usan una vez, para crear
el primer administrador en la base de datos (tabla `admins`) si está vacía
— ver `db/schema.py::_sembrar_admin_inicial`. Después de ese primer login,
el administrador cambia su contraseña desde el panel ("Cambiar contraseña",
`PUT /auth/password`) y el `.env` queda obsoleto.

Este script sirve para fijar esa contraseña inicial sin que quien hace el
despliegue la vea en texto plano: ejecutalo en TU máquina — no en el
servidor de despliegue — y copiale solo la línea `ADMIN_PASS_HASH=...`
resultante (mismo principio que el PIN de administrador del kiosko, ver
../biblioteca_cliente/cliente/setup.py). Si no te importa que quien
despliega conozca la contraseña inicial (total, se cambia después), podés
saltarte este script y usar directamente el hash de ejemplo del
`.env.example`.

Uso:
    python3 generar_hash_admin.py
"""
import getpass
import hashlib
import secrets
import sys

ITERACIONES = 600_000  # recomendación OWASP (2023+) para PBKDF2-HMAC-SHA256


def generar_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${salt.hex()}${derivado.hex()}"


def main() -> None:
    password = getpass.getpass("Contraseña de administrador (no se muestra en pantalla): ").strip()
    if not password:
        sys.exit("La contraseña no puede estar vacía.")
    confirmacion = getpass.getpass("Confírmala: ").strip()
    if password != confirmacion:
        sys.exit("Las contraseñas no coinciden.")

    print("\nAgrega esta línea al .env del servidor:\n")
    print(f"ADMIN_PASS_HASH={generar_hash(password)}")
    print("\n(No compartas la contraseña en texto plano — solo esta línea con el hash.)")


if __name__ == "__main__":
    main()

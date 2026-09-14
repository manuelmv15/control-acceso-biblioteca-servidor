import os
import sys
from pathlib import Path

# Los módulos de la app (routers, db, models) se importan como paquetes de
# nivel superior (`from routers import auth`, no `from servidor.routers...`),
# así que hace falta el directorio `servidor/` en sys.path — igual que
# cuando corre main.py con `servidor/` como cwd (ver Dockerfile/uvicorn).
SERVIDOR_DIR = Path(__file__).resolve().parents[1]
if str(SERVIDOR_DIR) not in sys.path:
    sys.path.insert(0, str(SERVIDOR_DIR))

# routers/auth.py exige SECRET_KEY al importarse (`_require_env`) y falla con
# RuntimeError si falta. Se fija acá, antes de que cualquier test importe el
# módulo, para no depender de un .env real ni de variables de entorno puestas
# a mano al correr pytest.
os.environ.setdefault("SECRET_KEY", "clave-de-prueba-solo-para-tests-no-usar-en-produccion")

# db/connection.py exige DB_USER y DB_PASSWORD al importarse (mismo patrón
# `_require_env` que SECRET_KEY, ver B2 en AUDITORIA.md) y `db/__init__.py`
# importa `connection` en cadena, así que hasta los tests que no tocan MySQL
# (test_auth.py, test_umbrales.py) disparan esa validación solo con
# `from routers import auth` / `from db import ...`. Se fijan acá por el
# mismo motivo que SECRET_KEY: no depender de un .env real ni de variables
# puestas a mano al correr pytest. Ningún test abre una conexión real a
# MySQL con estos valores.
os.environ.setdefault("DB_USER", "usuario-de-prueba-solo-para-tests")
os.environ.setdefault("DB_PASSWORD", "clave-de-prueba-solo-para-tests")

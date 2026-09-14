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

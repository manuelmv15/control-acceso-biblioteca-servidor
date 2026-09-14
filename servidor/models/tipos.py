from typing import Literal

# Mismas opciones que ofrece el selector de género del formulario de registro
# del kiosko (ver GENEROS en cliente/ui/registro.py). Se centralizan aquí para
# que todos los modelos que reciben "sexo" desde el kiosko (alta/edición de
# estudiantes, sync de sesiones, estado de PC) validen contra el mismo
# catálogo en vez de aceptar cualquier texto.
SEXOS_VALIDOS = ("M", "F", "LGBTIQ+", "N/D")
SexoValido = Literal[*SEXOS_VALIDOS]

# Formato permitido para un `pc_id` (letras, dígitos, guion y guion bajo — cubre
# tanto los IDs legibles asignados a mano, p. ej. "PC-01", como el UUID4 que
# genera `cliente/setup.py::generar_pc_id()`). Se centraliza acá para validarlo
# igual en todos los puntos donde el servidor lo recibe (payloads de
# estado/sync/hardware, header `X-PC-Id`, path `/pcs/{pc_id}/...`): sin este
# patrón, un `pc_id` con saltos de línea u otros caracteres de control llegaba
# intacto hasta los logs (`routers/pcs.py`, `routers/auth.py`, `routers/
# estudiantes.py`), donde alguien podía usarlo para forjar líneas de log falsas.
PC_ID_PATTERN = r"^[A-Za-z0-9_-]{1,100}$"

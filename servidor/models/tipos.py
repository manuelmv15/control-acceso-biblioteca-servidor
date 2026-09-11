from typing import Literal

# Mismas opciones que ofrece el selector de género del formulario de registro
# del kiosko (ver GENEROS en cliente/ui/registro.py). Se centralizan aquí para
# que todos los modelos que reciben "sexo" desde el kiosko (alta/edición de
# estudiantes, sync de sesiones, estado de PC) validen contra el mismo
# catálogo en vez de aceptar cualquier texto.
SEXOS_VALIDOS = ("M", "F", "LGBTIQ+", "N/D")
SexoValido = Literal[*SEXOS_VALIDOS]

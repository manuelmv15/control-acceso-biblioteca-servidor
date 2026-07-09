from pydantic import BaseModel
from typing import Optional


class Estudiante(BaseModel):
    nombre: str
    carnet: str
    fecha_nacimiento: Optional[str] = None
    carrera: Optional[str] = None
    departamento: Optional[str] = None
    facultad: Optional[str] = None
    sexo: Optional[str] = None
    fecha_registro: Optional[str] = None

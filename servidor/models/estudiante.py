from pydantic import BaseModel, Field
from typing import Optional

from .tipos import SexoValido


class Estudiante(BaseModel):
    nombre: str = Field(max_length=255)
    carnet: str = Field(max_length=30, pattern=r"^[A-Z]{2}\d{5}$")
    fecha_nacimiento: Optional[str] = Field(default=None, max_length=10)
    carrera: Optional[str] = Field(default=None, max_length=255)
    facultad: Optional[str] = Field(default=None, max_length=255)
    sexo: Optional[SexoValido] = None
    fecha_registro: Optional[str] = Field(default=None, max_length=10)

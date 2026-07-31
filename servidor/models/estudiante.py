from pydantic import BaseModel, Field
from typing import Optional


class Estudiante(BaseModel):
    nombre: str = Field(max_length=255)
    carnet: str = Field(max_length=30)
    fecha_nacimiento: Optional[str] = Field(default=None, max_length=10)
    carrera: Optional[str] = Field(default=None, max_length=255)
    facultad: Optional[str] = Field(default=None, max_length=255)
    sexo: Optional[str] = Field(default=None, max_length=20)
    fecha_registro: Optional[str] = Field(default=None, max_length=10)

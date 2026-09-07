from pydantic import BaseModel, Field
from typing import Optional


class Sesion(BaseModel):
    id: str = Field(max_length=100)
    pc_id: str = Field(max_length=100)
    carnet: Optional[str] = Field(default=None, max_length=30, pattern=r"^[A-Z]{2}\d{5}$")
    hora_inicio: str = Field(max_length=32)
    hora_fin: Optional[str] = Field(default=None, max_length=32)
    fecha: str = Field(max_length=10)
    sincronizado: Optional[int] = 0
    timestamp_sync: Optional[str] = Field(default=None, max_length=32)
    nombre: Optional[str] = Field(default=None, max_length=255)
    carrera: Optional[str] = Field(default=None, max_length=255)
    facultad: Optional[str] = Field(default=None, max_length=255)
    sexo: Optional[str] = Field(default=None, max_length=20)
    fecha_nacimiento: Optional[str] = Field(default=None, max_length=10)

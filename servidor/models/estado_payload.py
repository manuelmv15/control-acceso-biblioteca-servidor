from pydantic import BaseModel, Field
from typing import Optional


class EstadoPayload(BaseModel):
    pc_id: str = Field(max_length=100)
    pc_nombre: Optional[str] = Field(default=None, max_length=255)
    sesion_activa: bool
    carnet: Optional[str] = Field(default=None, max_length=30)
    nombre: Optional[str] = Field(default=None, max_length=255)
    hora_inicio: Optional[str] = Field(default=None, max_length=32)
    carrera: Optional[str] = Field(default=None, max_length=255)
    facultad: Optional[str] = Field(default=None, max_length=255)
    sexo: Optional[str] = Field(default=None, max_length=20)
    fecha_nacimiento: Optional[str] = Field(default=None, max_length=10)

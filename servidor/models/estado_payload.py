from pydantic import BaseModel
from typing import Optional


class EstadoPayload(BaseModel):
    pc_id: str
    pc_nombre: Optional[str] = None
    sesion_activa: bool
    carnet: Optional[str] = None
    nombre: Optional[str] = None
    hora_inicio: Optional[str] = None
    carrera: Optional[str] = None
    facultad: Optional[str] = None
    departamento: Optional[str] = None
    sexo: Optional[str] = None
    fecha_nacimiento: Optional[str] = None

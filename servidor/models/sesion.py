from pydantic import BaseModel
from typing import Optional


class Sesion(BaseModel):
    id: str
    pc_id: str
    carnet: str
    hora_inicio: str
    hora_fin: Optional[str] = None
    fecha: str
    sincronizado: Optional[int] = 0
    timestamp_sync: Optional[str] = None
    nombre: Optional[str] = None
    carrera: Optional[str] = None
    facultad: Optional[str] = None
    departamento: Optional[str] = None
    sexo: Optional[str] = None
    fecha_nacimiento: Optional[str] = None

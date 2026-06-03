from pydantic import BaseModel
from typing import Optional, List


class Estudiante(BaseModel):
    id: Optional[str] = None
    nombre: str
    carnet: str
    fecha_nacimiento: Optional[str] = None
    carrera: Optional[str] = None
    departamento: Optional[str] = None
    facultad: Optional[str] = None
    sexo: Optional[str] = None
    fecha_registro: Optional[str] = None


class Sesion(BaseModel):
    id: str
    pc_id: str
    carnet: str
    hora_inicio: str
    hora_fin: Optional[str] = None
    fecha: str
    sincronizado: Optional[int] = 0
    timestamp_sync: Optional[str] = None


class SyncPayload(BaseModel):
    pc_id: str
    pc_nombre: Optional[str] = None
    ip: Optional[str] = None
    sesiones: List[Sesion]


class EstadoPayload(BaseModel):
    pc_id: str
    pc_nombre: Optional[str] = None
    sesion_activa: bool
    carnet: Optional[str] = None
    nombre: Optional[str] = None
    hora_inicio: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

from pydantic import BaseModel
from typing import Optional, List

from .sesion import Sesion


class SyncPayload(BaseModel):
    pc_id: str
    pc_nombre: Optional[str] = None
    ip: Optional[str] = None
    sesiones: List[Sesion]

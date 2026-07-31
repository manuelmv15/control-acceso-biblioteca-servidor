import os
from pydantic import BaseModel, Field
from typing import Optional, List

from .sesion import Sesion

SYNC_MAX_SESIONES = int(os.environ.get("SYNC_MAX_SESIONES") or 500)


class SyncPayload(BaseModel):
    pc_id: str = Field(max_length=100)
    pc_nombre: Optional[str] = Field(default=None, max_length=255)
    ip: Optional[str] = Field(default=None, max_length=45)
    sesiones: List[Sesion] = Field(max_length=SYNC_MAX_SESIONES)

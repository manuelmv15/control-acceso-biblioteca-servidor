import os
from pydantic import BaseModel, Field
from typing import Optional, List

from .sesion import Sesion

SYNC_MAX_SESIONES = int(os.environ.get("SYNC_MAX_SESIONES") or 500)


class SyncPayload(BaseModel):
    pc_id: str
    pc_nombre: Optional[str] = None
    ip: Optional[str] = None
    sesiones: List[Sesion] = Field(max_length=SYNC_MAX_SESIONES)

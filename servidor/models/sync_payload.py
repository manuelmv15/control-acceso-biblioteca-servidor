import os
from typing import Optional

from pydantic import BaseModel, Field

from .sesion import Sesion
from .tipos import PC_ID_PATTERN

SYNC_MAX_SESIONES = int(os.environ.get("SYNC_MAX_SESIONES") or 500)


class SyncPayload(BaseModel):
    pc_id: str = Field(max_length=100, pattern=PC_ID_PATTERN)
    pc_nombre: Optional[str] = Field(default=None, max_length=255)
    ip: Optional[str] = Field(default=None, max_length=45)
    sesiones: list[Sesion] = Field(max_length=SYNC_MAX_SESIONES)

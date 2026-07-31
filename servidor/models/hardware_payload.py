from pydantic import BaseModel, Field
from typing import Optional


class HardwarePayload(BaseModel):
    hostname: Optional[str] = Field(default=None, max_length=255)
    mac: Optional[str] = Field(default=None, max_length=20)
    cpu: Optional[str] = Field(default=None, max_length=255)
    ram_total_mb: Optional[int] = None
    almacenamiento_total_gb: Optional[int] = None
    sistema_operativo: Optional[str] = Field(default=None, max_length=255)
    temperatura_cpu_c: Optional[float] = None
    disco_smart_ok: Optional[bool] = None
    horas_uso_acumuladas: float
    ultima_lectura: Optional[str] = Field(default=None, max_length=32)

from pydantic import BaseModel
from typing import Optional


class HardwarePayload(BaseModel):
    hostname: Optional[str] = None
    mac: Optional[str] = None
    cpu: Optional[str] = None
    ram_total_mb: Optional[int] = None
    almacenamiento_total_gb: Optional[int] = None
    sistema_operativo: Optional[str] = None
    temperatura_cpu_c: Optional[float] = None
    disco_smart_ok: Optional[bool] = None
    horas_uso_acumuladas: float
    ultima_lectura: Optional[str] = None

"""Métricas Prometheus para `GET /metrics` (opcional, ver `ENABLE_METRICS` en
`main.py`). No había ninguna métrica ni alerta en la app más allá del
`HEALTHCHECK` de Docker -- esto agrega lo mínimo útil para monitorear el
servicio desde afuera: cuántos requests atendió cada endpoint, con qué
código de estado, y cuánto tardaron. No expone nada de negocio (conteos de
estudiantes, sesiones, etc.) ni PII -- solo tráfico HTTP agregado."""
import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total de requests HTTP procesados",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Duración de requests HTTP en segundos",
    ["method", "path"],
)


def _path_template(request) -> str:
    """Usa el patrón de ruta declarado en el router ("/estudiantes/{carnet}"),
    no la URL real ("/estudiantes/AB12345") -- de lo contrario cada carnet o
    pc_id distinto generaría una serie de tiempo nueva (cardinalidad sin
    límite, el problema clásico de instrumentar por path real). Para un 404
    (nada matcheó) no hay `route` en el scope; se agrupan todos bajo
    "unmatched" en vez de explotar igual con cada URL inventada por un
    escaneo automatizado."""
    route = request.scope.get("route")
    return route.path if route is not None else "unmatched"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Registrado solo si `ENABLE_METRICS` está activo (ver main.py) -- así
    no hay overhead ni superficie nueva cuando nadie lo pidió."""

    async def dispatch(self, request, call_next):
        inicio = time.perf_counter()
        response = await call_next(request)
        duracion = time.perf_counter() - inicio
        path = _path_template(request)
        REQUEST_COUNT.labels(request.method, path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, path).observe(duracion)
        return response


def metrics_payload() -> tuple[bytes, str]:
    """`(cuerpo, content_type)` para la respuesta de `GET /metrics`."""
    return generate_latest(), CONTENT_TYPE_LATEST

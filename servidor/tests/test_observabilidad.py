"""Tests de observabilidad.py (métricas Prometheus de GET /metrics, ver
ENABLE_METRICS en main.py). Se prueba contra una app FastAPI mínima propia,
no main.app: main.py decide si registra el middleware/ruta según
ENABLE_METRICS al importarse, una sola vez -- fijar esa variable después de
que el resto de la suite ya importó main no tendría ningún efecto."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from observabilidad import MetricsMiddleware, metrics_payload


def _app():
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)

    @app.get("/saludo/{nombre}")
    def saludo(nombre: str):
        return {"hola": nombre}

    return app


def test_metrics_payload_registra_metodo_ruta_y_status():
    client = TestClient(_app())
    client.get("/saludo/mundo")
    cuerpo, content_type = metrics_payload()
    assert "text/plain" in content_type
    texto = cuerpo.decode()
    assert 'http_requests_total{method="GET",path="/saludo/{nombre}",status="200"}' in texto
    assert 'http_request_duration_seconds_count{method="GET",path="/saludo/{nombre}"}' in texto


def test_metrics_agrupa_por_patron_de_ruta_no_por_url_real():
    # Dos requests con valores de path distintos deben caer en la MISMA
    # serie de tiempo (el patrón de la ruta) -- de lo contrario cada
    # carnet/pc_id/nombre real generaría una serie nueva sin límite.
    client = TestClient(_app())
    client.get("/saludo/ana")
    client.get("/saludo/beto")
    cuerpo, _ = metrics_payload()
    texto = cuerpo.decode()
    assert 'path="/saludo/{nombre}"' in texto
    assert "ana" not in texto
    assert "beto" not in texto


def test_metrics_agrupa_404_bajo_unmatched():
    client = TestClient(_app())
    client.get("/esta-ruta-no-existe")
    cuerpo, _ = metrics_payload()
    texto = cuerpo.decode()
    assert 'path="unmatched",status="404"' in texto
    assert "esta-ruta-no-existe" not in texto

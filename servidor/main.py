from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
import os

from db import init_db
from routers import auth, sync, estudiantes, reportes, estado, pcs, hardware

app = FastAPI(title="Biblioteca Control", version="1.0.0")

CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
MAX_BODY_SIZE_BYTES = int(os.environ.get("MAX_BODY_SIZE_BYTES") or 5_000_000)


class LimitBodySizeMiddleware(BaseHTTPMiddleware):
    """Rechaza requests con body antes de que FastAPI/Pydantic los procesen.

    Un request sin `Content-Length` ni `Transfer-Encoding` no tiene body
    (p. ej. `POST /pcs/{id}/mantenimiento`, que el panel llama sin body) y se
    deja pasar. Si declara `Transfer-Encoding: chunked` sin `Content-Length`
    se rechaza (411): no hay forma barata de acotar su tamaño sin leerlo
    completo, y permitirlo abriría el mismo bypass que este middleware busca
    cerrar. Con `Content-Length` presente, se compara contra
    `MAX_BODY_SIZE_BYTES` sin necesidad de leer el body completo en memoria.
    """

    async def dispatch(self, request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length is None:
                if request.headers.get("transfer-encoding") is not None:
                    return Response("Content-Length requerido", status_code=411)
            elif int(content_length) > MAX_BODY_SIZE_BYTES:
                return Response("Payload demasiado grande", status_code=413)
        return await call_next(request)


app.add_middleware(LimitBodySizeMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(estudiantes.router)
app.include_router(reportes.router)
app.include_router(estado.router)
app.include_router(pcs.router)
app.include_router(hardware.router)

panel_path = os.path.join(os.path.dirname(__file__), "panel")
if os.path.isdir(panel_path):
    app.mount("/panel", StaticFiles(directory=panel_path, html=True), name="panel")

    @app.get("/")
    def root():
        return FileResponse(os.path.join(panel_path, "index.html"))


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}

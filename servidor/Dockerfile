FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

# H7: uvicorn no debe correr como root dentro del contenedor — limita el
# impacto de un eventual RCE al privilegio de un usuario sin permisos.
RUN useradd --create-home --shell /usr/sbin/nologin app \
    && chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]

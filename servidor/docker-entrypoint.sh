#!/bin/sh
# Entrypoint del contenedor `servidor`.
#
# Si docker-compose (u otro caller) pasa un comando explícito — como hace
# docker-compose.yml (desarrollo) con `command: ["uvicorn", ..., "--reload"]`
# — se ejecuta tal cual, sin tocarlo: así el flujo de desarrollo actual no
# cambia en nada.
#
# Si no se pasa comando (caso de docker-compose.prod.yml, que no define
# `command:`), arma la invocación de uvicorn acá mismo, agregando
# --ssl-certfile/--ssl-keyfile cuando TLS_CERT_PATH/TLS_KEY_PATH están
# configuradas (ver scripts/generar_ca.sh y docs/desarrollo/despliegue.md,
# sección TLS) — H1 del informe de auditoría: sin esto, el tráfico entre los
# kioscos y este servidor viaja sin cifrar por la LAN.
set -e

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

ARGS="main:app --host 0.0.0.0 --port 8000"

if [ "${UVICORN_RELOAD:-}" = "1" ] || [ "${UVICORN_RELOAD:-}" = "true" ]; then
    ARGS="$ARGS --reload"
fi

if [ -n "${TLS_CERT_PATH:-}" ] && [ -n "${TLS_KEY_PATH:-}" ]; then
    if [ ! -f "$TLS_CERT_PATH" ] || [ ! -f "$TLS_KEY_PATH" ]; then
        echo "TLS_CERT_PATH/TLS_KEY_PATH están configuradas pero el archivo no existe (¿montaste el volumen de certs?) — abortando." >&2
        exit 1
    fi
    ARGS="$ARGS --ssl-certfile $TLS_CERT_PATH --ssl-keyfile $TLS_KEY_PATH"
elif [ -n "${TLS_CERT_PATH:-}" ] || [ -n "${TLS_KEY_PATH:-}" ]; then
    echo "Solo una de TLS_CERT_PATH/TLS_KEY_PATH está configurada — hacen falta las dos, o ninguna. Abortando." >&2
    exit 1
fi

# shellcheck disable=SC2086  # $ARGS se arma en este script, sin datos externos sin validar
exec uvicorn $ARGS

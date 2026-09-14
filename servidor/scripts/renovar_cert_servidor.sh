#!/usr/bin/env bash
set -euo pipefail

# Renueva SOLO el certificado de servidor (server.key/server.pem), reusando
# la CA interna ya existente (ca.key/ca.pem) generada por generar_ca.sh.
# A diferencia de correr generar_ca.sh otra vez (que exige borrar la CA a
# mano y generaría una CA NUEVA), esto no invalida la confianza que ya
# tienen configurada los kioscos -- ca.pem no cambia, así que no hace falta
# volver a copiarlo a ninguno de los 16 kioscos.
#
# Uso:
#   ./servidor/scripts/renovar_cert_servidor.sh <IP-o-hostname-del-servidor> [directorio-certs]
#
# Por defecto usa <raíz del repo>/certs (mismo default que generar_ca.sh).
# server.key/server.pem viejos quedan respaldados como server.key.bak /
# server.pem.bak (se sobreescribe el respaldo anterior si corrés esto dos
# veces sin borrarlos).

if ! command -v openssl >/dev/null 2>&1; then
    echo "ERROR: openssl no está instalado." >&2
    exit 1
fi

if [[ $# -lt 1 ]]; then
    echo "Uso: $0 <IP-o-hostname-del-servidor> [directorio-certs]" >&2
    echo "Ejemplo: $0 192.168.10.5" >&2
    exit 1
fi

HOST="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${2:-$SCRIPT_DIR/../../certs}"

if [[ ! -f "$OUT_DIR/ca.key" || ! -f "$OUT_DIR/ca.pem" ]]; then
    echo "No se encontró una CA en $OUT_DIR (ca.key/ca.pem)." >&2
    echo "Este script renueva el certificado de servidor reusando una CA ya" >&2
    echo "generada -- para crear la CA por primera vez, usá generar_ca.sh." >&2
    exit 1
fi

OUT_DIR="$(cd "$OUT_DIR" && pwd)"
cd "$OUT_DIR"

if [[ -f server.key || -f server.pem ]]; then
    echo "Respaldando server.key/server.pem actuales como *.bak..."
    cp -f server.key server.key.bak 2>/dev/null || true
    cp -f server.pem server.pem.bak 2>/dev/null || true
fi

echo "=== Emitiendo nuevo certificado de servidor para '$HOST' (misma CA) ==="
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=$HOST"

if [[ "$HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    SAN="IP:$HOST"
else
    SAN="DNS:$HOST"
fi
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
    -out server.pem -days 825 -sha256 \
    -extfile <(printf "subjectAltName=%s" "$SAN")
rm -f server.csr ca.srl

chmod 600 server.key
chmod 644 server.pem

echo ""
echo "=== Listo ==="
echo "server.key/server.pem renovados en $OUT_DIR (vencen en ~825 días)."
echo "ca.pem NO cambió -- los kioscos ya configurados siguen confiando en este"
echo "certificado sin ningún cambio de su lado."
echo ""
echo "Reiniciá el contenedor 'servidor' para que uvicorn cargue el certificado nuevo:"
echo "  docker compose -f docker-compose.prod.yml restart servidor"

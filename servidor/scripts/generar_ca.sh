#!/usr/bin/env bash
set -euo pipefail

# Genera una CA interna propia y un certificado de servidor firmado por ella,
# para cifrar el tráfico entre los kioscos (biblioteca_cliente) y este
# servidor dentro de la LAN del laboratorio. No hay dominio público, solo
# una IP interna, así que no aplica una CA pública tipo Let's Encrypt — ver
# docs/desarrollo/despliegue.md, sección TLS.
#
# Se corre UNA VEZ en la PC maestra (o en cualquier máquina con openssl, y
# luego copiás los archivos a la PC maestra).
#
# Uso:
#   ./scripts/generar_ca.sh <IP-o-hostname-del-servidor> [directorio-salida]
#
# Ejemplo:
#   ./scripts/generar_ca.sh 192.168.10.5
#
# Genera, en el directorio de salida (por defecto ./certs, relativo a este
# script):
#   ca.key     — clave privada de la CA. GUARDAR OFFLINE (USB, gestor de
#                contraseñas), NO subir a git, NO hace falta en el servidor
#                una vez que existe server.pem — solo se necesita de nuevo
#                para firmar un futuro certificado de servidor o revocar.
#   ca.pem     — certificado público de la CA. Copiar a cada kiosko
#                (biblioteca_cliente/cliente/ca.pem, ver
#                config.ini -> [servidor] ca_cert).
#   server.key — clave privada del servidor. Queda en la PC maestra, NUNCA
#                se distribuye a los kioscos. TLS_KEY_PATH en el .env del
#                servidor.
#   server.pem — certificado del servidor firmado por la CA. TLS_CERT_PATH
#                en el .env del servidor.

if [[ $# -lt 1 ]]; then
    echo "Uso: $0 <IP-o-hostname-del-servidor> [directorio-salida]" >&2
    echo "Ejemplo: $0 192.168.10.5" >&2
    exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
    echo "ERROR: openssl no está instalado." >&2
    exit 1
fi

HOST="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Default: <raíz del repo>/certs (junto a docker-compose.prod.yml y .env),
# NO servidor/certs — ese directorio es el build context de la imagen
# Docker (servidor/Dockerfile hace `COPY . .`) y no queremos que las claves
# privadas terminen empacadas ahí adentro por accidente.
OUT_DIR="${2:-$SCRIPT_DIR/../../certs}"
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

if [[ -f "$OUT_DIR/ca.key" || -f "$OUT_DIR/ca.pem" ]]; then
    echo "Ya existe una CA en $OUT_DIR (ca.key/ca.pem)." >&2
    echo "Borrala a mano si querés regenerarla — ojo: regenerarla invalida el" >&2
    echo "certificado de todos los kioscos ya configurados con el ca.pem viejo," >&2
    echo "hay que volver a copiarles el nuevo." >&2
    exit 1
fi

cd "$OUT_DIR"

echo "=== Generando CA interna en $OUT_DIR ==="
openssl genrsa -out ca.key 4096
# -addext keyUsage: sin esta extensión, OpenSSL 3.2+ (validación estricta de
# cadena, ver X509_V_FLAG_X509_STRICT) rechaza este CA para verificar el
# certificado del servidor con "CA cert does not include key usage
# extension" — falla silenciosa en el cliente porque hay_conexion() traga
# cualquier excepción y la reporta solo como "sin conexión".
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
    -out ca.pem -subj "/CN=Biblioteca UES CA" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -addext "basicConstraints=critical,CA:true"

echo ""
echo "=== Generando certificado del servidor para '$HOST' ==="
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

chmod 600 ca.key server.key
chmod 644 ca.pem server.pem

echo ""
echo "=== Listo ==="
echo "Archivos generados en $OUT_DIR:"
ls -1 "$OUT_DIR"
echo ""
echo "En el servidor (.env):"
echo "  TLS_CERT_PATH=/certs/server.pem"
echo "  TLS_KEY_PATH=/certs/server.key"
echo "  (docker-compose.prod.yml monta $OUT_DIR en /certs dentro del contenedor —"
echo "   ajustá TLS_CERTS_DIR en el .env si moviste este directorio)"
echo ""
echo "En cada kiosko (biblioteca_cliente):"
echo "  Copiá $OUT_DIR/ca.pem a cliente/ca.pem"
echo "  En config.ini: [servidor] url = https://$HOST:8000 , ca_cert = ca.pem"
echo ""
echo "IMPORTANTE:"
echo "  - ca.key es la clave privada de la CA: no la distribuyas, no la subas a git,"
echo "    guardala offline. Sin ella no podés firmar un futuro certificado de servidor."
echo "  - server.pem vence en ~825 días (2.25 años) — calendarizá su renovación"
echo "    (volvé a correr este script, o solo la parte de 'certificado del servidor'"
echo "    reusando la misma CA)."

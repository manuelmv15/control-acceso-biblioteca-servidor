#!/usr/bin/env bash
set -euo pipefail

# Alerta cuando el certificado de servidor (generado por generar_ca.sh) o la
# CA interna están cerca de vencer. No hay renovación automática posible acá
# a diferencia de una CA pública (Let's Encrypt, etc.): renovar significa
# volver a correr generar_ca.sh y, si rotó la CA (no solo el certificado de
# servidor), redistribuir el nuevo ca.pem a los 16 kioscos a mano -- por eso
# este script solo AVISA con suficiente anticipación, no reemplaza nada.
#
# Uso:
#   ./servidor/scripts/verificar_vencimiento_cert.sh [directorio-certs] [dias-de-aviso]
#
# Por defecto revisa ./certs (relativo al directorio desde donde se corre,
# normalmente la raíz del repo) con 60 días de margen. Sale con código != 0
# si algún certificado está vencido o vence dentro del margen, para que un
# cron pueda usarlo como chequeo (mailea la salida de cron por defecto en la
# mayoría de sistemas si el comando falla).
#
# Ejemplo (chequeo semanal, lunes 8am):
#   0 8 * * 1 cd /ruta/al/repo && ./servidor/scripts/verificar_vencimiento_cert.sh

DIR_CERTS="${1:-./certs}"
DIAS_AVISO="${2:-60}"

if [ ! -d "$DIR_CERTS" ]; then
    echo "No existe el directorio '$DIR_CERTS' -- ¿corriste esto desde la raíz del repo?" >&2
    exit 1
fi

HOY_EPOCH="$(date +%s)"
FALLO=0

verificar() {
    local archivo="$1"
    local etiqueta="$2"
    if [ ! -f "$archivo" ]; then
        return 0 # ca.pem no siempre existe si no se regeneró la CA -- no es un error acá
    fi
    local vencimiento_str
    vencimiento_str="$(openssl x509 -enddate -noout -in "$archivo" | cut -d= -f2)"
    local vencimiento_epoch
    vencimiento_epoch="$(date -d "$vencimiento_str" +%s)"
    local dias_restantes=$((( vencimiento_epoch - HOY_EPOCH ) / 86400))

    if [ "$dias_restantes" -lt 0 ]; then
        echo "VENCIDO: $etiqueta ($archivo) venció hace $(( -dias_restantes )) día(s) ($vencimiento_str)."
        FALLO=1
    elif [ "$dias_restantes" -le "$DIAS_AVISO" ]; then
        echo "AVISO: $etiqueta ($archivo) vence en $dias_restantes día(s) ($vencimiento_str). Renovar con generar_ca.sh y redistribuir a los kioscos si rotó la CA."
        FALLO=1
    else
        echo "OK: $etiqueta ($archivo) vence en $dias_restantes día(s) ($vencimiento_str)."
    fi
}

verificar "$DIR_CERTS/server.pem" "Certificado de servidor"
verificar "$DIR_CERTS/ca.pem" "CA interna"

exit "$FALLO"

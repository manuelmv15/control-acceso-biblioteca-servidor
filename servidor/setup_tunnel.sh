#!/usr/bin/env bash
set -euo pipefail

TUNNEL_NAME="biblioteca"
SERVICE_URL="http://localhost:8000"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    echo "SO no soportado: $OSTYPE"; exit 1
fi

echo "=== Configurando túnel Cloudflare para Biblioteca ==="

install_cloudflared_linux() {
    if command -v cloudflared &>/dev/null; then
        echo "cloudflared ya instalado: $(cloudflared --version)"
        return
    fi
    echo "Instalando cloudflared..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
    sudo dpkg -i /tmp/cloudflared.deb
    rm /tmp/cloudflared.deb
}

install_cloudflared_windows() {
    if command -v cloudflared &>/dev/null; then
        echo "cloudflared ya instalado"; return
    fi
    echo "Descargando cloudflared para Windows..."
    DEST="$USERPROFILE/cloudflared.exe"
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe -o "$DEST"
    echo "Guardado en $DEST — agregar al PATH manualmente o mover a C:\\Windows\\System32"
}

if [[ "$OS" == "linux" ]]; then
    install_cloudflared_linux
    echo ""
    echo "Autenticando con Cloudflare (abrirá el navegador)..."
    cloudflared tunnel login

    echo "Creando túnel '$TUNNEL_NAME'..."
    cloudflared tunnel create "$TUNNEL_NAME" || echo "El túnel ya existe"

    CREDS=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    mkdir -p "$(dirname "$0")/cloudflared"
    cat > "$(dirname "$0")/cloudflared/config.yml" <<EOF
tunnel: $TUNNEL_NAME
credentials-file: $HOME/.cloudflared/$CREDS.json

ingress:
  - service: $SERVICE_URL
EOF

    echo "Registrando cloudflared como servicio systemd..."
    cloudflared service install
    systemctl enable cloudflared
    systemctl start cloudflared
    echo "Túnel activo. URL pública disponible en el dashboard de Cloudflare."
else
    install_cloudflared_windows
    echo "En Windows: ejecutar manualmente 'cloudflared tunnel login' y luego 'cloudflared service install'"
fi

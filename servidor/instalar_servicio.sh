#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/biblioteca/servidor"
SERVICE_FILE="/etc/systemd/system/biblioteca.service"
VENV_DIR="/opt/biblioteca/venv"

if [[ "$EUID" -ne 0 ]]; then
    echo "Ejecutar como root: sudo bash instalar_servicio.sh"; exit 1
fi

echo "=== Instalando servidor Biblioteca ==="

# Crear usuario de sistema
id -u biblioteca &>/dev/null || useradd --system --no-create-home --shell /sbin/nologin biblioteca

# Instalar archivos
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"
chown -R biblioteca:biblioteca "$INSTALL_DIR"

# Virtualenv
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet

# Servicio systemd
cp biblioteca.service "$SERVICE_FILE"
sed -i "s|/opt/biblioteca/servidor|$INSTALL_DIR|g" "$SERVICE_FILE"
sed -i "s|/opt/biblioteca/venv|$VENV_DIR|g" "$SERVICE_FILE"

systemctl daemon-reload
systemctl enable biblioteca
systemctl start biblioteca
systemctl status biblioteca --no-pager

echo ""
echo "Servidor activo en http://localhost:8000"
echo "IMPORTANTE: Cambiar SECRET_KEY y ADMIN_PASS en $SERVICE_FILE"

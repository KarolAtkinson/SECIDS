#!/bin/bash
# Configure SecIDS WebUI as a persistent service on the database server.

set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$( cd "$( dirname "$SCRIPT_PATH" )" && pwd )"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done

SCRIPT_DIR="$( cd "$( dirname "$SCRIPT_PATH" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

if [ "${EUID}" -ne 0 ]; then
    echo "Run as root: sudo ./Launchers/setup_db_server_hosting.sh"
    exit 1
fi

APP_USER="${SECIDS_APP_USER:-secids}"
APP_GROUP="${SECIDS_APP_GROUP:-secids}"
APP_ROOT="${SECIDS_APP_ROOT:-/opt/secids/SECIDS-CNN}"
DB_ROOT="${SECIDS_SERVER_DB_ROOT:-/srv/secids/ServerDB}"
PUBLIC_HOSTNAME="${SECIDS_PUBLIC_HOSTNAME:-}"
SERVICE_SRC="$PROJECT_ROOT/Deploy/systemd/secids-webui.service"
SERVICE_DST="/etc/systemd/system/secids-webui.service"
NGINX_SRC="$PROJECT_ROOT/Deploy/nginx/secids-webui.conf"
NGINX_DST="/etc/nginx/sites-available/secids-webui"

PY_FOR_PATHS="${PROJECT_ROOT}/.venv_test/bin/python"
if [ ! -x "$PY_FOR_PATHS" ]; then
    PY_FOR_PATHS="$(command -v python3 || true)"
fi
if [ -z "${PY_FOR_PATHS}" ]; then
    echo "❌ python3 is required to resolve WebUI access/login paths"
    exit 1
fi

ACCESS_PATH="$($PY_FOR_PATHS - <<'PY'
from WebUI.app import create_app
app = create_app()
print(app.config.get('SECIDS_ACCESS_PATH', ''))
PY
)"
LOGIN_PATH="$($PY_FOR_PATHS - <<'PY'
from WebUI.app import create_app
app = create_app()
print(app.config.get('SECIDS_LOGIN_PATH', '/login'))
PY
)"

if ! id -u "$APP_USER" >/dev/null 2>&1; then
    useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"
fi

if ! getent group "$APP_GROUP" >/dev/null 2>&1; then
    groupadd --system "$APP_GROUP"
fi

mkdir -p "$APP_ROOT" "$DB_ROOT"
chown -R "$APP_USER:$APP_GROUP" "$DB_ROOT"

if [ "$PROJECT_ROOT" != "$APP_ROOT" ]; then
    rsync -a --delete \
      --exclude '.git' \
      --exclude '__pycache__' \
      --exclude '*.pyc' \
      "$PROJECT_ROOT/" "$APP_ROOT/"
fi

if [ ! -x "$APP_ROOT/.venv_test/bin/python" ]; then
    python3 -m venv "$APP_ROOT/.venv_test"
fi

"$APP_ROOT/.venv_test/bin/pip" install --upgrade pip >/dev/null
"$APP_ROOT/.venv_test/bin/pip" install -r "$APP_ROOT/requirements.txt"

cp "$SERVICE_SRC" "$SERVICE_DST"
sed -i "s|^User=.*|User=$APP_USER|" "$SERVICE_DST"
sed -i "s|^Group=.*|Group=$APP_GROUP|" "$SERVICE_DST"
sed -i "s|^WorkingDirectory=.*|WorkingDirectory=$APP_ROOT|" "$SERVICE_DST"
sed -i "s|^Environment=SECIDS_SERVER_DB_ROOT=.*|Environment=SECIDS_SERVER_DB_ROOT=$DB_ROOT|" "$SERVICE_DST"
sed -i "s|^ExecStart=.*|ExecStart=$APP_ROOT/.venv_test/bin/python WebUI/production_server.py|" "$SERVICE_DST"

if command -v nginx >/dev/null 2>&1; then
    cp "$NGINX_SRC" "$NGINX_DST"
    if [ -n "$PUBLIC_HOSTNAME" ]; then
        sed -i "s|server_name YOUR_DOMAIN_OR_IP;|server_name ${PUBLIC_HOSTNAME};|" "$NGINX_DST"
    fi
    if [ ! -e "/etc/nginx/sites-enabled/secids-webui" ]; then
        ln -s "$NGINX_DST" "/etc/nginx/sites-enabled/secids-webui"
    fi
    nginx -t
    systemctl restart nginx
fi

systemctl daemon-reload
systemctl enable secids-webui
systemctl restart secids-webui
systemctl --no-pager --full status secids-webui | sed -n '1,20p'

echo ""
echo "Setup complete. Service is persistent and will survive reboots."
echo "Check logs: journalctl -u secids-webui -f"
if [ -n "$PUBLIC_HOSTNAME" ]; then
    echo "Public WebUI URL: https://${PUBLIC_HOSTNAME}${ACCESS_PATH}"
    echo "Public Login URL: https://${PUBLIC_HOSTNAME}${LOGIN_PATH}"
else
    echo "Public WebUI URL: http://<server-ip>${ACCESS_PATH}"
    echo "Public Login URL: http://<server-ip>${LOGIN_PATH}"
fi

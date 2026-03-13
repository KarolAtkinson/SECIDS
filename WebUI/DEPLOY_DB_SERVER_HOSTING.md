# Host WebUI On Database Server (Persistent)

This makes WebUI run on your database server so it stays online even when your local device is off.

## What this does

- Runs WebUI as a `systemd` service (`secids-webui`)
- Uses the server's `ServerDB` path via `SECIDS_SERVER_DB_ROOT`
- Optionally exposes through Nginx reverse proxy
- Auto-starts after reboot

## Files added

- `Deploy/systemd/secids-webui.service`
- `Deploy/nginx/secids-webui.conf`
- `Launchers/setup_db_server_hosting.sh`

## Step-by-step on the database server

1. Copy project to the database server (or git clone there).
2. Run setup as root:

```bash
sudo ./Launchers/setup_db_server_hosting.sh
```

3. Confirm service status:

```bash
systemctl status secids-webui --no-pager
```

4. Follow logs:

```bash
journalctl -u secids-webui -f
```

5. If Nginx is installed, validate public route:

```bash
curl -I http://127.0.0.1
```

## Public access

- If using domain + Nginx: `https://your-domain/portal/<slug>/login`
- If direct port: `http://<db-server-public-ip>:8080/portal/<slug>/login`

Get active login path from server:

```bash
/opt/secids/SECIDS-CNN/.venv_test/bin/python - <<'PY'
from WebUI.app import create_app
app = create_app()
print(app.config.get('SECIDS_LOGIN_PATH', '/login'))
PY
```

## Maintenance

1. Update code on server.
2. Reinstall requirements if changed:

```bash
/opt/secids/SECIDS-CNN/.venv_test/bin/pip install -r /opt/secids/SECIDS-CNN/requirements.txt
```

3. Restart service:

```bash
sudo systemctl restart secids-webui
```

4. Verify service health and logs.

## Notes

- Set a strong `SECIDS_WEB_SECRET` in the service file before production.
- Use HTTPS (Let's Encrypt) if exposed publicly.
- Keep temporary guest users only during testing.

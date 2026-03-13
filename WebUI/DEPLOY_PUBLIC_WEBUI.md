# Public WebUI Deployment

This enables SecIDS-CNN WebUI to run as a real hosted webpage so guest users can test it without local code.

## Option 1: Deploy to a Cloud Host (Recommended)

Use a VPS or PaaS (Render, Railway, Fly.io, Azure App Service).

1. Push this repository to GitHub.
2. Create a new web service from the repo.
3. Set runtime values:

```bash
SECIDS_WEB_HOST=0.0.0.0
SECIDS_WEB_PORT=8080
SECIDS_WEB_OPEN_BROWSER=0
SECIDS_WEB_SECRET=<strong-random-secret>
SECIDS_AUTH_MAX_ATTEMPTS=5
SECIDS_AUTH_LOCKOUT_SECONDS=900
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Start command:

```bash
python WebUI/production_server.py
```

After deploy, share your provider URL with guest users.

## Option 2: Run on Your Own Server

From project root:

```bash
./Launchers/webui-public
```

Then expose `8080` behind Nginx/Caddy with HTTPS and a domain.

## Guest Accounts (Temporary)

Configured in `Config/webui_users.json`:

- `guest_school_tmp` / `SchoolTmp#2026`
- `guest_library_tmp` / `LibraryTmp#2026`
- `guest_restaurant_tmp` / `RestoTmp#2026`

Rotate or remove these after testing.

## Guest Point Of View: Step-By-Step Access

1. Open the shared URL in any browser (phone, tablet, or desktop).
2. The login page appears (`.../portal/<slug>/login`).
3. Sign in with one temporary account:
	- `guest_school_tmp` / `SchoolTmp#2026`
	- `guest_library_tmp` / `LibraryTmp#2026`
	- `guest_restaurant_tmp` / `RestoTmp#2026`
4. After login, switch between Realtime and Simulation.
5. In Simulation mode, choose architecture type (`School`, `Library`, `Restaurant`) and run a simulation.
6. Verify the page adapts to the current device screen size and orientation.
7. Log out using the top toolbar button when done.

## Operator Side: What You Need To Do Before Guests Test

1. Deploy and start production service.
2. Confirm service health from your side:

```bash
curl -I https://<your-domain>
```

3. Confirm login page is reachable:

```bash
curl -I https://<your-domain>/portal
```

4. Send guests only the URL and temporary credentials.
5. Keep admin credentials private.

## Ongoing Maintenance Checklist

### Daily/Session checks

1. Check process uptime and restart if needed.
2. Review `Logs/` and WebUI errors for failed jobs or repeated auth failures.
3. Confirm disk space if simulations produce datasets/reports.

### Weekly checks

1. Pull latest code and dependency updates.
2. Rebuild environment if requirements changed:

```bash
./.venv_test/bin/pip install -r requirements.txt
```

3. Restart production service after updates.
4. Validate login + simulation run path.

### Security hygiene

1. Remove or disable temporary guest users after testing.
2. Rotate `SECIDS_WEB_SECRET` periodically.
3. Enforce HTTPS and keep domain TLS certificates valid.
4. Keep lockout settings enabled:
	- `SECIDS_AUTH_MAX_ATTEMPTS`
	- `SECIDS_AUTH_LOCKOUT_SECONDS`

### Backup and rollback

1. Backup `Config/`, `ServerDB/`, and `Logs/` regularly.
2. Keep the previous deployment build available for quick rollback.

## Important Security Notes

- Keep `SECIDS_SINGLE_ADMIN_MODE` disabled for multi-user guest testing.
- Use HTTPS in production.
- Restrict admin account usage to trusted operators only.
- Remove temporary guest users when validation is complete.

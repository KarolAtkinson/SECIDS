# SecIDS-CNN Implementation & WebUI Upgrade Plan

## Objective
Maintain parity with the Kali terminal workflow while operating a hardened browser control plane, and keep the broader SECIDS-CNN project map synchronized with current implemented features.

## Project-Wide Feature Inventory (Current)

### Core Runtime & Interfaces
- Primary terminal UX: `UI/terminal_ui_enhanced.py`.
- Browser UX: `WebUI/app.py` + `WebUI/templates/index.html` + `WebUI/static/app.js` + `WebUI/static/style.css`.
- Root orchestration entry points: `Root/secids_main.py`, `Root/system_integrator.py`, `Root/integrated_workflow.py`.

### Detection / Data / Model Stack
- Model pipeline and training/testing in `SecIDS-CNN/` and `Model_Tester/Code/`.
- Capture/deep scan tooling in `Tools/` (`deep_scan.py`, `live_capture_and_assess.py`, `pipeline_orchestrator.py`, etc.).
- Dataset and command config under `Config/` (`dataset_config.json`, `command_shortcuts.json`, `command_history.json`).

### Countermeasures & Device Profiling
- Countermeasure architecture in `Countermeasures/` (`countermeasure_core.py`, `countermeasure_active.py`, `countermeasure_passive.py`, `ddos_countermeasure.py`).
- Trust/decision lists and reports in `Device_Profile/` (whitelist, greylist, blacklist, scans).

### Automation / Scheduling / Maintenance
- Auto-update and monitoring in `Auto_Update/` (`task_scheduler.py`, `git_auto_sync.py`, monitors, schedulers).
- Launch helpers in `Launchers/` and maintenance/debug scripts in `Scripts/`.

### Debugging & Reporting
- Deep debug tooling in `Scripts/production_debug_scan.py` and `Scripts/comprehensive_debug_scan.py`.
- Ongoing report outputs in `Reports/`, `Results/`, and `Stress_Test_Results/`.

## WebUI Architecture & Design (Implemented)
- Flask API backend with predefined action IDs only (no raw shell input from browser).
- Realtime/simulation execution, queueing, timeout policy, cancel/retry, and history rerun.
- Toolbar/panel design for scheduler, queue state, settings, history, audit, and users.
- Persistent UI settings (`UI/ui_config.json`) and command history integration (`Config/command_history.json`).

## Security & Access Control (Implemented)

### Completed Hardening
- Session identity + role enforcement for protected operations.
- Audit event stream and export endpoint.
- PBKDF2 password hashing, login lockout, and password-change enforcement gates.
- Password age policy support (`SECIDS_AUTH_MAX_AGE_DAYS`).

### New Upgrade (This Cycle)
- **Single-admin login mode** enabled in `WebUI/app.py`.
- Dedicated login page at `/login` via `WebUI/templates/login.html`.
- Fixed single user for admin access:
  - username: `kali`
  - password: `uclb()w1V`
- Web root (`/`) now redirects unauthenticated users to `/login`.
- API authentication gate added for protected API routes.
- User-management mutation APIs are disabled in single-admin mode.

## Live View / Live-Server-Like Workflow (New)
- Added `WebUI/live_server.py`:
  - Runs WebUI with Flask debug auto-reload.
  - Opens browser automatically (configurable).
  - Default URL: `http://127.0.0.1:8080/login`.

## Operational Commands

### Standard WebUI
```bash
.venv_test/bin/python WebUI/app.py
```

### Live View Mode (Auto-reload + browser open)
```bash
.venv_test/bin/python WebUI/live_server.py
```

Optional env vars:
- `SECIDS_WEB_HOST` (default `127.0.0.1`)
- `SECIDS_WEB_PORT` (default `8080`)
- `SECIDS_WEB_OPEN_BROWSER` (`1`/`0`)

## Deep Debug Plan
- Run comprehensive deep scan using `Scripts/comprehensive_debug_scan.py`.
- Review generated JSON/TXT artifacts in `Reports/`.
- Feed actionable errors back into targeted fixes.

## Next Recommended Steps
1. Add HTTPS reverse proxy + systemd for persistent WebUI service.
2. Add explicit account lock/unlock dashboard indicators.
3. Add optional MFA when single-admin mode is disabled.

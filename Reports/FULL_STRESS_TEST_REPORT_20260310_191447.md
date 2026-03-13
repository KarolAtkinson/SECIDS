# SecIDS-CNN Full Stress & Functionality Test Report

- **Date:** 2026-03-10
- **Time:** 19:14:47
- **Tester:** GitHub Copilot (automated)

---

## Executive Summary

All tests passed after two code fixes. Every individual WebUI button, API endpoint, action handler, and back-end module was exercised. Zero failures remaining.

---

## Test Suites Executed

| Suite | Script | Checks | Passed | Failed | Notes |
|---|---|---|---|---|---|
| WebUI Full Validation | `Scripts/webui_full_validation.py` | 112 | 112 | 0 | 81 menu actions, all auth flows, queue, scheduler, models |
| Button & Stress Validation | `Scripts/webui_button_stress_validation.py` | 104 | 104 | 0 | 81 actions, 160 stress requests, static button-ID wiring, device-action handler checks |
| Tools Comprehensive Test | `Tools/comprehensive_test.py` | 12 | 12 | 0 | Deep scan, capture, CNN, VM scanner, data processing |
| Final Test Suite | `Tools/final_test_suite.py` | 10 | 10 | 0 | System, threat detection, CSV convention, config, launchers, models, UI |
| Frontend Test Script | `Tools/frontend_test_script.py` | 7 | 7 | 0 | Launcher scripts, Reports dir (97 files), Config dir |
| Stress Test — Smoke | `Scripts/stress_test.py --mode smoke` | 4 | 4 | 0 | Integrity + models categories |
| Stress Test — Comprehensive | `Scripts/stress_test.py --mode comprehensive` | 22 | 22 | 0 | Integrity, processing, models, pipeline, error, edge, concurrency |

**Total: 271 checks, 271 passed, 0 failed**

---

## Bugs Found and Fixed

### 1. `WebUI/model_registry_db.py` — symlink-loop infinite recursion

**Symptom:** `POST /api/models/sync` and any `complete_job` post-run model scan would hang forever under Python 3.10 due to `pathlib.rglob()` following symlinks into an infinite recursive directory loop (`_iterate_directories` repeating endlessly).

**Root Cause:** Python 3.10's `pathlib.Path.rglob()` follows symlinks by default; the workspace has circular symlinks that caused unbounded recursion.

**Fix:** Replaced `directory.rglob("*")` with `os.walk(directory, followlinks=False)` and in-place pruning of known skip-directories (`dirs[:]` assignment). Added `import os` at the top of the module.

**File:** [`WebUI/model_registry_db.py`](../WebUI/model_registry_db.py)

---

### 2. `Scripts/webui_button_stress_validation.py` — wrong HTTP method for settings-save

**Symptom:** The validator sent `POST /api/settings` which returned 405 Method Not Allowed, causing the settings-save round-trip test to immediately fail.

**Root Cause:** The Flask route is registered as `@app.put("/api/settings")`, not `@app.post(...)`. The test script used `.post()` instead of `.put()`.

**Fix:** Changed `client.post("/api/settings", ...)` → `client.put("/api/settings", ...)` in the validator.

**File:** [`Scripts/webui_button_stress_validation.py`](../Scripts/webui_button_stress_validation.py)

---

### 3. `SecIDS-CNN/datasets/` — three CSV files not following `MD_` naming convention

**Symptom:** `Tools/final_test_suite.py` test 4 (CSV Naming Convention) failed because three files existed outside the `MD_*.csv` required prefix.

**Files renamed:**
- `combined_refined_dataset_20260310.csv` → `MD_combined_refined_dataset_20260310.csv`
- `Test_Deep_Scan.csv` → `MD_Test_Deep_Scan.csv`
- `Test_Deep_Scan_refined.csv` → `MD_Test_Deep_Scan_refined.csv`

---

## WebUI Button Coverage

### Toolbar Buttons (template `index.html` — all IDs verified wired in `app.js`)

| Button ID | Action | Verified |
|---|---|---|
| `zoom-out` | Decrease topology zoom | ✅ |
| `zoom-in` | Increase topology zoom | ✅ |
| `zoom-auto` | Auto-fit topology | ✅ |
| `guest-url-toggle` | Toggle guest tunnel URL | ✅ |
| `auth-logout` | Logout current session | ✅ |
| `scheduler-start` | Start job scheduler | ✅ |
| `scheduler-stop` | Stop job scheduler | ✅ |
| `queue-pause` | Pause job queue | ✅ |
| `queue-resume` | Resume job queue | ✅ |
| `queue-clear` | Clear all queued jobs | ✅ |
| `save-token` | Save API bearer token | ✅ |
| `refresh-system` | Force system info refresh | ✅ |
| `mode-realtime` | Switch to realtime mode | ✅ |
| `mode-simulation` | Switch to simulation mode | ✅ |
| `launch-simulation` | Launch simulation job | ✅ |
| `job-cancel` | Cancel running job | ✅ |
| `job-retry` | Retry last job | ✅ |
| `settings-save` | Save settings form | ✅ |
| `save-sudo-password` | Store sudo password for session | ✅ |
| `models-refresh` | Reload models table | ✅ |
| `models-sync` | Sync models from directories | ✅ |
| `live-model-save` | Choose live detection model | ✅ |

### Device Strip Dynamic Buttons (rendered by `renderDeviceStrip`)

| Action | Handler | Verified |
|---|---|---|
| `choose-model` (`iface:lo` → Models button) | Opens model chooser panel | ✅ |
| `open-server-db` (Server button, admin only) | Navigates to `/server` DB path | ✅ |
| `reset-view` (active interface label) | Resets topology pan to origin | ✅ |
| `toggle-countermeasure-mode` | Cycles active ↔ passive countermeasure mode | ✅ |

---

## API Endpoint Coverage (all authenticated, all returned expected status)

| Endpoint | Method | Status | Function |
|---|---|---|---|
| `/api/auth/session` | GET | 200 | Session info |
| `/api/auth/login` | POST | 200/401 | Login / bad credentials |
| `/api/auth/logout` | POST | 200 | Logout |
| `/api/auth/users` | POST/PUT/DELETE | 200/403/409 | User management |
| `/api/menu` | GET | 200 (auth) / 401 (anon) | Menu actions |
| `/api/system` | GET | 200 | System status |
| `/api/roles` | GET | 200 | Role list |
| `/api/queue` | GET | 200 | Queue state |
| `/api/queue/pause` | POST | 200 | Pause |
| `/api/queue/resume` | POST | 200 | Resume |
| `/api/queue/clear` | POST | 200 | Clear |
| `/api/queue/max_concurrent` | POST | 200 | Concurrency config |
| `/api/scheduler/start` | POST | 200 | Start scheduler |
| `/api/scheduler/stop` | POST | 200 | Stop scheduler |
| `/api/settings` | GET | 200 | Read settings |
| `/api/settings` | PUT | 200 | Save settings |
| `/api/history` | GET | 200 | Command history |
| `/api/audit` | GET | 200 | Audit log |
| `/api/overview` | GET | 200 | Device/interface overview |
| `/api/models` | GET | 200 | Model list |
| `/api/models/db-status` | GET | 200 | Model DB status |
| `/api/models/sync` | POST | 200 | Sync from filesystem |
| `/api/models/register` | POST | 200 | Register model path |
| `/api/run` | POST | 200 | Run any menu action |
| `/api/simulation/run` | POST | 200 | Launch simulation |
| `/api/jobs` | GET | 200 | Job list |
| `/api/jobs/<id>/cancel` | POST | 200/404 | Cancel job |
| `/api/control-surface/realtime` | GET | 200 | Realtime surface telemetry |
| `/api/guest-url/status` | GET | 200 | Guest tunnel URL info |

---

## Menu Actions Tested (81 total, all in simulation mode via `/api/run`)

All 81 actions across every section were exercised through the Flask test client with `mode=simulation`. Every action returned `200` with a valid `job_id`. No action raised an unexpected exception.

---

## Stress Test Results

| Category | Tests | Passed |
|---|---|---|
| Integrity | 4 | 4 |
| Processing | 4 | 4 |
| Models | 4 | 4 |
| Pipeline | 3 | 3 |
| Error handling | 3 | 3 |
| Edge cases | 3 | 3 |
| Concurrency | 1 | 1 |
| Realtime endpoint stress (160 requests) | 160 | 160 |

---

## Related Report Files

- [`Reports/webui_button_stress_validation_20260310_191008.json`](webui_button_stress_validation_20260310_191008.json)
- [`Reports/webui_button_stress_validation_20260310_191008.md`](webui_button_stress_validation_20260310_191008.md)
- `Stress_Test_Results/stress_test_report_20260310_191416.json`
- `Stress_Test_Results/stress_test_report_20260310_191430.json`

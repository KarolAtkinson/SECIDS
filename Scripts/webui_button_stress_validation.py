#!/usr/bin/env python3
"""WebUI button wiring + endpoint stress validation.

This script combines:
- Backend functional checks for button-backed API endpoints.
- Menu action execution in simulation mode.
- Static verification that template button IDs and device actions are wired in app.js.
- Lightweight stress polling of realtime endpoints.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from WebUI.app import create_app  # noqa: E402


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def safe_json(resp) -> dict[str, Any]:
    try:
        payload = resp.get_json(silent=True)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def main() -> int:
    app = create_app()
    client = app.test_client()

    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    def expect_status(name: str, response, allowed: set[int]) -> dict[str, Any]:
        body = response.get_data(as_text=True)[:300]
        ok = response.status_code in allowed
        record(name, ok, f"status={response.status_code} body={body}")
        require(ok, f"{name}: expected {sorted(allowed)} got {response.status_code}")
        return safe_json(response)

    # Login
    login_resp = client.post("/api/auth/login", json={"username": "kali", "password": "uclb()w1V"})
    login_data = expect_status("login", login_resp, {200})
    require(bool(login_data.get("ok")), "login did not return ok=true")

    # Button-backed API endpoints (toolbar + key controls)
    endpoint_checks = [
        ("refresh-system", "GET", "/api/system", None, {200}),
        ("queue-pause", "POST", "/api/queue/pause", {}, {200}),
        ("queue-resume", "POST", "/api/queue/resume", {}, {200}),
        ("queue-clear", "POST", "/api/queue/clear", {}, {200}),
        ("scheduler-stop", "POST", "/api/scheduler/stop", {}, {200}),
        ("scheduler-start", "POST", "/api/scheduler/start", {}, {200}),
        ("queue-max-concurrent", "POST", "/api/queue/max_concurrent", {"value": 2}, {200}),
        ("overview", "GET", "/api/overview", None, {200}),
        ("control-surface-realtime", "GET", "/api/control-surface/realtime", None, {200}),
        ("models-list", "GET", "/api/models?limit=5", None, {200}),
        ("models-sync", "POST", "/api/models/sync", {"source": "button-stress"}, {200}),
        ("settings-get", "GET", "/api/settings", None, {200}),
        ("guest-url-status", "GET", "/api/guest-url/status", None, {200}),
    ]

    for name, method, path, payload, allowed in endpoint_checks:
        if method == "GET":
            response = client.get(path)
        else:
            response = client.post(path, json=payload)
        expect_status(name, response, allowed)

    # Save current settings payload back through API to verify settings-save path.
    # The endpoint is PUT /api/settings (not POST).
    current_settings_resp = client.get("/api/settings")
    current_settings = expect_status("settings-get-for-save", current_settings_resp, {200})
    save_payload = current_settings.get("settings") or {}
    settings_save_resp = client.put("/api/settings", json=save_payload)
    expect_status("settings-save", settings_save_resp, {200})

    # Validate /api/run for all menu actions in simulation mode.
    menu = expect_status("menu", client.get("/api/menu"), {200}).get("menu", [])
    action_count = 0
    for section in menu:
        for action in section.get("actions", []):
            action_id = action.get("id")
            params = {param.get("name"): str(param.get("default", "")) for param in action.get("params", [])}
            if action_id == "history-rerun-last":
                params["command"] = "echo button-validation"
            run_resp = client.post(
                "/api/run",
                json={
                    "action_id": action_id,
                    "params": params,
                    "mode": "simulation",
                    "timeout_seconds": 30,
                },
            )
            data = expect_status(f"run:{action_id}", run_resp, {200})
            require("job_id" in data, f"run:{action_id} missing job_id")
            action_count += 1

    record("menu-actions-count", True, f"tested={action_count}")

    # Stress poll key endpoints.
    stress_targets = ["/api/system", "/api/overview", "/api/control-surface/realtime", "/api/queue"]
    stress_start = time.time()
    stress_total = 0
    for _ in range(40):
        for path in stress_targets:
            resp = client.get(path)
            require(resp.status_code == 200, f"stress poll failed path={path} status={resp.status_code}")
            stress_total += 1
    stress_ms = int((time.time() - stress_start) * 1000)
    record("stress-poll", True, f"requests={stress_total} duration_ms={stress_ms}")

    # Static check: template button ids are referenced in app.js.
    template_text = (PROJECT_ROOT / "WebUI" / "templates" / "index.html").read_text(encoding="utf-8")
    app_js_text = (PROJECT_ROOT / "WebUI" / "static" / "app.js").read_text(encoding="utf-8")

    button_ids = set(re.findall(r"<button[^>]*id=\"([^\"]+)\"", template_text))
    ignored_ids = {"zoom-label"}  # non-button span id
    missing_id_refs = []
    for button_id in sorted(button_ids):
        if button_id in ignored_ids:
            continue
        if f'getElementById("{button_id}")' not in app_js_text and f"#{button_id}" not in app_js_text:
            missing_id_refs.append(button_id)

    require(not missing_id_refs, f"button IDs not referenced in app.js: {missing_id_refs}")
    record("button-id-wiring", True, f"ids_checked={len(button_ids)}")

    # Static check: data-device-action handlers exist for actions rendered in strip.
    rendered_actions = sorted(set(re.findall(r"data-device-action=\\\"([^\\\"]+)\\\"", app_js_text)))
    unhandled_actions = []
    for action in rendered_actions:
        handler_probe = f"[data-device-action='{action}']"
        if handler_probe not in app_js_text:
            unhandled_actions.append(action)

    require(not unhandled_actions, f"device actions without handlers: {unhandled_actions}")
    record("device-action-wiring", True, f"actions_checked={len(rendered_actions)}")

    # Logout path
    expect_status("logout", client.post("/api/auth/logout"), {200})
    expect_status("menu-after-logout", client.get("/api/menu"), {401})

    passed = sum(1 for item in checks if item["ok"])
    failed = len(checks) - passed

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "passed": passed,
        "failed": failed,
        "checks": checks,
        "actions_tested": action_count,
        "stress_requests": stress_total,
    }

    reports_dir = PROJECT_ROOT / "Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    json_path = reports_dir / f"webui_button_stress_validation_{ts}.json"
    md_path = reports_dir / f"webui_button_stress_validation_{ts}.md"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# WebUI Button and Stress Validation",
        "",
        f"- Timestamp: {report['timestamp']}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Menu actions tested (simulation): {action_count}",
        f"- Stress requests: {stress_total}",
        "",
        "## Failed Checks",
        "",
    ]
    failed_rows = [item for item in checks if not item["ok"]]
    if failed_rows:
        for item in failed_rows:
            lines.append(f"- {item['name']}: {item['detail']}")
    else:
        lines.append("- None")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[webui-button-stress] PASS={passed} FAIL={failed} actions={action_count} stress={stress_total}")
    print(f"[webui-button-stress] JSON report: {json_path}")
    print(f"[webui-button-stress] Markdown report: {md_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

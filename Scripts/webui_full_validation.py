#!/usr/bin/env python3
"""Comprehensive WebUI functional validation for SecIDS-CNN.

This script runs against Flask test_client (no external server needed) and
validates auth, API surfaces, queue/job flows, model registry endpoints, and
all menu actions in safe simulation mode.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from WebUI.app import create_app


def fail(message: str) -> None:
    raise AssertionError(message)


def expect_status(resp, allowed: set[int], label: str) -> None:
    if resp.status_code not in allowed:
        fail(f"{label}: expected {sorted(allowed)} got {resp.status_code} body={resp.get_data(as_text=True)[:300]}")


def main() -> int:
    app = create_app()
    client = app.test_client()

    checks_passed = 0

    # Unauthenticated behavior
    expect_status(client.get("/login"), {200, 302}, "GET /login")
    checks_passed += 1
    expect_status(client.get("/api/auth/session"), {200}, "GET /api/auth/session (anon)")
    checks_passed += 1
    expect_status(client.get("/api/menu"), {401}, "GET /api/menu (anon)")
    checks_passed += 1

    # Login
    bad = client.post("/api/auth/login", json={"username": "kali", "password": "wrong"})
    expect_status(bad, {401, 429}, "POST /api/auth/login bad")
    checks_passed += 1

    login = client.post("/api/auth/login", json={"username": "kali", "password": "uclb()w1V"})
    expect_status(login, {200}, "POST /api/auth/login good")
    if not login.get_json().get("ok"):
        fail("Login response missing ok=true")
    checks_passed += 1

    # Core API surfaces
    for path in [
        "/api/auth/session",
        "/api/menu",
        "/api/system",
        "/api/roles",
        "/api/queue",
        "/api/settings",
        "/api/history?limit=10",
        "/api/audit?limit=10",
        "/api/overview",
        "/api/models/db-status",
        "/api/models?limit=5",
    ]:
        resp = client.get(path)
        expect_status(resp, {200}, f"GET {path}")
        checks_passed += 1

    # User mutation checks (supports both single-admin and multi-user modes)
    probe_username = "validator_u1"
    user_create = client.post(
        "/api/auth/users",
        json={"username": probe_username, "role": "viewer", "password": "validator123"},
    )
    expect_status(user_create, {200, 403, 409}, "POST /api/auth/users")
    checks_passed += 1

    if user_create.status_code == 200:
        expect_status(client.put(f"/api/auth/users/{probe_username}/role", json={"role": "operator"}), {200}, "PUT /api/auth/users/<name>/role")
        checks_passed += 1
        expect_status(client.post(f"/api/auth/users/{probe_username}/reset-password", json={}), {200}, "POST /api/auth/users/<name>/reset-password")
        checks_passed += 1
        expect_status(client.delete(f"/api/auth/users/{probe_username}"), {200}, "DELETE /api/auth/users/<name>")
        checks_passed += 1
    else:
        expect_status(client.post("/api/auth/users/kali/reset-password", json={}), {403}, "POST /api/auth/users/<name>/reset-password (single-admin)")
        checks_passed += 1

    # Queue controls and scheduler controls
    expect_status(client.post("/api/queue/pause"), {200}, "POST /api/queue/pause")
    checks_passed += 1
    expect_status(client.post("/api/queue/resume"), {200}, "POST /api/queue/resume")
    checks_passed += 1
    expect_status(client.post("/api/queue/max_concurrent", json={"value": 2}), {200}, "POST /api/queue/max_concurrent")
    checks_passed += 1
    expect_status(client.post("/api/queue/clear"), {200}, "POST /api/queue/clear")
    checks_passed += 1
    expect_status(client.post("/api/scheduler/stop"), {200}, "POST /api/scheduler/stop")
    checks_passed += 1

    # Model registry workflows
    sync_resp = client.post("/api/models/sync", json={"source": "validation"})
    expect_status(sync_resp, {200}, "POST /api/models/sync")
    checks_passed += 1
    models_resp = client.get("/api/models?limit=3")
    models = models_resp.get_json().get("models", [])
    if models:
        first_path = models[0].get("path", "")
        reg = client.post("/api/models/register", json={"path": first_path, "source": "validation-register"})
        expect_status(reg, {200}, "POST /api/models/register")
        checks_passed += 1

    # Menu actions: run each in simulation mode so command payloads are validated without execution.
    menu = client.get("/api/menu").get_json().get("menu", [])
    action_count = 0
    for section in menu:
        for action in section.get("actions", []):
            action_id = action.get("id")
            params = {param.get("name"): str(param.get("default", "")) for param in action.get("params", [])}

            # Ensure history rerun internal action can succeed in automation.
            if action_id == "history-rerun-last":
                params["command"] = "echo validation-history"

            run_resp = client.post(
                "/api/run",
                json={
                    "action_id": action_id,
                    "params": params,
                    "mode": "simulation",
                    "timeout_seconds": 30,
                },
            )
            expect_status(run_resp, {200}, f"POST /api/run ({action_id})")
            payload = run_resp.get_json()
            if "job_id" not in payload:
                fail(f"POST /api/run ({action_id}) missing job_id")
            action_count += 1

    checks_passed += action_count

    # Exercise simulation endpoint itself (realtime queue path), then cancel safely.
    sim_resp = client.post(
        "/api/simulation/run",
        json={
            "attacker_profile": "mixed",
            "defender_profile": "adaptive-ai",
            "countermeasure_mode": "active",
            "intensity": "low",
            "attackers": 1,
            "duration": 10,
            "retrain": False,
            "seed": 101,
            "timeout_seconds": 30,
        },
    )
    expect_status(sim_resp, {200}, "POST /api/simulation/run")
    sim_job_id = sim_resp.get_json().get("job_id")
    if sim_job_id:
        time.sleep(0.4)
        cancel_resp = client.post(f"/api/jobs/{sim_job_id}/cancel")
        expect_status(cancel_resp, {200, 404}, "POST /api/jobs/<id>/cancel simulation")
        checks_passed += 1

    # Job list + logout
    expect_status(client.get("/api/jobs"), {200}, "GET /api/jobs")
    checks_passed += 1
    expect_status(client.post("/api/auth/logout"), {200}, "POST /api/auth/logout")
    checks_passed += 1
    expect_status(client.get("/api/menu"), {401}, "GET /api/menu after logout")
    checks_passed += 1

    print(f"[webui-validation] PASS ({checks_passed} checks)")
    print(f"[webui-validation] Actions tested: {action_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Non-interactive Git auto-sync + privacy guard setup for SECIDS-CNN."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TASK_CONFIG = PROJECT_ROOT / "Auto_Update" / "schedulers" / "task_config.json"
SYNC_SCRIPT = PROJECT_ROOT / "Auto_Update" / "git_auto_sync.py"
VENV_PYTHON = PROJECT_ROOT / ".venv_test" / "bin" / "python"


def ensure_task_config(interval_hours: int) -> dict:
    TASK_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    payload = {"tasks": {}, "thresholds": {}}
    if TASK_CONFIG.exists():
        try:
            payload = json.loads(TASK_CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"tasks": {}, "thresholds": {}}

    payload.setdefault("tasks", {})
    git_task = payload["tasks"].get("git_sync", {})
    git_task.update(
        {
            "enabled": True,
            "interval_hours": int(interval_hours),
            "script": "Auto_Update/git_auto_sync.py",
            "description": "Sync repository with GitHub (private-guarded pull and push changes)",
        }
    )
    payload["tasks"]["git_sync"] = git_task
    TASK_CONFIG.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return git_task


def upsert_cron(interval_hours: int) -> tuple[bool, str]:
    schedule_map = {
        1: "0 * * * *",
        6: "0 */6 * * *",
        12: "0 */12 * * *",
        24: "0 2 * * *",
    }
    schedule = schedule_map.get(interval_hours, "0 */6 * * *")
    python_exec = VENV_PYTHON if VENV_PYTHON.exists() else Path("python3")
    cron_cmd = (
        f"cd {PROJECT_ROOT} && SECIDS_REQUIRE_PRIVATE_REPO=1 {python_exec} {SYNC_SCRIPT} "
        f">> Auto_Update/logs/git_sync_cron.log 2>&1"
    )
    cron_line = f"{schedule} {cron_cmd}"

    try:
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
        existing_lines = [] if current.returncode != 0 else [line for line in current.stdout.splitlines() if line.strip()]
        filtered = [line for line in existing_lines if "Auto_Update/git_auto_sync.py" not in line]
        filtered.append(cron_line)
        subprocess.run(["crontab", "-"], input="\n".join(filtered) + "\n", text=True, capture_output=True, check=True)
        return True, "cron configured"
    except Exception as exc:
        return False, str(exc)


def check_privacy() -> tuple[bool, str]:
    python_exec = VENV_PYTHON if VENV_PYTHON.exists() else Path("python3")
    result = subprocess.run(
        [str(python_exec), str(SYNC_SCRIPT), "--check-privacy"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    ok = result.returncode == 0
    message = (result.stdout or result.stderr or "").strip()
    return ok, message


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure Git auto-sync and privacy policy")
    parser.add_argument("--interval-hours", type=int, default=6, help="Sync interval in hours (1, 6, 12, 24)")
    parser.add_argument("--no-cron", action="store_true", help="Do not configure crontab")
    args = parser.parse_args()

    task = ensure_task_config(args.interval_hours)
    print(json.dumps({"task_config": task}, indent=2))

    if not args.no_cron:
        cron_ok, cron_msg = upsert_cron(args.interval_hours)
        print(json.dumps({"cron_ok": cron_ok, "cron_message": cron_msg}, indent=2))

    privacy_ok, privacy_msg = check_privacy()
    print(json.dumps({"privacy_ok": privacy_ok, "privacy": privacy_msg}, indent=2))

    return 0 if privacy_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

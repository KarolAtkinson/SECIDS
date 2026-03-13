#!/usr/bin/env python3
"""
Auto-updating workflow chart generator.

Creates/refreshes Reports/WORKFLOW_CHART.md and aligns its file permissions
with Master-Manual.md so both artifacts keep the same access model.
"""

from __future__ import annotations

import hashlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


def sha256_short(file_path: Path) -> str:
    if not file_path.exists() or not file_path.is_file():
        return "missing"
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def file_state(file_path: Path) -> str:
    return "✅ Present" if file_path.exists() else "❌ Missing"


def sync_permissions(source: Path, target: Path) -> None:
    if not source.exists() or not target.exists():
        return

    src_stat = source.stat()
    os.chmod(target, stat.S_IMODE(src_stat.st_mode))

    try:
        os.chown(target, src_stat.st_uid, src_stat.st_gid)
    except PermissionError:
        # Non-root runs may not be allowed to change owner/group.
        pass


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    manual_path = project_root / "Master-Manual.md"
    chart_path = project_root / "Reports" / "WORKFLOW_CHART.md"
    chart_path.parent.mkdir(parents=True, exist_ok=True)

    tracked = [
        project_root / "Root" / "integrated_workflow.py",
        project_root / "Tools" / "simulate_ddos_workflow.py",
        project_root / "WebUI" / "app.py",
        project_root / "WebUI" / "menu_actions.py",
        project_root / "WebUI" / "templates" / "index.html",
        project_root / "WebUI" / "static" / "app.js",
        project_root / "WebUI" / "static" / "style.css",
        project_root / "SecIDS-CNN" / "train_and_test.py",
        project_root / "Auto_Update" / "task_scheduler.py",
        project_root / "Auto_Update" / "schedulers" / "task_config.json",
    ]

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    rows = []
    for tracked_file in tracked:
        rel = tracked_file.relative_to(project_root)
        rows.append(
            f"| `{rel}` | {file_state(tracked_file)} | `{sha256_short(tracked_file)}` |"
        )

    chart = f"""# SecIDS-CNN Workflow Chart (Auto-Updated)

**Generated:** {now_utc}
**Source:** `Auto_Update/monitors/update_workflow_chart.py`
**Privilege Baseline:** `Master-Manual.md`

## Operational Flow

```mermaid
flowchart LR
    A["A. Gathering Intelligence"] --> B["B. Detecting Threat"]
    B --> C["C. Countermeasures"]
    C --> D["D. Improvement"]
    D --> A

    C --> F["Policy/Response Feedback"]
    F --> D

    U["WebUI + Terminal UI"] --> B
    U --> C
    U --> D

    M["WebUI Simulation Mode"] --> X["Safe DDoS Simulation Subroutine"]
    X --> D

    S["Auto-Update Scheduler"] --> W["Workflow Chart Refresh"]
    S --> D
```

## Stage Ownership

- **A. Gathering Intelligence:** Live packet capture and data ingestion
- **B. Detecting Threat:** Flow feature extraction + model inference
- **C. Countermeasures:** Policy decision + active/passive response
- **D. Improvement:** Feedback persistence + retraining + model refresh

## Integrity Snapshot

| Tracked File | Status | Fingerprint |
|---|---|---|
{os.linesep.join(rows)}

## Notes

- This chart is automatically updated by Auto-Update task `workflow_chart_update`.
- It is intended to stay aligned with the live workflow implementation and scheduler config.
"""

    with open(chart_path, "w", encoding="utf-8") as handle:
        handle.write(chart)

    sync_permissions(manual_path, chart_path)

    print(f"Updated: {chart_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

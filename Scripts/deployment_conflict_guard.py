#!/usr/bin/env python3
"""Detect and quarantine deployment-conflict legacy files, then update stale launcher references.

This script is designed to work with the existing TrashDump workflow by moving
legacy/conflicting files into TrashDump with a timestamped name and preserving
relative paths for traceability.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRASH_DUMP_DIR = PROJECT_ROOT / "TrashDump"
CONFLICT_TRASH_DIR = TRASH_DUMP_DIR / "deployment_conflicts"
REPORTS_DIR = PROJECT_ROOT / "Reports"

SCAN_ROOTS = [
    PROJECT_ROOT / "Launchers",
    PROJECT_ROOT / "WebUI",
    PROJECT_ROOT / "Scripts",
    PROJECT_ROOT / "UI",
    PROJECT_ROOT / "Root",
]

TEXT_SUFFIXES = {".sh", ".py", ".md", ".txt", ".service", ".conf"}
EXCLUDE_PARTS = {".git", ".venv", ".venv_test", "__pycache__", "TrashDump", "Backups"}

# Rules used to identify old file variants that can interfere with active code paths.
LEGACY_NAME_RULES = [
    re.compile(r".+(?:_old|_backup|_deprecated|_legacy|_v\d+|_copy)\.[A-Za-z0-9]+$", re.IGNORECASE),
    re.compile(r".+\.(?:bak|tmp|temp|orig)$", re.IGNORECASE),
]

# Canonical path updates for deployment launch flow.
REFERENCE_REPLACEMENTS = {
    "WebUI/live_server.py": "WebUI/production_server.py",
    "secids_webui_live.log": "secids_webui_public.log",
}


@dataclass
class MoveRecord:
    source: str
    destination: str
    reason: str


@dataclass
class PatchRecord:
    path: str
    replacements: int


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in path.parts)


def is_legacy_candidate(path: Path) -> bool:
    name = path.name
    return any(rule.match(name) for rule in LEGACY_NAME_RULES)


def looks_replaceable_legacy(path: Path) -> bool:
    """Only quarantine legacy file if a likely canonical sibling exists."""
    stem = path.stem
    suffix = path.suffix

    for token in ("_old", "_backup", "_deprecated", "_legacy", "_copy"):
        if token in stem.lower():
            normalized = re.sub(token + r"$", "", stem, flags=re.IGNORECASE)
            sibling = path.with_name(normalized + suffix)
            if sibling.exists():
                return True

    v_match = re.match(r"(.+)_v\d+$", stem, flags=re.IGNORECASE)
    if v_match:
        sibling = path.with_name(v_match.group(1) + suffix)
        if sibling.exists():
            return True

    base = path.with_suffix("")
    for canonical_name in ("app", "production_server", "index", "style"):
        if canonical_name in base.name.lower():
            return True

    return False


def move_to_trashdump(path: Path, reason: str, apply_changes: bool) -> MoveRecord | None:
    rel = path.relative_to(PROJECT_ROOT)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    destination_dir = CONFLICT_TRASH_DIR / rel.parent
    destination_name = f"{path.stem}_{timestamp}{path.suffix}"
    destination = destination_dir / destination_name

    if apply_changes:
        destination_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))

    return MoveRecord(source=str(rel), destination=str(destination.relative_to(PROJECT_ROOT)), reason=reason)


def patch_stale_references(apply_changes: bool) -> List[PatchRecord]:
    patched: List[PatchRecord] = []
    self_path = Path(__file__).resolve()

    for root in SCAN_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file() or should_skip(path) or path.suffix.lower() not in TEXT_SUFFIXES:
                continue

            if path.resolve() == self_path:
                continue

            if path.name == "live_server.py":
                continue

            try:
                original = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            updated = original
            replacements = 0
            for old, new in REFERENCE_REPLACEMENTS.items():
                if old in updated:
                    updated = updated.replace(old, new)
                    replacements += original.count(old)

            if updated == original:
                continue

            if apply_changes:
                path.write_text(updated, encoding="utf-8")

            patched.append(PatchRecord(path=str(path.relative_to(PROJECT_ROOT)), replacements=replacements))

    return patched


def find_and_quarantine_legacy_files(apply_changes: bool) -> List[MoveRecord]:
    moved: List[MoveRecord] = []

    for root in SCAN_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file() or should_skip(path):
                continue

            if not is_legacy_candidate(path):
                continue

            if not looks_replaceable_legacy(path):
                continue

            record = move_to_trashdump(path, "legacy deployment variant", apply_changes)
            if record:
                moved.append(record)

    return moved


def write_report(moved: List[MoveRecord], patched: List[PatchRecord], apply_changes: bool) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"DEPLOYMENT_CONFLICT_GUARD_{ts}.md"

    mode = "APPLY" if apply_changes else "DRY-RUN"
    lines = [
        "# Deployment Conflict Guard Report",
        f"- Timestamp (UTC): {datetime.utcnow().isoformat()}",
        f"- Mode: {mode}",
        f"- Legacy files quarantined: {len(moved)}",
        f"- Stale references patched: {len(patched)}",
        "",
        "## Quarantined Files",
    ]

    if moved:
        lines.extend([f"- `{item.source}` -> `{item.destination}` ({item.reason})" for item in moved])
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Patched References")
    if patched:
        lines.extend([f"- `{item.path}` ({item.replacements} replacements)" for item in patched])
    else:
        lines.append("- None")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_path = CONFLICT_TRASH_DIR / f"manifest_{ts}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_payload = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "mode": mode,
        "moved": [item.__dict__ for item in moved],
        "patched": [item.__dict__ for item in patched],
        "report": str(report_path.relative_to(PROJECT_ROOT)),
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Quarantine deployment-conflict legacy variants to TrashDump and patch stale references.")
    parser.add_argument("--dry-run", action="store_true", help="Report findings without modifying files.")
    args = parser.parse_args()

    apply_changes = not args.dry_run

    moved = find_and_quarantine_legacy_files(apply_changes=apply_changes)
    patched = patch_stale_references(apply_changes=apply_changes)
    report = write_report(moved=moved, patched=patched, apply_changes=apply_changes)

    print("=" * 70)
    print("Deployment Conflict Guard")
    print("=" * 70)
    print(f"Mode: {'APPLY' if apply_changes else 'DRY-RUN'}")
    print(f"Legacy files quarantined: {len(moved)}")
    print(f"Stale references patched: {len(patched)}")
    print(f"Report: {report.relative_to(PROJECT_ROOT)}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

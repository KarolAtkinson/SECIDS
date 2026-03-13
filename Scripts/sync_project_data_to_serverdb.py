#!/usr/bin/env python3
"""Sync project data assets into tagged ServerDB folders without moving source code."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_DB_ROOT = PROJECT_ROOT / "ServerDB"

TAG_FOLDERS = {
    "NIST-CSW": SERVER_DB_ROOT / "NIST-CSW",
    "modelDB": SERVER_DB_ROOT / "modelDB",
    "datasetDB": SERVER_DB_ROOT / "datasetDB",
    "captureDB": SERVER_DB_ROOT / "captureDB",
    "resultDB": SERVER_DB_ROOT / "resultDB",
    "reportDB": SERVER_DB_ROOT / "reportDB",
    "webuiVersionsDB": SERVER_DB_ROOT / "webuiVersionsDB",
    "settingsDB": SERVER_DB_ROOT / "settingsDB",
    "userDB": SERVER_DB_ROOT / "userDB",
    "auditDB": SERVER_DB_ROOT / "auditDB",
    "actionDB": SERVER_DB_ROOT / "actionDB",
    "packetDB": SERVER_DB_ROOT / "packetDB",
    "historyDB": SERVER_DB_ROOT / "historyDB",
    "profileDB": SERVER_DB_ROOT / "profileDB",
    "logDB": SERVER_DB_ROOT / "logDB",
    "miscDB": SERVER_DB_ROOT / "miscDB",
}

SCAN_ROOTS = [
    PROJECT_ROOT / "Archives",
    PROJECT_ROOT / "Captures",
    PROJECT_ROOT / "Backups",
    PROJECT_ROOT / "Results",
    PROJECT_ROOT / "Reports",
    PROJECT_ROOT / "Logs",
    PROJECT_ROOT / "Stress_Test_Results",
    PROJECT_ROOT / "Config",
    PROJECT_ROOT / "Models",
    PROJECT_ROOT / "Model_Tester",
    PROJECT_ROOT / "Device_Profile",
]

EXCLUDED_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".sh",
    ".md",
    ".db",
}


def classify_tag(relative_path: Path) -> str:
    parts = relative_path.parts
    top = parts[0] if parts else ""
    suffix = relative_path.suffix.lower()
    lower_text = str(relative_path).lower()

    if "nist" in lower_text or "csw" in lower_text or "simulation_ddos" in lower_text:
        return "NIST-CSW"

    model_ext = {".h5", ".keras", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".tflite"}
    if suffix in model_ext or top in {"Models"} or lower_text.startswith("model_tester/models/"):
        return "modelDB"
    if suffix in {".pcap", ".pcapng"} or top in {"Captures"}:
        return "captureDB"
    if suffix in {".csv", ".parquet"} or top in {"Archives"} or lower_text.startswith("model_tester/datasets/") or lower_text.startswith("model_tester/threat_detection_model_1/"):
        return "datasetDB"
    if top in {"Results", "Stress_Test_Results"}:
        return "resultDB"
    if top in {"WebUI", "Backups"}:
        return "webuiVersionsDB"
    if top in {"Reports"}:
        return "reportDB"
    if top in {"Logs"} or lower_text.startswith("model_tester/logs/"):
        return "logDB"
    if top in {"Config"}:
        if "users" in lower_text:
            return "userDB"
        return "settingsDB"
    if "audit" in lower_text:
        return "auditDB"
    if "packet" in lower_text:
        return "packetDB"
    if "action" in lower_text:
        return "actionDB"
    if "history" in lower_text:
        return "historyDB"
    if top in {"Device_Profile"}:
        return "profileDB"
    return "miscDB"


def ensure_folders() -> None:
    SERVER_DB_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in TAG_FOLDERS.values():
        folder.mkdir(parents=True, exist_ok=True)


def sync_data(execute: bool = True) -> dict:
    ensure_folders()
    summary = {
        "started_at": datetime.utcnow().isoformat(),
        "execute": execute,
        "scanned": 0,
        "synced": 0,
        "skipped": 0,
        "errors": 0,
        "by_tag": {},
        "error_samples": [],
    }

    for root in SCAN_ROOTS:
        if not root.exists() or not root.is_dir():
            continue

        for source_path in root.rglob("*"):
            if not source_path.is_file():
                continue

            relative = source_path.relative_to(PROJECT_ROOT)
            if relative.suffix.lower() in EXCLUDED_SUFFIXES:
                continue

            summary["scanned"] += 1
            tag = classify_tag(relative)
            tag_stats = summary["by_tag"].setdefault(tag, {"synced": 0, "skipped": 0})
            target_root = TAG_FOLDERS.get(tag, TAG_FOLDERS["miscDB"])
            target_path = target_root / relative
            target_path.parent.mkdir(parents=True, exist_ok=True)

            if target_path.exists():
                src_stat = source_path.stat()
                dst_stat = target_path.stat()
                if int(src_stat.st_mtime) == int(dst_stat.st_mtime) and src_stat.st_size == dst_stat.st_size:
                    summary["skipped"] += 1
                    tag_stats["skipped"] += 1
                    continue

            if not execute:
                summary["synced"] += 1
                tag_stats["synced"] += 1
                continue

            try:
                if target_path.exists():
                    target_path.unlink()
                try:
                    os.link(source_path, target_path)
                except OSError:
                    shutil.copy2(source_path, target_path)
                summary["synced"] += 1
                tag_stats["synced"] += 1
            except OSError as exc:
                summary["errors"] += 1
                if len(summary["error_samples"]) < 20:
                    summary["error_samples"].append({"file": str(relative), "error": str(exc)})

    summary["finished_at"] = datetime.utcnow().isoformat()
    summary["db_root"] = str(SERVER_DB_ROOT.relative_to(PROJECT_ROOT))

    reports_dir = PROJECT_ROOT / "Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"server_db_sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["report"] = str(report_path.relative_to(PROJECT_ROOT))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync project data into tagged ServerDB folders")
    parser.add_argument("--dry-run", action="store_true", help="Calculate sync without writing files")
    args = parser.parse_args()

    result = sync_data(execute=not args.dry_run)
    print(json.dumps(result, indent=2))
    return 0 if result.get("errors", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

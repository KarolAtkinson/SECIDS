#!/usr/bin/env python3
"""Convert NIST-CSW open-source feed records to SECIDS model-style dataset format."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NIST_CSW_ROOT = PROJECT_ROOT / "ServerDB" / "NIST-CSW"
SOURCE_FEEDS_DIR = NIST_CSW_ROOT / "source_feeds"
CONVERTED_DIR = NIST_CSW_ROOT / "converted"
DATASETS_DIR = PROJECT_ROOT / "SecIDS-CNN" / "datasets"


MODEL_COLUMNS = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Length of Fwd Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Average Packet Size",
    "Packet Length Std",
    "FIN Flag Count",
    "ACK Flag Count",
    "is_attack",
    "Label",
    "source_file",
    "ip_source",
    "pattern_name",
    "pattern_source",
    "countermeasure_stopped",
    "sim_probability",
    "sim_second",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_normalized_feed_files() -> List[Path]:
    if not SOURCE_FEEDS_DIR.exists():
        return []
    files = sorted(SOURCE_FEEDS_DIR.glob("*_normalized_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    latest_by_prefix: Dict[str, Path] = {}
    for path in files:
        name = path.name
        prefix = name.split("_normalized_")[0]
        if prefix not in latest_by_prefix:
            latest_by_prefix[prefix] = path
    return sorted(latest_by_prefix.values(), key=lambda p: p.name)


def load_items(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    return [item for item in items if isinstance(item, dict)]


def score_from_item(item: Dict[str, Any]) -> float:
    value = str(item.get("cvss", "")).strip()
    try:
        return max(0.1, min(float(value), 10.0))
    except ValueError:
        return 6.5


def map_row(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
    score = score_from_item(item)
    cve = str(item.get("cve", "NIST-CSW-UNKNOWN")).strip() or "NIST-CSW-UNKNOWN"
    source = str(item.get("source", "nist_csw")).strip() or "nist_csw"

    destination_port = 443 if "web" in str(item.get("notes", "")).lower() else random.choice([80, 443, 53, 8080, 8443])
    total_packets = int(20 + (score * 10) + random.randint(0, 30))
    total_bytes = int(total_packets * (500 + score * 50))
    flow_duration = int((0.5 + (10.0 - score) * 0.3) * 1_000_000)
    duration_s = max(flow_duration / 1_000_000, 0.1)

    return {
        "Destination Port": destination_port,
        "Flow Duration": flow_duration,
        "Total Fwd Packets": total_packets,
        "Total Length of Fwd Packets": total_bytes,
        "Flow Bytes/s": float(total_bytes / duration_s),
        "Flow Packets/s": float(total_packets / duration_s),
        "Average Packet Size": float(total_bytes / max(total_packets, 1)),
        "Packet Length Std": float(40 + score * 20 + random.uniform(0, 60)),
        "FIN Flag Count": int(0 if score > 7 else random.randint(0, 2)),
        "ACK Flag Count": int(3 + score + random.randint(0, 4)),
        "is_attack": 1,
        "Label": "ATTACK",
        "source_file": "nist_csw_converted",
        "ip_source": f"nist-csw-src-{(idx % 254) + 1}",
        "pattern_name": cve[:80],
        "pattern_source": source[:120],
        "countermeasure_stopped": int(score >= 7.5),
        "sim_probability": round(min(max(score / 10.0, 0.05), 0.99), 4),
        "sim_second": idx,
    }


def convert() -> Dict[str, Any]:
    CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    files = latest_normalized_feed_files()
    if not files:
        return {"ok": False, "error": "No normalized NIST-CSW source feeds found", "converted_rows": 0}

    rows: List[Dict[str, Any]] = []
    consumed: List[str] = []

    for path in files:
        items = load_items(path)
        consumed.append(str(path.relative_to(PROJECT_ROOT)))
        for item in items[:600]:
            rows.append(map_row(item, len(rows)))

    if not rows:
        return {"ok": False, "error": "No feed items available for conversion", "converted_rows": 0, "consumed": consumed}

    df = pd.DataFrame(rows)
    for col in MODEL_COLUMNS:
        if col not in df.columns:
            df[col] = 0
    df = df[MODEL_COLUMNS]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    converted_csv = CONVERTED_DIR / f"nist_csw_model_style_{ts}.csv"
    dataset_csv = DATASETS_DIR / f"MD_nist_csw_converted_{ts}.csv"
    report_json = CONVERTED_DIR / f"nist_csw_conversion_report_{ts}.json"

    df.to_csv(converted_csv, index=False)
    df.to_csv(dataset_csv, index=False)

    report = {
        "ok": True,
        "generated_at": now_iso(),
        "converted_rows": len(df),
        "converted_file": str(converted_csv.relative_to(PROJECT_ROOT)),
        "dataset_file": str(dataset_csv.relative_to(PROJECT_ROOT)),
        "report_file": str(report_json.relative_to(PROJECT_ROOT)),
        "consumed_sources": consumed,
        "pipeline_alignment": {
            "A_gather_intel": "NIST/CISA open-source feed ingestion",
            "B_detect_threat": "Model-style feature conversion",
            "C_countermeasure": "Synthetic labels/countermeasure signals included",
            "D_improvement": "Dataset emitted for retrain/testing pipelines",
        },
    }

    with open(report_json, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert NIST-CSW source feeds to SECIDS model-style dataset")
    _ = parser.parse_args()

    result = convert()
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

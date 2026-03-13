#!/usr/bin/env python3
"""Safe DDoS simulation workflow for WebUI simulation mode.

This script does NOT execute real attacks. It generates synthetic traffic/flow
signals based on known DDoS-like patterns from local pattern sources and runs a
closed-loop simulation:
  1) attacker behavior synthesis
  2) defender/countermeasure response simulation
  3) optional model retrain + model tester handoff
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHIVES_DIR = PROJECT_ROOT / "Archives"
BLACKLIST_PATTERNS = PROJECT_ROOT / "Device_Profile" / "Blacklist" / "attack_patterns" / "patterns.json"
DATASETS_DIR = PROJECT_ROOT / "SecIDS-CNN" / "datasets"
RESULTS_DIR = PROJECT_ROOT / "Results"

ARCHITECTURE_PROFILES = {
    "school": {
        "hardware": ["edge-router", "managed-switch", "file-server", "student-devices", "wireless-ap"],
        "software": ["dhcp-dns", "content-filter", "endpoint-av", "siem-lite", "secids-cnn"],
        "traffic_multiplier": 1.0,
        "burst_multiplier": 1.0,
    },
    "library": {
        "hardware": ["edge-router", "switch", "circulation-server", "public-terminals", "wireless-ap"],
        "software": ["session-manager", "dns-filter", "endpoint-av", "log-collector", "secids-cnn"],
        "traffic_multiplier": 0.85,
        "burst_multiplier": 0.8,
    },
    "restaurant": {
        "hardware": ["edge-router", "pos-gateway", "switch", "pos-tablets", "wireless-ap"],
        "software": ["pos-stack", "guest-portal", "payment-controls", "log-collector", "secids-cnn"],
        "traffic_multiplier": 0.9,
        "burst_multiplier": 1.15,
    },
}


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def load_csw_ddos_patterns() -> List[Dict]:
    """Load pattern candidates from local CSW-like sources.

    Priority:
    1. Files containing "CSW" in filename
    2. Blacklist attack pattern JSON
    3. Archives/Attack_Dataset.csv filtered for DDoS-like records
    """
    patterns: List[Dict] = []

    csw_candidates = list(PROJECT_ROOT.rglob("*CSW*"))
    for candidate in csw_candidates:
        if not candidate.is_file() or candidate.suffix.lower() not in {".csv", ".json"}:
            continue
        try:
            if candidate.suffix.lower() == ".json":
                with open(candidate, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, list):
                    for item in payload[:100]:
                        patterns.append({"name": str(item)[:80], "source": str(candidate.relative_to(PROJECT_ROOT))})
            else:
                df = pd.read_csv(candidate)
                for _, row in df.head(100).iterrows():
                    text = " ".join(str(value) for value in row.tolist())
                    if "ddos" in text.lower() or "denial of service" in text.lower():
                        patterns.append({"name": text[:120], "source": str(candidate.relative_to(PROJECT_ROOT))})
        except Exception:
            continue

    if BLACKLIST_PATTERNS.exists():
        try:
            with open(BLACKLIST_PATTERNS, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, list):
                for item in payload[-200:]:
                    dst_port = item.get("dst_port", 0)
                    patterns.append(
                        {
                            "name": f"blacklist-pattern-port-{dst_port}",
                            "source": "Device_Profile/Blacklist/attack_patterns/patterns.json",
                            "packets": item.get("packets", 50),
                            "bytes": item.get("bytes", 15000),
                        }
                    )
        except Exception:
            pass

    attack_dataset = ARCHIVES_DIR / "Attack_Dataset.csv"
    if attack_dataset.exists():
        try:
            df = pd.read_csv(attack_dataset)
            keywords = [
                "ddos",
                "denial of service",
                "syn flood",
                "udp flood",
                "volumetric",
                "protocol-based",
            ]
            text_cols = [col for col in df.columns if df[col].dtype == object]
            for _, row in df.head(400).iterrows():
                blob = " ".join(str(row[col]) for col in text_cols).lower()
                if any(word in blob for word in keywords):
                    title = str(row.iloc[1]) if len(row) > 1 else "ddos-pattern"
                    patterns.append({"name": title[:120], "source": "Archives/Attack_Dataset.csv"})
        except Exception:
            pass

    if not patterns:
        patterns = [
            {"name": "synthetic-syn-flood", "source": "fallback"},
            {"name": "synthetic-udp-flood", "source": "fallback"},
            {"name": "synthetic-volumetric-burst", "source": "fallback"},
        ]

    return patterns


def pick_profile_weights(attacker_profile: str) -> Dict[str, float]:
    profile_weights = {
        "botnet": {"syn": 0.35, "udp": 0.4, "vol": 0.25},
        "syn-flood": {"syn": 0.75, "udp": 0.15, "vol": 0.10},
        "udp-flood": {"syn": 0.10, "udp": 0.75, "vol": 0.15},
        "mixed": {"syn": 0.34, "udp": 0.33, "vol": 0.33},
    }
    return profile_weights.get(attacker_profile, profile_weights["mixed"])


def defender_strength(defender_profile: str, countermeasure_mode: str, intensity: str) -> float:
    defender = {
        "edge-firewall": 0.60,
        "adaptive-ai": 0.78,
        "baseline": 0.45,
    }.get(defender_profile, 0.60)

    mode_bonus = 0.14 if countermeasure_mode == "active" else 0.05
    intensity_penalty = {"low": 0.0, "medium": 0.05, "high": 0.12}.get(intensity, 0.05)
    return clamp(defender + mode_bonus - intensity_penalty, 0.2, 0.95)


def resolve_architecture_profile(architecture_type: str) -> Dict:
    return ARCHITECTURE_PROFILES.get(architecture_type, ARCHITECTURE_PROFILES["school"])


def synthesize_dataset(
    patterns: List[Dict],
    architecture_type: str,
    attacker_profile: str,
    defender_profile: str,
    countermeasure_mode: str,
    intensity: str,
    attackers: int,
    duration: int,
    seed: int,
) -> tuple[pd.DataFrame, Dict]:
    random.seed(seed)

    architecture = resolve_architecture_profile(architecture_type)
    base_rate = {"low": 18, "medium": 45, "high": 95}.get(intensity, 45)
    base_rate = int(base_rate * float(architecture.get("traffic_multiplier", 1.0)))
    weights = pick_profile_weights(attacker_profile)
    strength = defender_strength(defender_profile, countermeasure_mode, intensity)

    rows: List[Dict] = []
    blocked_events = 0
    allowed_events = 0

    for second in range(max(10, duration)):
        waves = max(1, int(random.gauss(attackers, max(1, attackers * 0.2))))

        for _ in range(waves):
            attack_choice = random.choices(
                population=["syn", "udp", "vol"],
                weights=[weights["syn"], weights["udp"], weights["vol"]],
                k=1,
            )[0]

            pattern = random.choice(patterns)
            burst = random.uniform(0.8, 1.3) * float(architecture.get("burst_multiplier", 1.0))
            pkt_count = int(base_rate * burst * random.uniform(0.6, 1.7))
            byte_count = int(pkt_count * random.uniform(500, 1450))
            flow_duration_us = int(random.uniform(0.2, 2.8) * 1_000_000)

            if attack_choice == "syn":
                fin, ack = random.randint(0, 2), random.randint(2, 9)
                dst_port = random.choice([80, 443, 8080, 8443])
            elif attack_choice == "udp":
                fin, ack = 0, random.randint(0, 3)
                dst_port = random.choice([53, 123, 1900, 161, 500])
            else:
                fin, ack = random.randint(0, 1), random.randint(1, 7)
                dst_port = random.choice([80, 443, 22, 3389])

            probability = clamp(random.uniform(0.55, 0.98), 0.0, 1.0)
            stopped = random.random() < strength
            if stopped:
                blocked_events += 1
            else:
                allowed_events += 1

            duration_s = max(flow_duration_us / 1_000_000, 0.05)
            rows.append(
                {
                    "Destination Port": int(dst_port),
                    "Flow Duration": int(flow_duration_us),
                    "Total Fwd Packets": int(pkt_count),
                    "Total Length of Fwd Packets": int(byte_count),
                    "Flow Bytes/s": float(byte_count / duration_s),
                    "Flow Packets/s": float(pkt_count / duration_s),
                    "Average Packet Size": float(byte_count / max(1, pkt_count)),
                    "Packet Length Std": float(random.uniform(40, 420)),
                    "FIN Flag Count": int(fin),
                    "ACK Flag Count": int(ack),
                    "is_attack": 1,
                    "Label": "ATTACK",
                    "source_file": "simulation_ddos",
                    "ip_source": f"sim-attacker-{random.randint(1, 10000)}",
                    "pattern_name": str(pattern.get("name", "unknown"))[:80],
                    "pattern_source": str(pattern.get("source", "unknown"))[:120],
                    "countermeasure_stopped": int(stopped),
                    "sim_probability": float(probability),
                    "sim_second": int(second),
                }
            )

    if not rows:
        raise RuntimeError("No simulation rows generated")

    df = pd.DataFrame(rows)
    summary = {
        "architecture_type": architecture_type,
        "architecture_hardware": architecture["hardware"],
        "architecture_software": architecture["software"],
        "attack_events": len(df),
        "blocked_events": blocked_events,
        "allowed_events": allowed_events,
        "stop_ratio": round((blocked_events / max(1, len(df))) * 100.0, 2),
        "simulation_quality_score": round(
            clamp(
                60.0
                + (min(100_000, len(df)) / 100_000.0) * 20.0
                + len(summary_sources := sorted({str(item.get("source", "unknown")) for item in patterns})) * 1.2,
                0.0,
                99.0,
            ),
            2,
        ),
        "quality_note": "Score blends synthetic data volume and source diversity for this architecture.",
        "pattern_sources": summary_sources,
    }
    return df, summary


def run_training_handoff(dataset_path: Path) -> Dict:
    env = os.environ.copy()
    env["SECIDS_DATASET_PATH"] = str(dataset_path)

    secids_train = PROJECT_ROOT / "SecIDS-CNN" / "train_and_test.py"
    unified_train = PROJECT_ROOT / "Model_Tester" / "Code" / "train_unified_model.py"

    results = {
        "secids_train": {"ok": False, "code": None},
        "unified_train": {"ok": False, "code": None},
    }

    if secids_train.exists():
        proc = subprocess.run(
            ["python3", str(secids_train)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=2400,
            env=env,
        )
        results["secids_train"] = {"ok": proc.returncode == 0, "code": proc.returncode, "stderr": proc.stderr[:400]}

    if unified_train.exists():
        proc = subprocess.run(
            ["python3", str(unified_train)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=2400,
        )
        results["unified_train"] = {"ok": proc.returncode == 0, "code": proc.returncode, "stderr": proc.stderr[:400]}

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe DDoS simulation workflow")
    parser.add_argument("--architecture-type", default="school", choices=["school", "library", "restaurant"])
    parser.add_argument("--attacker-profile", default="mixed", choices=["botnet", "syn-flood", "udp-flood", "mixed"])
    parser.add_argument("--defender-profile", default="adaptive-ai", choices=["edge-firewall", "adaptive-ai", "baseline"])
    parser.add_argument("--countermeasure-mode", default="active", choices=["passive", "active"])
    parser.add_argument("--intensity", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--attackers", type=int, default=25)
    parser.add_argument("--duration", type=int, default=90)
    parser.add_argument("--retrain", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("[simulation] Starting safe DDoS simulation (no real attack traffic generated)")
    patterns = load_csw_ddos_patterns()
    print(f"[simulation] Pattern candidates loaded: {len(patterns)}")

    df, summary = synthesize_dataset(
        patterns=patterns,
        architecture_type=args.architecture_type,
        attacker_profile=args.attacker_profile,
        defender_profile=args.defender_profile,
        countermeasure_mode=args.countermeasure_mode,
        intensity=args.intensity,
        attackers=max(1, args.attackers),
        duration=max(10, args.duration),
        seed=args.seed,
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_path = DATASETS_DIR / f"MD_simulation_ddos_{ts}.csv"
    report_path = RESULTS_DIR / f"simulation_ddos_report_{ts}.json"

    df.to_csv(dataset_path, index=False)
    print(f"[simulation] Synthetic dataset saved: {dataset_path}")
    print(
        "[simulation] Architecture: "
        f"{args.architecture_type} "
        f"(hardware={len(summary['architecture_hardware'])}, software={len(summary['architecture_software'])})"
    )
    print(
        f"[simulation] Countermeasures stop ratio: {summary['stop_ratio']}% "
        f"(blocked={summary['blocked_events']}, allowed={summary['allowed_events']})"
    )
    print(f"[simulation] Quality score: {summary['simulation_quality_score']}/99")

    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": "safe_simulation",
        "inputs": vars(args),
        "summary": summary,
        "dataset": str(dataset_path.relative_to(PROJECT_ROOT)),
        "training_handoff": None,
    }

    if args.retrain:
        print("[simulation] Launching model training handoff (SecIDS + Model Tester)...")
        handoff = run_training_handoff(dataset_path)
        report["training_handoff"] = handoff
        if handoff["secids_train"]["ok"] or handoff["unified_train"]["ok"]:
            print("[simulation] New model artifact(s) created and routed to model testing workflow")
        else:
            print("[simulation] Training handoff failed; see report for stderr snippets")
    else:
        print("[simulation] Retraining skipped (enable --retrain to create model artifacts)")

    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(f"[simulation] Report written: {report_path}")
    print("[simulation] Completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

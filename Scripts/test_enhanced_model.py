#!/usr/bin/env python3
"""
Lightweight model validation for Auto_Update scheduler.
Validates critical ML imports and confirms at least one model artifact exists.
"""

from pathlib import Path
import sys


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    models_dir = project_root / "Models"

    try:
        import tensorflow as tf  # noqa: F401
        import numpy as np  # noqa: F401
        import pandas as pd  # noqa: F401
    except Exception as exc:
        print(f"[FAIL] Critical ML import failed: {exc}")
        return 1

    if not models_dir.exists():
        print(f"[FAIL] Models directory missing: {models_dir}")
        return 1

    model_candidates = list(models_dir.glob("*.h5")) + list(models_dir.glob("*.pkl"))
    if not model_candidates:
        print("[FAIL] No model artifacts found in Models/")
        return 1

    largest = max(model_candidates, key=lambda p: p.stat().st_size)
    size_mb = largest.stat().st_size / (1024 * 1024)
    print(f"[PASS] Imports OK. Model artifacts detected: {len(model_candidates)}")
    print(f"[PASS] Largest artifact: {largest.name} ({size_mb:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

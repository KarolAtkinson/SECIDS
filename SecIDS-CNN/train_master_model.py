#!/usr/bin/env python3
"""Helper to run the Master ML_AI training pipeline from this project.

Usage:
  python3 train_master_model.py

This script locates `Master ML_AI/Code/train_unified_model.py` and runs it in a subprocess
so users can trigger the unified model training from the main workspace.
"""
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TRAIN_SCRIPT = ROOT / 'Master ML_AI' / 'Code' / 'train_unified_model.py'

if __name__ == '__main__':
    if not TRAIN_SCRIPT.exists():
        print('Training script not found:', TRAIN_SCRIPT)
        sys.exit(1)

    print('Starting Master ML_AI unified training pipeline...')
    cmd = [sys.executable, str(TRAIN_SCRIPT)]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print('Training completed successfully')
    else:
        print('Training failed with exit code', res.returncode)
        sys.exit(res.returncode)

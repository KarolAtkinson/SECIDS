#!/usr/bin/env python3
"""Canonical paths for Model_Tester scripts and artifacts."""

from __future__ import annotations

from pathlib import Path


CODE_DIR = Path(__file__).resolve().parent
MODEL_TESTER_ROOT = CODE_DIR.parent
TRAINING_DATA_DIR = MODEL_TESTER_ROOT / "Threat_Detection_Model_1"
DATASETS_DIR = MODEL_TESTER_ROOT / "datasets"
MODELS_DIR = MODEL_TESTER_ROOT / "models"
LOGS_DIR = MODEL_TESTER_ROOT / "logs"


def ensure_model_tester_dirs() -> None:
    TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
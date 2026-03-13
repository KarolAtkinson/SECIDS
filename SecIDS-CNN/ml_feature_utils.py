#!/usr/bin/env python3
"""Shared feature/target preprocessing helpers for SecIDS-CNN pipelines."""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

CORE_FEATURE_COLUMNS = [
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
]

TARGET_CANDIDATES = [
    "is_attack",
    "is_ddos",
    "Attack",
    "attack",
    "Label",
    "Class",
    "label",
    "class",
    "Type",
    "type",
    "threat",
    "Threat",
    "Intrusion",
]

META_DROP_COLUMNS = {
    "prediction",
    "probability",
    "source_file",
    "ip_source",
    "pattern_name",
    "pattern_source",
    "_src_ip",
    "_dst_ip",
}


def find_target_column(df: pd.DataFrame) -> Optional[str]:
    for col in TARGET_CANDIDATES:
        if col in df.columns:
            return col
    return None


def _coerce_objects_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    for col in clean.columns:
        if clean[col].dtype == object:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")
    return clean


def build_feature_frame(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    drop_targets: bool = True,
    prefer_core_columns: bool = True,
) -> pd.DataFrame:
    work = df.copy()

    drop_cols = set(META_DROP_COLUMNS)
    if drop_targets:
        drop_cols.update([c for c in TARGET_CANDIDATES if c in work.columns])
    elif target_col:
        drop_cols.add(target_col)

    work = work.drop(columns=[c for c in drop_cols if c in work.columns], errors="ignore")
    work = _coerce_objects_to_numeric(work)
    work = work.fillna(work.mean(numeric_only=True))

    numeric = work.select_dtypes(include=[np.number])
    if numeric.empty:
        return numeric

    if prefer_core_columns:
        present_core = [col for col in CORE_FEATURE_COLUMNS if col in numeric.columns]
        if len(present_core) >= 6:
            return numeric[present_core].copy()

    return numeric.copy()


def align_feature_dimension(features: pd.DataFrame, expected_dim: Optional[int]) -> pd.DataFrame:
    if expected_dim is None or expected_dim <= 0:
        return features

    aligned = features.copy()
    current_dim = aligned.shape[1]
    if current_dim == expected_dim:
        return aligned

    if current_dim > expected_dim:
        return aligned.iloc[:, :expected_dim].copy()

    # current_dim < expected_dim: pad with zeros
    missing = expected_dim - current_dim
    for idx in range(missing):
        aligned[f"pad_feature_{idx+1}"] = 0.0
    return aligned


def resolve_target_and_features(df: pd.DataFrame) -> Tuple[Optional[str], pd.DataFrame]:
    target_col = find_target_column(df)
    features = build_feature_frame(df, target_col=target_col, drop_targets=True, prefer_core_columns=True)
    return target_col, features

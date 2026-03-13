#!/usr/bin/env python3
import pickle
from pathlib import Path
import os
import numpy as np
import pandas as pd

class UnifiedModelWrapper:
    """Wrapper to load a trained UnifiedThreatModel's components (RF + GB + scaler)

    This wrapper expects the model files produced by `Model_Tester/Code/unified_threat_model.py`:
      - unified_threat_model_<timestamp>.pkl  (contains {'rf':..., 'gb':...})
      - unified_scaler_<timestamp>.pkl

    The wrapper finds the latest timestamped files in the provided `model_dir` and
    exposes `predict_proba(df)` and `predict(df)` methods which accept a pandas DataFrame
    containing the feature columns used by the UnifiedThreatModel.
    """

    def __init__(self, model_dir=None):
        project_root = Path(__file__).resolve().parents[1]
        default_master_models = project_root / 'Model_Tester' / 'Code' / 'models'
        self.model_dir = Path(model_dir) if model_dir else default_master_models
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

        self.rf = None
        self.gb = None
        self.scaler = None
        self.feature_names = None

        self._load_latest()

    def _find_latest(self, pattern):
        files = list(self.model_dir.glob(pattern))
        if not files:
            return None
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0]

    def _load_latest(self):
        # Look for latest model and scaler files
        model_file = self._find_latest('unified_threat_model_*.pkl')
        scaler_file = self._find_latest('unified_scaler_*.pkl')
        metadata_file = self._find_latest('unified_metadata_*.pkl')

        if model_file is None or scaler_file is None:
            raise FileNotFoundError('Could not find saved unified model or scaler in ' + str(self.model_dir))

        with open(model_file, 'rb') as f:
            loaded = pickle.load(f)
        # Expecting dict with keys 'rf' and 'gb'
        self.rf = loaded.get('rf') if isinstance(loaded, dict) else None
        self.gb = loaded.get('gb') if isinstance(loaded, dict) else None

        with open(scaler_file, 'rb') as f:
            self.scaler = pickle.load(f)

        # Optionally load metadata for feature_names
        if metadata_file is not None:
            try:
                with open(metadata_file, 'rb') as f:
                    meta = pickle.load(f)
                self.feature_names = meta.get('feature_names')
            except (FileNotFoundError, pickle.UnpicklingError) as e:
                print(f"Warning: Could not load metadata: {e}")
                self.feature_names = None

        if self.rf is None or self.gb is None:
            raise ValueError('Loaded model does not contain expected RF/GB components')

    def _prepare(self, df: pd.DataFrame):
        # If a feature set is known, select those columns; else use numeric columns
        if self.feature_names:
            missing = [c for c in self.feature_names if c not in df.columns]
            if missing:
                # Try to continue by using numeric columns
                X = df.select_dtypes(include=[np.number]).copy()
            else:
                X = df[self.feature_names].copy()
        else:
            X = df.select_dtypes(include=[np.number]).copy()

        # Fill and replace
        X = X.fillna(X.mean(numeric_only=True))
        X = X.replace([np.inf, -np.inf], 0)

        # Scale
        X_scaled = self.scaler.transform(X)  # type: ignore
        return X_scaled, X.columns.tolist()

    def predict_proba(self, df: pd.DataFrame):
        X_scaled, cols = self._prepare(df)
        rf_proba = self.rf.predict_proba(X_scaled)[:, 1]  # type: ignore
        gb_proba = self.gb.predict_proba(X_scaled)[:, 1]  # type: ignore
        ensemble_proba = (rf_proba + gb_proba) / 2.0
        return ensemble_proba

    def predict(self, df: pd.DataFrame):
        probs = self.predict_proba(df)
        return (probs >= 0.5).astype(int)


if __name__ == '__main__':
    print('This module provides UnifiedModelWrapper for loading Model_Tester saved models.')

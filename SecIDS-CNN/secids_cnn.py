#!/usr/bin/env python3
import os

# TensorFlow runtime/logging must be configured before importing tensorflow
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')

import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
import json

# Suppress warnings
warnings.filterwarnings('ignore')
tf.get_logger().setLevel('ERROR')

try:
    tf.config.set_visible_devices([], 'GPU')
except Exception:
    pass

# Patch for Keras 3.x compatibility with quantization_config
original_from_config = tf.keras.layers.Dense.from_config

@classmethod
def patched_from_config(cls, config):
    if 'quantization_config' in config:
        config.pop('quantization_config')
    return original_from_config(config)

tf.keras.layers.Dense.from_config = patched_from_config

class SecIDSModel:
    def __init__(self, model_path="SecIDS-CNN.h5"):
        # Load the trained model - check multiple possible locations
        from pathlib import Path

        raw_path = Path(model_path)
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent

        if raw_path.is_absolute():
            resolved_path = raw_path
        else:
            candidate_paths = [
                Path.cwd() / raw_path,
                script_dir / raw_path,
                project_root / raw_path,
                project_root / "Models" / raw_path.name,
                script_dir / raw_path.name,
                project_root / raw_path.name,
            ]

            resolved_path = None
            for candidate in candidate_paths:
                if candidate.exists() and candidate.is_file():
                    resolved_path = candidate
                    break

            if resolved_path is None:
                tried = "\n".join(f"- {candidate}" for candidate in candidate_paths)
                raise FileNotFoundError(
                    f"Model file not found for '{model_path}'. Tried:\n{tried}"
                )

        self.model = tf.keras.models.load_model(str(resolved_path), compile=False)
        self.label_encoders = {}

    def predict(self, data):
        # Preprocess data
        processed_data = self.preprocess_data(data)
        
        # Make predictions (direct call avoids repeated retracing from model.predict)
        predictions = self.model(processed_data, training=False).numpy()

        # Convert predictions to readable format
        if predictions.ndim == 2 and predictions.shape[1] == 1:
            # Binary classification (sigmoid output)
            probs = predictions.flatten()
            return ["Attack" if p > 0.5 else "Benign" for p in probs]
        elif predictions.ndim == 2 and predictions.shape[1] > 1:
            # Multi-class classification (softmax)
            class_labels = ["Benign", "Attack"]  # Adjust based on your classes
            return [class_labels[np.argmax(pred)] for pred in predictions]
        else:
            # Fallback
            return predictions

    def predict_proba(self, data):
        """Return raw probability scores for binary or multi-class outputs.

        Binary: returns 1D array of probabilities for the positive class.
        Multi-class: returns 2D array of softmax probabilities.
        """
        processed_data = self.preprocess_data(data)
        preds = self.model(processed_data, training=False).numpy()
        if preds.ndim == 2 and preds.shape[1] == 1:
            return preds.flatten()
        return preds

    def preprocess_data(self, data):
        # Make a copy to avoid modifying original
        df = data.copy()
        
        # Remove non-numeric columns or encode them
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except (ValueError, TypeError):
                    # If conversion fails, use label encoding
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))
        
        # Handle missing values
        df = df.fillna(df.mean())
        
        # Select only numeric columns
        numeric_data = df.select_dtypes(include=[np.number])
        
        # Normalize data (local scaler keeps inference thread-safe)
        scaler = StandardScaler()
        normalized_data = scaler.fit_transform(numeric_data)
        
        return normalized_data.astype(np.float32)

#!/usr/bin/env python3
import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import os
import warnings
import json

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')

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
        
        if not Path(model_path).is_absolute():
            # Try different locations
            possible_paths = [
                Path(model_path),  # Current directory
                Path(__file__).parent / model_path,  # Same directory as this script
                Path(__file__).parent.parent / 'Models' / model_path,  # Models folder
            ]
            
            for path in possible_paths:
                if path.exists():
                    model_path = str(path)
                    break
        
        self.model = tf.keras.models.load_model(model_path)
        self.scaler = StandardScaler()
        self.label_encoders = {}

    def predict(self, data):
        # Preprocess data
        processed_data = self.preprocess_data(data)
        
        # Make predictions
        predictions = self.model.predict(processed_data, verbose=0)

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
        preds = self.model.predict(processed_data, verbose=0)
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
                except Exception:
                    # If conversion fails, use label encoding
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))
        
        # Handle missing values
        df = df.fillna(df.mean())
        
        # Select only numeric columns
        numeric_data = df.select_dtypes(include=[np.number])
        
        # Normalize data
        normalized_data = self.scaler.fit_transform(numeric_data)
        
        return normalized_data.astype(np.float32)

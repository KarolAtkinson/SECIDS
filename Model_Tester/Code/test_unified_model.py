#!/usr/bin/env python3
"""
Quick Test: Unified Threat Detection Model
Demonstrates how to use the trained model for threat predictions
"""

import pandas as pd
import numpy as np
import os
import pickle
from pathlib import Path

def load_trained_model():
    """Load the most recently trained unified model"""
    model_dir = Path(__file__).parent / "models"
    
    # Find most recent unified model files
    unified_models = sorted(model_dir.glob("unified_threat_model_*.pkl"))
    unified_scalers = sorted(model_dir.glob("unified_scaler_*.pkl"))
    
    if not unified_models or not unified_scalers:
        print("⚠ No trained unified models found yet.")
        print("  Run train_unified_model.py first")
        return None, None
    
    latest_model_path = unified_models[-1]
    latest_scaler_path = unified_scalers[-1]
    
    print(f"✓ Loading model: {latest_model_path.name}")
    with open(latest_model_path, 'rb') as f:
        model = pickle.load(f)
    
    print(f"✓ Loading scaler: {latest_scaler_path.name}")
    with open(latest_scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    return model, scaler


def predict_threat(model, scaler, features_dict):
    """
    Predict if network flow is a threat
    
    Args:
        model: Trained ensemble model
        scaler: Feature scaler
        features_dict: Dictionary with feature values
        
    Returns:
        prediction (0=Normal, 1=DDoS), probability
    """
    if model is None or scaler is None:
        return None, None
    
    # Feature order (must match training)
    feature_names = [
        'Destination Port',
        'Flow Duration',
        'Total Fwd Packets',
        'Total Length of Fwd Packets',
        'Flow Bytes/s',
        'Flow Packets/s',
        'Average Packet Size',
        'Packet Length Std',
        'FIN Flag Count',
        'ACK Flag Count'
    ]
    
    # Create feature array
    X = np.array([[features_dict.get(f, 0) for f in feature_names]])
    
    # Scale
    X_scaled = scaler.transform(X)
    
    # Predict
    rf_proba = model['rf'].predict_proba(X_scaled)[:, 1][0]
    gb_proba = model['gb'].predict_proba(X_scaled)[:, 1][0]
    ensemble_proba = (rf_proba + gb_proba) / 2
    
    prediction = 1 if ensemble_proba >= 0.5 else 0
    
    return prediction, ensemble_proba


def main():
    """Main execution"""
    print("="*80)
    print("UNIFIED THREAT DETECTION MODEL - PREDICTION TEST")
    print("="*80)
    print()
    
    # Load model
    model, scaler = load_trained_model()
    
    if model is None:
        print("\nWaiting for model training to complete...")
        return
    
    # Example 1: Normal network traffic
    print("Test Case 1: Normal Network Traffic")
    print("-" * 60)
    normal_flow = {
        'Destination Port': 80,
        'Flow Duration': 1000,
        'Total Fwd Packets': 10,
        'Total Length of Fwd Packets': 1500,
        'Flow Bytes/s': 1500,
        'Flow Packets/s': 10,
        'Average Packet Size': 150,
        'Packet Length Std': 50,
        'FIN Flag Count': 0,
        'ACK Flag Count': 5
    }
    
    pred, prob = predict_threat(model, scaler, normal_flow)
    if pred is not None:
        threat_type = "🔴 DDoS DETECTED" if pred == 1 else "🟢 NORMAL TRAFFIC"
        print(f"Prediction: {threat_type}")
        print(f"Confidence: {prob:.2%}")
        print()
    
    # Example 2: Suspicious DDoS-like traffic
    print("Test Case 2: Suspicious High-Volume Traffic (Potential DDoS)")
    print("-" * 60)
    ddos_flow = {
        'Destination Port': 80,
        'Flow Duration': 100,
        'Total Fwd Packets': 10000,
        'Total Length of Fwd Packets': 50000,
        'Flow Bytes/s': 500000,
        'Flow Packets/s': 100000,
        'Average Packet Size': 50,
        'Packet Length Std': 5,
        'FIN Flag Count': 0,
        'ACK Flag Count': 0
    }
    
    pred, prob = predict_threat(model, scaler, ddos_flow)
    if pred is not None:
        threat_type = "🔴 DDoS DETECTED" if pred == 1 else "🟢 NORMAL TRAFFIC"
        print(f"Prediction: {threat_type}")
        print(f"Confidence: {prob:.2%}")
        print()
    
    # Example 3: Another normal flow on different port
    print("Test Case 3: HTTPS Traffic (Port 443)")
    print("-" * 60)
    https_flow = {
        'Destination Port': 443,
        'Flow Duration': 2000,
        'Total Fwd Packets': 25,
        'Total Length of Fwd Packets': 5000,
        'Flow Bytes/s': 2500,
        'Flow Packets/s': 12.5,
        'Average Packet Size': 200,
        'Packet Length Std': 100,
        'FIN Flag Count': 1,
        'ACK Flag Count': 10
    }
    
    pred, prob = predict_threat(model, scaler, https_flow)
    if pred is not None:
        threat_type = "🔴 DDoS DETECTED" if pred == 1 else "🟢 NORMAL TRAFFIC"
        print(f"Prediction: {threat_type}")
        print(f"Confidence: {prob:.2%}")
        print()
    
    print("="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

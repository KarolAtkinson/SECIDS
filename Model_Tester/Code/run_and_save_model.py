#!/usr/bin/env python3
"""
Run unified model and save predictions to Test1.csv
"""
import sys
import os
from pathlib import Path

# Add Code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from unified_threat_model import UnifiedThreatModel
import pandas as pd
import numpy as np
from path_config import MODELS_DIR, TRAINING_DATA_DIR, ensure_model_tester_dirs

ensure_model_tester_dirs()

# Setup paths
base_path = code_dir.parent
model_dir = MODELS_DIR
model_dir.mkdir(parents=True, exist_ok=True)

# Initialize and train model
unified_model = UnifiedThreatModel(model_dir=model_dir)

print("Training model...")
unified_model.train_model(test_size=0.2)

x_test = unified_model.X_test
y_test = unified_model.y_test
y_pred = unified_model.y_pred
model_outputs = unified_model.model

if x_test is None or y_test is None or y_pred is None or model_outputs is None:
    raise RuntimeError("Model training did not produce test features/labels/predictions")

if 'ensemble_proba' not in model_outputs:
    raise RuntimeError("Missing 'ensemble_proba' in model outputs")

ensemble_proba = model_outputs['ensemble_proba']

# Create test results dataframe
print("\nGenerating test predictions...")
test_results = pd.DataFrame({
    'Destination_Port': x_test['Destination Port'].values,
    'Flow_Duration': x_test['Flow Duration'].values,
    'Total_Fwd_Packets': x_test['Total Fwd Packets'].values,
    'Total_Length_Fwd_Packets': x_test['Total Length of Fwd Packets'].values,
    'Flow_Bytes_per_sec': x_test['Flow Bytes/s'].values,
    'Flow_Packets_per_sec': x_test['Flow Packets/s'].values,
    'Avg_Packet_Size': x_test['Average Packet Size'].values,
    'Packet_Length_Std': x_test['Packet Length Std'].values,
    'FIN_Flag_Count': x_test['FIN Flag Count'].values,
    'ACK_Flag_Count': x_test['ACK Flag Count'].values,
    'Actual_Label': y_test.values,
    'Predicted_Label': y_pred,
    'Prediction_Probability': ensemble_proba,
    'Prediction_Confidence': np.abs(ensemble_proba - 0.5) * 2,
    'Correct_Prediction': (y_test.values == y_pred).astype(int)
})

# Save to Threat_Detection_Model_1
output_path = TRAINING_DATA_DIR / "Test1.csv"
test_results.to_csv(output_path, index=False)

print(f"\n✓ Predictions saved to {output_path}")
print(f"  Total predictions: {len(test_results)}")
print(f"  Accuracy: {test_results['Correct_Prediction'].mean():.4f}")
print(f"\nFirst 10 rows:")
print(test_results.head(10))

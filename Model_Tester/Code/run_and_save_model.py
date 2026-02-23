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

# Setup paths
base_path = code_dir.parent
model_dir = code_dir / "models"
model_dir.mkdir(exist_ok=True)

# Initialize and train model
unified_model = UnifiedThreatModel(model_dir=model_dir)

print("Training model...")
unified_model.train_model(test_size=0.2)

# Create test results dataframe
print("\nGenerating test predictions...")
test_results = pd.DataFrame({
    'Destination_Port': unified_model.X_test['Destination Port'].values,
    'Flow_Duration': unified_model.X_test['Flow Duration'].values,
    'Total_Fwd_Packets': unified_model.X_test['Total Fwd Packets'].values,
    'Total_Length_Fwd_Packets': unified_model.X_test['Total Length of Fwd Packets'].values,
    'Flow_Bytes_per_sec': unified_model.X_test['Flow Bytes/s'].values,
    'Flow_Packets_per_sec': unified_model.X_test['Flow Packets/s'].values,
    'Avg_Packet_Size': unified_model.X_test['Average Packet Size'].values,
    'Packet_Length_Std': unified_model.X_test['Packet Length Std'].values,
    'FIN_Flag_Count': unified_model.X_test['FIN Flag Count'].values,
    'ACK_Flag_Count': unified_model.X_test['ACK Flag Count'].values,
    'Actual_Label': unified_model.y_test.values,
    'Predicted_Label': unified_model.y_pred,
    'Prediction_Probability': unified_model.model['ensemble_proba'],
    'Prediction_Confidence': np.abs(unified_model.model['ensemble_proba'] - 0.5) * 2,
    'Correct_Prediction': (unified_model.y_test.values == unified_model.y_pred).astype(int)
})

# Save to Threat_Detection_Model_1
output_path = base_path / "Threat_Detection_Model_1" / "Test1.csv"
test_results.to_csv(output_path, index=False)

print(f"\n✓ Predictions saved to {output_path}")
print(f"  Total predictions: {len(test_results)}")
print(f"  Accuracy: {test_results['Correct_Prediction'].mean():.4f}")
print(f"\nFirst 10 rows:")
print(test_results.head(10))

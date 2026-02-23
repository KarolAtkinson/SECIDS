# CYBERSECURITY THREAT DETECTION MODEL - OPERATIONAL CHECKLIST

## Overview
This document provides a step-by-step guide to operate the AI Cybersecurity Threat Detection Model for DDoS and Phishing attacks.

---

## PRE-EXECUTION CHECKLIST

### 1. Verify Directory Structure
  - [ ] Confirm `Threat_Detection_Model_1/` directory exists with CSV files:
  - [ ] `Attack_Dataset.csv` - Attack scenario descriptions and techniques
  - [ ] `cicids2017_cleaned.csv` - Network traffic data (DDoS detection)
  - [ ] `Global_Cybersecurity_Threats_2015-2024.csv` - Phishing and attack trends
  - [ ] `cybersecurity_attacks.csv` - Detailed attack logs
  - [ ] `cybersecurity_intrusion_data.csv` - Intrusion patterns
  - [ ] `cybersecurity_cases_india_combined.csv` - Regional incident data
  - [ ] `Cyber_security.csv` - Country-level cybersecurity indices

- [ ] Confirm `Code/` directory exists (where all scripts are located)

### 2. Install Required Python Packages
```powershell
cd "C:\Users\karol\OneDrive\Pulpit\Master ML_AI"

# Install dependencies
pip install pandas numpy scikit-learn matplotlib seaborn scipy

# Or use requirements.txt (if created)
pip install -r requirements.txt
```

### 3. Verify Python Environment
- [ ] Python 3.8+ is installed
- [ ] Virtual environment is activated (if using one)
- [ ] All required packages are installed

---

## EXECUTION STEPS

### STEP 1: Run the Complete Pipeline (Recommended)
**Purpose:** Execute the entire threat detection workflow automatically

**Command:**
```powershell
cd "C:\Users\karol\OneDrive\Pulpit\Master ML_AI\Code"
python main.py
```

**What happens:**
1. **Data Analysis** - Analyzes all 7 CSV datasets for structure, patterns, and threat types
2. **Dataset Creation** - Creates three consolidated training datasets:
   - `ddos_training_dataset.csv` - Network traffic features for DDoS detection
   - `phishing_training_dataset.csv` - Communication patterns for Phishing detection
   - `intrusion_training_dataset.csv` - Session data for intrusion detection
3. **Model Training** - Trains ensemble ML models:
   - DDoS Model: Random Forest + Gradient Boosting
   - Phishing Model: Logistic Regression + Random Forest
4. **Model Saving** - Saves trained models to `Code/models/` directory
5. **Prediction Testing** - Tests models with sample data

**Expected Output:**
- Console logs showing progress
- `Code/threat_detection.log` - Detailed execution log
- `Code/datasets/` - Consolidated training datasets
- `Code/models/` - Trained model files (.pkl)

**Estimated Runtime:** 5-15 minutes (depending on hardware)

---

### STEP 2: Individual Module Execution

#### 2A. Data Analysis Only
**Purpose:** Examine datasets without creating new files

**Command:**
```powershell
cd "C:\Users\karol\OneDrive\Pulpit\Master ML_AI\Code"
python -c "from data_analyzer import DataAnalyzer; analyzer = DataAnalyzer(r'C:\Users\karol\OneDrive\Pulpit\Master ML_AI\Threat_Detection_Model_1'); analyzer.run_complete_analysis()"
```

#### 2B. Create Datasets Only
**Purpose:** Generate training datasets without training models

**Command:**
```powershell
cd "C:\Users\karol\OneDrive\Pulpit\Master ML_AI\Code"
python -c "from dataset_creator import DatasetCreator; creator = DatasetCreator(r'C:\Users\karol\OneDrive\Pulpit\Master ML_AI\Threat_Detection_Model_1', r'.\datasets'); creator.create_all_datasets()"
```

#### 2C. Train Models Only
**Purpose:** Train models using existing datasets

**Command:**
```powershell
cd "C:\Users\karol\OneDrive\Pulpit\Master ML_AI\Code"
python -c "
from threat_detector import ThreatDetectionModel
import os
detector = ThreatDetectionModel('./models')
detector.train_all_models(
    './datasets/ddos_training_dataset.csv',
    './datasets/phishing_training_dataset.csv'
)
"
```

---

## USING TRAINED MODELS FOR PREDICTIONS

### Making DDoS Predictions
```python
from threat_detector import ThreatDetectionModel

detector = ThreatDetectionModel('./models')

# Load pre-trained models
import pickle
with open('./models/ddos_model.pkl', 'rb') as f:
    ddos_data = pickle.load(f)
detector.ddos_model = ddos_data

with open('./models/ddos_scaler.pkl', 'rb') as f:
    detector.ddos_scaler = pickle.load(f)

# Example: Network traffic features
features = [
    80,      # Destination Port
    1000,    # Flow Duration
    50,      # Total Fwd Packets
    5000,    # Total Length of Fwd Packets
    2500,    # Fwd Packet Length Max
    0,       # Fwd Packet Length Min
    100,     # Fwd Packet Length Mean
    50,      # Fwd Packet Length Std
    2000,    # Bwd Packet Length Max
    0,       # Bwd Packet Length Min
    80,      # Bwd Packet Length Mean
    40,      # Bwd Packet Length Std
    5.0,     # Flow Bytes/s
    0.05,    # Flow Packets/s
    100,     # Flow IAT Mean
    50,      # Flow IAT Std
]

result = detector.predict_ddos(features)
# Output: {'is_ddos': 1/0, 'confidence': 0-1, 'threat_level': 'HIGH/MEDIUM/LOW'}
```

### Making Phishing Predictions
```python
# Similar process for phishing
result = detector.predict_phishing(features)
# Output: {'is_phishing': 1/0, 'confidence': 0-1, 'threat_level': 'HIGH/MEDIUM/LOW'}
```

---

## OUTPUT FILES EXPLANATION

### Generated Datasets
- **`Code/datasets/ddos_training_dataset.csv`**
  - Features: Network traffic metrics from CICIDs2017
  - Target: `is_ddos` (1=DDoS attack, 0=Normal traffic)
  - Size: ~10,000 balanced samples

- **`Code/datasets/phishing_training_dataset.csv`**
  - Features: Attack characteristics from Global Threats dataset
  - Target: `is_phishing` (1=Phishing, 0=Normal)
  - Size: ~10,000 samples

- **`Code/datasets/intrusion_training_dataset.csv`**
  - Features: Session and login characteristics
  - Target: `is_attack` (1=Attack detected, 0=Normal)
  - Size: ~9,500 samples

### Trained Models
- **`Code/models/ddos_model.pkl`** - DDoS detection ensemble model
- **`Code/models/ddos_scaler.pkl`** - Feature scaler for DDoS model
- **`Code/models/phishing_model.pkl`** - Phishing detection ensemble model
- **`Code/models/phishing_scaler.pkl`** - Feature scaler for Phishing model

### Logs
- **`Code/threat_detection.log`** - Complete execution log with timestamps

---

## TROUBLESHOOTING

### Issue: "No module named 'pandas'"
**Solution:**
```powershell
pip install pandas numpy scikit-learn
```

### Issue: "File not found: cicids2017_cleaned.csv"
**Solution:** Ensure all CSV files are in the `Threat_Detection_Model_1/` directory

### Issue: Models not training
**Solution:**
1. Check the log file: `Code/threat_detection.log`
2. Ensure datasets were created: Check `Code/datasets/` directory
3. Verify sufficient disk space and RAM available

### Issue: Low model accuracy
**Possible causes:**
- Imbalanced dataset (more normal traffic than attacks)
- Limited feature set from datasets
- Need more diverse training data

**Solutions:**
- Collect more attack samples
- Add more engineered features
- Adjust model hyperparameters in `threat_detector.py`

---

## MODEL ARCHITECTURE DETAILS

### DDoS Detection Model
- **Type:** Ensemble (Random Forest + Gradient Boosting)
- **Features:** 16 network traffic metrics
- **Target:** Binary classification (DDoS vs Normal)
- **Typical Accuracy:** 85-95%

### Phishing Detection Model
- **Type:** Ensemble (Logistic Regression + Random Forest)
- **Features:** Attack characteristics and metadata
- **Target:** Binary classification (Phishing vs Normal)
- **Typical Accuracy:** 80-90%

---

## PERFORMANCE METRICS INTERPRETATION

After model training, you'll see metrics like:
- **Accuracy:** % of correct predictions overall
- **Precision:** % of detected threats that are actual threats
- **Recall:** % of actual threats detected
- **F1-Score:** Balance between precision and recall

**Ideal values:** All metrics > 0.85 (85%)

---

## NEXT STEPS FOR IMPROVEMENT

1. **Data Collection:** Gather more real-world attack samples
2. **Feature Engineering:** Add more sophisticated features
3. **Model Tuning:** Adjust hyperparameters based on performance
4. **Real-time Integration:** Deploy models in production monitoring system
5. **Continuous Learning:** Retrain models with new attack patterns

---

## QUICK START (TL;DR)

```powershell
# Navigate to Code directory
cd "C:\Users\karol\OneDrive\Pulpit\Master ML_AI\Code"

# Install packages (first time only)
pip install pandas numpy scikit-learn

# Run complete pipeline
python main.py

# Check results
dir datasets\      # See generated datasets
dir models\        # See trained models
type threat_detection.log  # View detailed log
```

---

## CONTACT & SUPPORT

For detailed information, refer to:
- Source code comments in `main.py`, `data_analyzer.py`, `dataset_creator.py`, `threat_detector.py`
- Log file: `Code/threat_detection.log`
- Dataset documentation: Inside each CSV file

**Last Updated:** 2025-12-10
**Version:** 1.0.0

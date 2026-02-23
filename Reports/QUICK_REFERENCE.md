# SecIDS-CNN Quick Reference Guide v2.0

## 🚀 Quick Start Commands

### Launch Methods (Choose One):

#### 1. **Interactive UI** (Recommended)
```bash
python secids_main.py ui
# OR
./Launchers/QUICK_START_V2.sh ui
# OR
./Launchers/secids-ui
```

#### 2. **System Check**
```bash
python secids_main.py check
```

#### 3. **File-Based Detection**
```bash
# Analyze all CSV files
python secids_main.py detect file --all

# Analyze specific files
python secids_main.py detect file dataset1.csv dataset2.csv
```

#### 4. **Live Network Detection**
```bash
python secids_main.py detect live --interface eth0
python secids_main.py detect live --interface eth0 --window 10 --interval 5
```

#### 5. **Model Tester**
```bash
python secids_main.py model-test
```

#### 6. **Auto-Update Scheduler**
```bash
python secids_main.py auto-update
```

---

## 📦 Python API Usage

### System Integrator
```python
from system_integrator import SystemIntegrator

# Initialize everything
integrator = SystemIntegrator()
integrator.initialize_all()

# Or initialize components individually
model = integrator.load_detection_model()
countermeasure = integrator.initialize_countermeasures()
scheduler = integrator.start_scheduler()

# Get system status
status = integrator.get_status()
print(f"Model loaded: {status['model_loaded']}")
print(f"Countermeasures active: {status['countermeasure_active']}")
```

### Detection Model
```python
from secids_cnn import SecIDSModel
import pandas as pd

# Load model
model = SecIDSModel("Models/SecIDS-CNN.h5")

# Make predictions
data = pd.read_csv("your_data.csv")
predictions = model.predict(data)
probabilities = model.predict_proba(data)
```

### Countermeasures
```python
from ddos_countermeasure import DDoSCountermeasure

# Initialize
countermeasure = DDoSCountermeasure(
    block_threshold=5,
    time_window=60,
    auto_block=True
)

# Start monitoring
countermeasure.start()

# Report threat
countermeasure.report_threat(
    src_ip="192.168.1.100",
    dst_port=80,
    threat_type="DDoS"
)

# Get statistics
stats = countermeasure.get_statistics()
```

---

## 🗂️ Project Structure

```
SecIDS-CNN/
├── secids_main.py              # Main entry point
├── system_integrator.py        # Integration module
├── requirements.txt            # Dependencies
│
├── SecIDS-CNN/                 # Core detection
│   ├── secids_cnn.py
│   ├── run_model.py
│   └── SecIDS-CNN.h5
│
├── UI/                         # User interfaces
│   ├── terminal_ui_enhanced.py
│   ├── terminal_ui_v2.py
│   └── terminal_ui.py
│
├── Tools/                      # Utilities
│   ├── progress_utils.py
│   ├── system_checker.py
│   ├── wireshark_manager.py
│   └── report_generator.py
│
├── Countermeasures/            # Attack mitigation
│   └── ddos_countermeasure.py
│
├── Auto_Update/                # Automation
│   └── task_scheduler.py
│
├── Model_Tester/               # Model testing
│   └── Code/
│
└── Launchers/                  # Launch scripts
    ├── QUICK_START_V2.sh
    ├── secids
    └── secids-ui
```

---

## 🔧 Configuration

### Environment Variables
```bash
export TF_CPP_MIN_LOG_LEVEL=2     # Reduce TensorFlow logging
export TF_ENABLE_ONEDNN_OPTS=1    # Enable optimizations
```

### Config Files
- `Config/dataset_config.json` - Dataset paths
- `Config/command_shortcuts.json` - Command shortcuts
- `Config/command_history.json` - Command history

---

## 🧪 Testing

### Run System Diagnostics
```bash
python secids_main.py check
```

### Test Individual Components
```bash
# Test integrator
python system_integrator.py

# Test detection model
cd SecIDS-CNN && python secids_cnn.py

# Test UI
python UI/terminal_ui_enhanced.py

# Test countermeasures
python Countermeasures/test_countermeasure.py
```

---

## 📊 Common Workflows

### 1. **Quick Threat Scan**
```bash
# 1. Check system
python secids_main.py check

# 2. Run detection
python secids_main.py detect file --all

# 3. View results
ls -lh Results/
```

### 2. **Live Monitoring**
```bash
# Launch UI and select Live Detection
python secids_main.py ui
# Then choose: 1. Live Detection & Monitoring
```

### 3. **Model Training**
```bash
# Launch UI and select Model Training
python secids_main.py ui
# Then choose: 4. Model Training & Testing
```

---

## 🛠️ Troubleshooting

### Virtual Environment Issues
```bash
# Recreate environment
rm -rf .venv_test
python3 -m venv .venv_test
source .venv_test/bin/activate
pip install -r requirements.txt
```

### Import Errors
```bash
# Ensure all __init__.py files exist
find . -type d -name "__pycache__" -prune -o -type d -exec test ! -e {}/__init__.py \; -print

# Add to Python path manually
export PYTHONPATH=$PYTHONPATH:/path/to/SecIDS-CNN
```

### Permission Errors
```bash
# Fix launcher permissions
chmod +x Launchers/*.sh
chmod +x secids_main.py
```

### Missing Dependencies
```bash
# Install from requirements
pip install -r requirements.txt

# Or install individually
pip install tensorflow keras numpy pandas scikit-learn scapy rich tqdm
```

---

## 📈 Performance Tips

1. **Use GPU if available:** TensorFlow will auto-detect
2. **Batch processing:** Use `--all` for multiple files
3. **Adjust window/interval:** For live detection, tune parameters
4. **Monitor resources:** Use `htop` or Task Manager
5. **Clear old results:** Regularly archive old detection results

---

## 🔐 Security Notes

- Run live capture as root/sudo (requires raw socket access)
- Review countermeasure actions before enabling auto-block
- Keep model files secured (they contain trained weights)
- Regularly update dependencies for security patches

---

## 📝 Getting Help

```bash
# Main help
python secids_main.py --help

# Detection help
python secids_main.py detect --help
python secids_main.py detect file --help
python secids_main.py detect live --help

# In UI, press 'H' for help
```

---

## 🔗 Integration Points

All components are linked through `system_integrator.py`:

```
secids_main.py → system_integrator.py → [All Components]
```

Access any component programmatically:
```python
from system_integrator import get_integrator

integrator = get_integrator()
# Now use integrator.load_detection_model(), etc.
```

---

**Version:** 2.0.0  
**Updated:** January 31, 2026  
**Status:** Production Ready ✅

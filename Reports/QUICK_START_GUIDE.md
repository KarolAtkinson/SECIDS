# SecIDS-CNN Quick Start Guide
**Version 2.0.0 Enhanced** | Updated: February 7, 2026

## 🚀 Getting Started

### Launch the Enhanced UI (Recommended)
```bash
python3 UI/terminal_ui_enhanced.py
```

The UI now has **all features fully functional** with intuitive menus and real-time command execution.

---

## 📋 Main Menu Options

### 1️⃣ Live Detection & Monitoring
Detect threats in real-time from network traffic

**Quick Options:**
- **Fast Mode**: 6s window, 4s interval - For quick scans
- **Standard Mode**: 10s window, 4s interval - Balanced performance
- **Slow Mode**: 20s window, 10s interval - Maximum accuracy
- **Deep Scan**: 600s duration, 60s interval - Comprehensive analysis

### 2️⃣ Network Capture Operations
Capture network packets for analysis

**Quick Options:**
- **Quick Capture**: 120 seconds of traffic
- **Custom Capture**: Define your own duration
- **Continuous Capture**: Long-running capture with 120s windows

### 3️⃣ File-Based Analysis
Analyze existing CSV or PCAP files

**Quick Options:**
- **Single File**: Analyze one CSV file
- **Batch Analysis**: Process all CSV files
- **PCAP Conversion**: Convert PCAP to CSV format

### 4️⃣ Model Training & Testing
Train and evaluate detection models

**Quick Options:**
- **Train SecIDS**: Train the main CNN model
- **Train Unified**: Train the unified threat model
- **Test Model**: Evaluate model performance

### 5️⃣ System Configuration
Configure and verify system settings

**Quick Options:**
- **Check Interfaces**: List available network interfaces
- **Verify TensorFlow**: Check TensorFlow installation
- **System Diagnostics**: Run health checks

### 6️⃣ View Reports & Results
Access detection results and reports

**Quick Options:**
- **List Results**: View recent detection results
- **Latest Report**: View most recent analysis
- **System Logs**: Check system activity

### 7️⃣ Utilities & Tools
Additional tools and utilities

**Quick Options:**
- **List Datasets**: View available data files
- **List Models**: View trained models
- **View Whitelist/Blacklist**: Check IP lists

### 8️⃣ Command History
View and manage command history

**Quick Options:**
- **View History**: See last 20 commands
- **Rerun Last**: Execute previous command
- **Clear History**: Remove all history

### 9️⃣ Settings & Configuration
Customize default settings

**Quick Options:**
- **Change Interface**: Set default network interface
- **Set Defaults**: Configure timing parameters

---

## ⚡ Command Line Quick Reference

### Live Detection Commands

```bash
# Fast detection (6s window, 4s interval)
sudo python3 SecIDS-CNN/run_model.py live --iface eth0 --window 6 --interval 4

# Standard detection (10s window, 4s interval)
sudo python3 SecIDS-CNN/run_model.py live --iface eth0 --window 10 --interval 4

# Slow detection (20s window, 10s interval)
sudo python3 SecIDS-CNN/run_model.py live --iface eth0 --window 20 --interval 10
```

### Deep Scan Commands

```bash
# Live deep scan (600s duration, 60s interval)
sudo python3 Tools/deep_scan.py --iface eth0 --duration 600 --interval 60

# File deep scan (10 passes)
python3 Tools/deep_scan.py --file path/to/data.csv --passes 10
```

### Capture Commands

```bash
# Quick capture (120 seconds)
sudo dumpcap -i eth0 -a duration:120 -w Captures/capture_$(date +%s).pcap

# Continuous capture (120s windows)
sudo python3 Tools/continuous_live_capture.py --iface eth0 --window 120 --interval 120
```

### File Analysis Commands

```bash
# Analyze single CSV
python3 SecIDS-CNN/run_model.py file path/to/data.csv

# Analyze all CSV files
python3 SecIDS-CNN/run_model.py file --all

# Convert PCAP to CSV
python3 Tools/pcap_to_secids_csv.py -i capture.pcap -o output.csv
```

---

## 🎯 Using the Command Library

The command library provides shortcuts for common operations:

### List All Commands
```bash
python3 Tools/command_library.py list
```

### Execute a Command
```bash
# Basic execution
python3 Tools/command_library.py exec verify

# With parameters
python3 Tools/command_library.py exec live-detect-fast --param iface=eth0

# Dry run (show command without executing)
python3 Tools/command_library.py exec pipeline-capture --param iface=eth0 --dry-run
```

### View Command History
```bash
python3 Tools/command_library.py history
```

### Manage Favorites
```bash
# Add to favorites
python3 Tools/command_library.py add-favorite live-detect-fast

# View favorites
python3 Tools/command_library.py favorites
```

---

## 📊 New Timing Parameters (All Doubled!)

| Scan Type | Duration/Window | Interval | Passes |
|-----------|-----------------|----------|--------|
| **Deep Scan (Live)** | 600s | 60s | 6 |
| **Deep Scan (File)** | N/A | N/A | 10 |
| **Fast Detection** | 6s | 4s | N/A |
| **Standard Detection** | 10s | 4s | N/A |
| **Slow Detection** | 20s | 10s | N/A |
| **Continuous Capture** | 120s | 120s | N/A |
| **Quick Capture** | 120s | N/A | N/A |

---

## 🔧 Common Workflows

### Workflow 1: Quick Threat Check
```bash
# Launch UI
python3 UI/terminal_ui_enhanced.py

# Select: 1 (Detection) → 1 (Fast Detection)
# Enter interface: eth0
# Wait for scan to complete
# View results in Results/ folder
```

### Workflow 2: Deep Security Analysis
```bash
# Launch deep scan
sudo python3 Tools/deep_scan.py --iface eth0 --duration 600 --interval 60

# Monitor output for threats
# Review report in Results/deep_scan_report_*.json
```

### Workflow 3: Analyze Captured Traffic
```bash
# 1. Capture traffic
sudo dumpcap -i eth0 -a duration:120 -w Captures/test.pcap

# 2. Convert to CSV
python3 Tools/pcap_to_secids_csv.py -i Captures/test.pcap -o Results/test.csv

# 3. Analyze
python3 SecIDS-CNN/run_model.py file Results/test.csv

# 4. Review results
ls -lt Results/detection_results_*.csv
```

### Workflow 4: Complete Pipeline
```bash
# Run full pipeline (capture, train, detect)
python3 Tools/pipeline_orchestrator.py --mode full

# Or specific stages:
# Capture only
python3 Tools/pipeline_orchestrator.py --mode capture --iface eth0 --duration 240

# Training only
python3 Tools/pipeline_orchestrator.py --mode train

# Detection only (live)
python3 Tools/pipeline_orchestrator.py --mode detect-live --iface eth0

# Detection only (batch)
python3 Tools/pipeline_orchestrator.py --mode detect-batch --input datasets/Test1.csv
```

---

## 🆘 Troubleshooting

### UI doesn't start
```bash
# Check if rich library is installed
pip install rich

# Check Python version
python3 --version  # Should be 3.8+

# Try from project root
cd /home/kali/Documents/Code/SECIDS-CNN
python3 UI/terminal_ui_enhanced.py
```

### Permission denied errors
```bash
# Use sudo for network operations
sudo python3 SecIDS-CNN/run_model.py live --iface eth0

# Or add user to network group
sudo usermod -a -G wireshark $USER
```

### TensorFlow not found
```bash
# Activate virtual environment
source .venv_test/bin/activate

# Or run through launcher
./Launchers/secids-ui
```

### Commands not executing from UI
```bash
# Verify command library exists
ls -l Tools/command_library.py

# Check permissions
chmod +x Tools/command_library.py

# Test command library directly
python3 Tools/command_library.py list
```

---

## 💡 Tips & Best Practices

### For Maximum Accuracy
- Use **Slow Detection** (20s window, 10s interval) for critical networks
- Run **Deep Scan** with full 600s duration
- Use **10 passes** for file analysis

### For Real-Time Monitoring
- Use **Fast Detection** (6s window, 4s interval) for quick checks
- Monitor Results/ folder for new detection files
- Check system logs regularly

### For Resource Efficiency
- Use **Standard Detection** (10s window, 4s interval) as default
- Schedule deep scans during low-traffic periods
- Clean temp files regularly via Utilities menu

### For Best Results
1. Keep whitelist/blacklist updated
2. Train models on recent traffic patterns
3. Review and tune detection thresholds
4. Monitor false positive rates
5. Regular system health checks

---

## 📁 Important File Locations

| Type | Location |
|------|----------|
| **Detection Results** | `Results/detection_results_*.csv` |
| **Threat Reports** | `Results/*_report_*.{md,json}` |
| **Deep Scan Reports** | `Results/deep_scan_*.json` |
| **Captures** | `Captures/capture_*.pcap` |
| **Datasets** | `SecIDS-CNN/datasets/` |
| **Models** | `SecIDS-CNN/*.h5`, `Models/` |
| **Logs** | `Logs/` |
| **Config** | `Config/`, `UI/ui_config.json` |
| **Archives** | `Archives/` |

---

## 🔗 Related Documentation

- **Full Upgrade Report**: `FRONTEND_BACKEND_UPGRADE_REPORT.md`
- **Master Manual**: `Master-Manual.md`
- **System Integration**: `system_integrator.py`
- **Command Library Help**: `python3 Tools/command_library.py --help`
- **UI README**: `UI/README.md`

---

## 📞 Support

For issues or questions:
1. Check `Master-Manual.md` for detailed documentation
2. Review `FRONTEND_BACKEND_UPGRADE_REPORT.md` for recent changes
3. Run system diagnostics: `python3 Tools/system_checker.py`
4. Check logs in `Logs/` directory

---

**Last Updated:** February 7, 2026  
**System Version:** SecIDS-CNN 2.0.0 Enhanced  
**Status:** ✅ Fully Operational

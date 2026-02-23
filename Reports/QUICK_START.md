# Quick Start Guide - Enhancement Update

## What's New

✅ **Progress bars** for all major operations  
✅ **Automatic Wireshark management** for live capture  
✅ **Better interface selection** (eth0, any, wlan0, etc.)  
✅ **Enhanced user experience** with visual feedback  

## Installation

```bash
cd /home/kali/Documents/Code/SECIDS-CNN/SecIDS-CNN
pip install -r requirements.txt
```

## Quick Test

Verify everything is working:

```bash
cd /home/kali/Documents/Code/SECIDS-CNN
python3 Tools/test_enhancements.py
```

## Usage Examples

### 1. Live Capture with Auto-Wireshark (NEW!)

```bash
cd /home/kali/Documents/Code/SECIDS-CNN/SecIDS-CNN

# Capture on eth0
sudo python3 run_model.py live --iface eth0 --window 60

# Capture on all interfaces
sudo python3 run_model.py live --iface any --window 60
```

**What happens:**
1. 🦈 Wireshark auto-starts in background
2. 📊 Progress bars show capture status
3. 🔍 Real-time threat detection runs
4. 🛑 Wireshark auto-closes on exit (Ctrl+C)

### 2. File Analysis with Progress Bars (ENHANCED)

```bash
cd /home/kali/Documents/Code/SECIDS-CNN/SecIDS-CNN
python3 run_model.py file path/to/traffic.csv
```

**You'll see:**
- 📁 Loading progress bar
- ⚙️ Preprocessing progress
- 🎯 Prediction progress
- ✅ Results summary

### 3. Model Training with Visual Feedback (ENHANCED)

```bash
cd /home/kali/Documents/Code/SECIDS-CNN/SecIDS-CNN
python3 train_and_test.py
```

**New features:**
- 📊 Epoch-by-epoch progress
- 📈 Real-time loss/accuracy display
- ⏱️ Time estimates

### 4. Continuous Live Capture (ENHANCED)

```bash
cd /home/kali/Documents/Code/SECIDS-CNN/Tools
sudo python3 continuous_live_capture.py \
    --iface eth0 \
    --window 5 \
    --interval 2 \
    --enable-countermeasure
```

**Features:**
- 🦈 Auto Wireshark management
- 📊 Live progress bars
- 🚨 Real-time threat alerts
- 🛡️ Automatic countermeasures

## Interface Selection Guide

Choose the right interface for your needs:

| Interface | Use Case | Pros | Cons |
|-----------|----------|------|------|
| `eth0` | Production monitoring | Focused, efficient | Single interface only |
| `any` | Testing/full monitoring | Captures all traffic | Higher overhead |
| `wlan0` | Wireless monitoring | WiFi specific | Wireless only |

## Troubleshooting

### Issue: "wireshark not found"

```bash
sudo apt-get update
sudo apt-get install wireshark dumpcap
```

### Issue: "Permission denied"

```bash
# Option 1: Run with sudo
sudo python3 run_model.py live --iface eth0

# Option 2: Set capabilities (one-time)
sudo setcap cap_net_raw,cap_net_admin=eip $(which dumpcap)
```

### Issue: "tqdm not found"

```bash
pip install tqdm
```

### Issue: Wireshark won't close

```bash
sudo killall wireshark dumpcap
```

## File Locations

All new files are properly organized:

```
📁 SecIDS-CNN/
├── 📁 Tools/
│   ├── 🆕 wireshark_manager.py     # Wireshark automation
│   ├── 🆕 progress_utils.py        # Progress bar utilities
│   ├── 🆕 test_enhancements.py     # Test script
│   ├── ✏️ continuous_live_capture.py (updated)
│   ├── ✏️ live_capture_and_assess.py (updated)
│   └── ✏️ pcap_to_secids_csv.py     (updated)
├── 📁 SecIDS-CNN/
│   ├── ✏️ run_model.py              (updated)
│   ├── ✏️ train_and_test.py         (updated)
│   └── ✏️ requirements.txt          (updated)
└── 📁 Reports/
    ├── 🆕 ENHANCEMENT_UPDATE.md     # Full documentation
    └── 🆕 QUICK_START.md            # This file
```

## Key Commands

```bash
# Test everything
python3 Tools/test_enhancements.py

# Live capture with Wireshark
sudo python3 SecIDS-CNN/run_model.py live --iface eth0

# File analysis
python3 SecIDS-CNN/run_model.py file data.csv

# Training
python3 SecIDS-CNN/train_and_test.py

# Full featured live capture
sudo python3 Tools/continuous_live_capture.py \
    --iface any --window 5 --interval 2 \
    --enable-countermeasure --enable-whitelist
```

## Next Steps

1. **Install dependencies**: `pip install -r SecIDS-CNN/requirements.txt`
2. **Run test**: `python3 Tools/test_enhancements.py`
3. **Try live capture**: `sudo python3 SecIDS-CNN/run_model.py live --iface eth0`
4. **Read full docs**: `Reports/ENHANCEMENT_UPDATE.md`

## Support

For detailed documentation, see:
- **Full Documentation**: `Reports/ENHANCEMENT_UPDATE.md`
- **Project Manual**: `Master-Manual.md`

---

**Status**: ✅ Complete and Ready to Use  
**Date**: January 29, 2026  
**Version**: 2.0

# SecIDS-CNN Enhancement Update

## New Features Added

This update adds **progress bars** for all major operations and **automatic Wireshark management** for live capture sessions.

### 1. Progress Bar Utilities

All major operations now display progress bars for better user experience:

- **Data loading**: Shows progress when loading CSV files
- **Preprocessing**: Displays progress during data preprocessing
- **Model training**: Visual feedback during training epochs (with tqdm-keras integration)
- **Predictions**: Progress tracking for batch predictions
- **File conversion**: Shows progress when converting PCAP files to CSV
- **Live capture**: Real-time progress for packet and flow processing

**Location**: `Tools/progress_utils.py`

**Usage Examples**:
```python
from progress_utils import DataLoadingProgress, TrainingProgress

# For data loading
with DataLoadingProgress.create(total_files) as pbar:
    for file in files:
        load_data(file)
        pbar.update()

# For training
with TrainingProgress.create(epochs) as pbar:
    for epoch in range(epochs):
        train_epoch()
        pbar.update()
```

### 2. Wireshark Manager

Automatic Wireshark management for live capture sessions:

- **Auto-start**: Wireshark automatically opens when live capture begins
- **Auto-close**: Wireshark gracefully closes when capture ends or program stops
- **Interface support**: Works with specific interfaces (eth0, wlan0) or 'any' for all interfaces
- **Background mode**: Runs dumpcap in background for efficient capture without GUI overhead
- **Process management**: Properly handles process cleanup and zombie process prevention

**Location**: `Tools/wireshark_manager.py`

**Features**:
- Context manager support for automatic cleanup
- Graceful shutdown with SIGTERM followed by SIGKILL if needed
- Process detection to avoid duplicate Wireshark instances
- Configurable interface selection (eth0, any, etc.)

**Usage Examples**:
```python
from wireshark_manager import WiresharkManager

# Context manager (recommended)
with WiresharkManager('eth0') as ws:
    # Do capture work
    capture_traffic()
    # Wireshark auto-closes when done

# Manual control
manager = WiresharkManager('any', use_any=True)
manager.start()
# ... do work ...
manager.stop()
```

## Updated Files

### Core Files

1. **SecIDS-CNN/run_model.py**
   - Added progress bars for data loading
   - Integrated Wireshark auto-start/stop for live capture mode
   - Progress tracking for predictions
   - Enhanced error handling

2. **SecIDS-CNN/train_and_test.py**
   - Added tqdm-keras callbacks for training progress
   - Progress bars for data loading and preprocessing
   - Visual feedback during model training epochs

### Tools

3. **Tools/continuous_live_capture.py**
   - Wireshark auto-management integrated
   - Progress bars for packet processing
   - Enhanced live capture workflow

4. **Tools/live_capture_and_assess.py**
   - Wireshark auto-start at session beginning
   - Wireshark auto-stop on exit or interrupt
   - Interface selection support (eth0/any)

5. **Tools/pcap_to_secids_csv.py**
   - Progress bars for packet reading
   - Progress bars for flow feature computation
   - Visual feedback during conversion process

### New Utility Modules

6. **Tools/progress_utils.py** (NEW)
   - Standardized progress bar classes
   - Multiple progress bar types for different operations
   - Context manager support
   - Multi-stage progress tracking

7. **Tools/wireshark_manager.py** (NEW)
   - Complete Wireshark lifecycle management
   - Process control and cleanup
   - Interface configuration
   - Background/foreground mode support

## Installation

Install the new dependencies:

```bash
cd SecIDS-CNN
pip install -r requirements.txt
```

New dependencies added:
- `tqdm>=4.65.0` - Progress bars
- `psutil>=5.9.0` - Process management for Wireshark
- `scapy>=2.5.0` - Already included, but now explicitly listed

## Usage Examples

### Running Live Capture with Wireshark (NEW)

The program now automatically opens Wireshark when you start a live capture:

```bash
# Using eth0 interface
cd SecIDS-CNN
sudo python3 run_model.py live --iface eth0 --window 60 --interval 60

# Using 'any' interface (captures all interfaces)
sudo python3 run_model.py live --iface any --window 60 --interval 60
```

Wireshark will:
1. **Auto-start** when the program begins
2. Capture traffic on the specified interface
3. **Auto-close** when you press Ctrl+C or the program ends

### File-Based Detection with Progress Bars (ENHANCED)

File processing now shows progress:

```bash
cd SecIDS-CNN
python3 run_model.py file path/to/traffic.csv
```

You'll see:
- Progress bar for loading files
- Progress bar for preprocessing
- Progress bar for predictions

### Training with Progress Bars (ENHANCED)

Training now shows detailed progress:

```bash
cd SecIDS-CNN
python3 train_and_test.py
```

You'll see:
- Loading progress
- Training progress per epoch with loss/accuracy
- Validation progress

### Continuous Live Capture (ENHANCED)

```bash
cd Tools
sudo python3 continuous_live_capture.py --iface eth0 --window 5 --interval 2 --enable-countermeasure
```

Features:
- Wireshark auto-starts
- Progress bars for packet/flow processing
- Real-time threat detection
- Automatic countermeasures (if enabled)
- Clean shutdown with Wireshark auto-close

## Configuration Options

### Wireshark Interface Selection

You can use either:
- **Specific interface**: `--iface eth0` (recommended for production)
- **All interfaces**: `--iface any` (better for testing/monitoring all traffic)

The code automatically determines whether to use 'any' mode based on the interface name.

### Progress Bar Customization

Progress bars are automatically styled with colors:
- Blue: Data loading
- Cyan: Preprocessing
- Green: Training/Capture
- Yellow: Predictions
- Magenta: File conversion

## Technical Details

### Wireshark Process Management

The WiresharkManager uses:
- `subprocess.Popen` for process spawning
- `os.setsid()` for process group creation
- `SIGTERM` for graceful shutdown
- `SIGKILL` as fallback for stuck processes
- `psutil` for process detection and management

### Progress Bar Implementation

Progress bars use the `tqdm` library:
- Standard tqdm for general operations
- tqdm.keras callbacks for TensorFlow training
- Custom context managers for clean resource management
- Automatic color coding for different operation types

## Troubleshooting

### Wireshark doesn't start

**Issue**: "wireshark not found" or "dumpcap not found"

**Solution**: Install Wireshark:
```bash
sudo apt-get install wireshark dumpcap  # Debian/Ubuntu
sudo yum install wireshark              # RedHat/CentOS
```

### Permission denied for packet capture

**Issue**: "Need elevated permissions to capture"

**Solution**: Run with sudo or configure capabilities:
```bash
# Option 1: Run with sudo
sudo python3 run_model.py live --iface eth0

# Option 2: Set capabilities (one-time setup)
sudo setcap cap_net_raw,cap_net_admin=eip $(which dumpcap)
sudo setcap cap_net_raw=ep $(which python3)
```

### Progress bars not showing

**Issue**: Progress bars don't appear

**Solution**: Install tqdm:
```bash
pip install tqdm
```

### Wireshark doesn't close properly

**Issue**: Wireshark process remains after program exit

**Solution**: The manager will attempt to kill remaining processes. If issues persist:
```bash
# Manually kill wireshark/dumpcap
sudo killall wireshark dumpcap
```

## File Organization

All files are properly organized:

```
SecIDS-CNN/
├── SecIDS-CNN/
│   ├── run_model.py (UPDATED)
│   ├── train_and_test.py (UPDATED)
│   ├── requirements.txt (UPDATED)
│   └── ...
├── Tools/
│   ├── wireshark_manager.py (NEW)
│   ├── progress_utils.py (NEW)
│   ├── continuous_live_capture.py (UPDATED)
│   ├── live_capture_and_assess.py (UPDATED)
│   ├── pcap_to_secids_csv.py (UPDATED)
│   └── ...
└── Reports/
    └── ENHANCEMENT_UPDATE.md (THIS FILE)
```

## Benefits

1. **Better User Experience**: Visual feedback for all long-running operations
2. **Automatic Workflow**: No manual Wireshark management needed
3. **Professional Output**: Clean, colored progress bars with time estimates
4. **Resource Management**: Proper cleanup of Wireshark processes
5. **Flexible Configuration**: Support for multiple interfaces (eth0, any, etc.)
6. **Error Handling**: Graceful degradation if Wireshark or progress bars unavailable

## Compatibility

- **Python**: 3.8+
- **Operating Systems**: Linux (tested on Kali/Debian/Ubuntu)
- **Wireshark**: Any recent version with dumpcap
- **Dependencies**: All automatically handled via requirements.txt

## Future Enhancements

Potential future improvements:
- Remote Wireshark session support
- Custom progress bar themes
- Progress persistence across sessions
- Distributed capture across multiple interfaces
- Web-based progress monitoring

---

**Date**: January 29, 2026
**Version**: 2.0
**Status**: ✅ Complete and Integrated

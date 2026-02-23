# Terminal UI Enhanced - User Guide

**Version:** 2.0.0  
**Last Updated:** February 7, 2026

## What Has Changed

The Terminal UI has been completely redesigned to be more intuitive and user-friendly:

### ✅ Fixed Issues
1. **Direct Number Selection** - Pressing a number (1-9/0) immediately takes you into that menu
2. **Two-Panel Layout** - Consistent beautiful layout throughout all menus
3. **No More Two-Stage System** - No confusing "select then engage" - just press a number and go
4. **Progress Feedback** - Commands show execution progress and output
5. **Easy Navigation** - Press "0" or "B" to go back, "Q" to quit anytime

### 🎯 How to Use It

#### Main Menu
```
1. The left panel shows all available actions (numbered 1-9, 0)
2. The right panel shows details of the highlighted action
3. Press the number to enter that menu immediately
4. Or press ENTER to execute the currently highlighted option
```

#### Inside Submenus  
```
1. Same two-panel layout - options on left, details on right
2. Press a number (like "1") to execute that action
3. Enter any required parameters (like network interface)
4. Watch the progress/output
5. Press "0" or "B" to go back to main menu
```

## Usage Examples

### Starting the UI
```bash
cd /home/kali/Documents/Code/SECIDS-CNN
.venv_test/bin/python UI/terminal_ui_enhanced.py
```

### Example Session: File Detection
```
1. Launch UI
2. Press "1" → Goes into Live Detection & Monitoring menu
3. Press "6" → Selects File-Based Detection
4. Enter file path: SecIDS-CNN/datasets/MD_20260129_145407.csv
5. Watch progress as detection runs
6. Press Enter when done
7. Press "0" to return to main menu
```

### Example Session: Live Detection
```
1. Launch UI
2. Press "1" → Live Detection menu
3. Press "1" → Quick live detection
4. Enter interface: eth0
5. Detection starts (requires sudo)
6. Ctrl+C to stop when done
7. Press Enter to continue
8. Press "0" to go back
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| **1-9** | Select and execute that action immediately |
| **0** | Go back to previous menu OR exit |
| **ENTER** | Execute currently highlighted action |
| **Q** | Quit the application |
| **H** | Show help |
| **B** | Go back (alternative to 0) |

## Menu Structure

```
Main Menu
├── 1. Live Detection & Monitoring
│   ├── 1. Live Detection (Quick)
│   ├── 2. Live Detection (Standard)
│   ├── 3. Live Detection (Slow)
│   ├── 4. Deep Scan (Live)
│   ├── 5. Deep Scan (File)
│   ├── 6. File-Based Detection
│   └── 0. Back
├── 2. Network Capture Operations
│   ├── 1. Quick Capture (120s)
│   ├── 2. Custom Duration
│   ├── 3. Continuous Capture
│   ├── 4. List Captures
│   ├── 5. Pipeline Capture
│   └── 0. Back
├── 3. File-Based Analysis
│   ├── 1. Analyze CSV
│   ├── 2. Analyze PCAP
│   ├── 3. Batch Analysis
│   ├── 4. PCAP to CSV
│   ├── 5. Enhance Dataset
│   └── 0. Back
└── ... (more menus)
```

## Tips

1. **Use numbers for speed** - Just press "3" then "1" to quickly navigate
2. **Sample file path** - Default is provided: `SecIDS-CNN/datasets/MD_20260129_145407.csv`
3. **Network interface** - Usually "eth0" on most systems, UI remembers your last choice
4. **Live detection** - Requires sudo permissions (password prompt will appear)
5. **Check results** - After detection, results are saved to `Results/` folder

## Troubleshooting

**UI doesn't start:**
```bash
# Make sure virtual environment is active
cd /home/kali/Documents/Code/SECIDS-CNN
.venv_test/bin/python UI/terminal_ui_enhanced.py
```

**Keystrokes don't work:**
- Make sure you press ENTER after typing a number
- The UI uses regular input(), not special key capture
- Type the number and press ENTER

**Menu doesn't respond:**
- Try pressing "Q" to quit and restart
- Make sure terminal window is focused and active

**Commands fail:**
- Check that required files exist (models, datasets)
- Live detection needs sudo: `sudo .venv_test/bin/python UI/terminal_ui_enhanced.py`
- Verify network interface name: `ip link show`

## Features

### ✨ New in Version 2.0
- **Immediate action selection** - no more two-stage system
- **Consistent two-panel layout** - beautiful layout in all menus
- **Better navigation** - intuitive controls throughout
- **Progress feedback** - see what's happening during execution
- **Config memory** - remembers your last interface, file paths
- **Command history** - tracks all executed commands

### 🎨 Visual Design
- Clean two-panel design
- Color-coded elements (cyan for titles, yellow for selections, green for status)
- Clear section separators
- Responsive to terminal size
- Professional appearance

## Known Limitations

1. **Terminal size** - Works best at 120x30 or larger
2. **Sudo required** - Live detection needs elevated privileges
3. **No arrow key navigation** - Use numbers instead (simpler and faster)
4. **Background tasks** - Can't run multiple detections simultaneously in UI

## Getting Help

Inside the UI, press **"H"** to see the help screen with keyboard shortcuts and tips.

For technical issues, refer to:
- [Master-Manual.md](../Master-Manual.md) - Complete system documentation
- [QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md) - Quick start instructions

## Version History

**2.0.0** (2026-02-07)
- Complete UI redesign
- Fixed all control issues
- Implemented two-panel layout for all menus
- Added immediate action selection
- Improved navigation and feedback

**1.0.0** (2026-01-31)
- Initial release with two-stage system
- Basic two-panel main menu
- Legacy submenu displays

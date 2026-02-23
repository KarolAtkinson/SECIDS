# SecIDS-CNN Terminal UI

Interactive terminal interface for easy access to all SecIDS-CNN functions.

## Features

- **Simple Keyboard Navigation**: Use keys 1-0 to access functions
- **Save/Load Configuration**: Remembers your last used settings
- **Command History**: Track and re-run previous commands
- **Organized Menus**: Categorized access to all system functions
- **Beautiful Terminal UI**: Rich formatting with colors and tables

## Quick Start

### Method 1: System-Wide Command (Recommended)

Launch from anywhere, just like Wireshark or any system tool:

```bash
# One-time setup
cd /home/kali/Documents/Code/SECIDS-CNN
sudo ln -sf "$(pwd)/Launchers/secids-ui" /usr/local/bin/SECIDS

# Then run from anywhere
sudo SECIDS
```

**Benefits:**
- Run from any directory in your terminal
- No need to remember project path
- Works like standard system commands
- Same command every time

### Method 2: From Project Directory

```bash
cd /home/kali/Documents/Code/SECIDS-CNN
bash Launchers/secids-ui
```

### Method 3: Direct Python Execution

```bash
cd /home/kali/Documents/Code/SECIDS-CNN
python3 UI/terminal_ui.py
```

## Menu Structure

### Main Menu (Keys 1-0)

1. **Live Detection & Monitoring**
   - Standard/Fast/Slow detection modes
   - Custom parameters
   - Quick test detection

2. **Network Capture Operations**
   - Quick/Standard/Extended captures
   - Custom duration
   - List interfaces
   - View captured files

3. **File-Based Analysis**
   - Analyze CSV files
   - Test datasets
   - Master dataset analysis
   - Batch processing
   - PCAP conversion
   - Feature enhancement

4. **Model Training & Testing**
   - Train SecIDS-CNN
   - Train Unified Model
   - Train all models
   - Test performance
   - Smoke tests
   - Full test suite
   - Stress testing

5. **System Configuration & Setup**
   - Verify setup
   - Install dependencies
   - Check interfaces
   - Create master dataset
   - File organization
   - Task scheduler management

6. **View Reports & Results**
   - Detection results
   - Stress test reports
   - Threat analysis
   - System logs
   - Scheduler logs

7. **Utilities & Tools**
   - Threat origin analysis
   - Whitelist/Blacklist review
   - Dataset/Model listing
   - Archive viewing
   - Cleanup operations

8. **Command History**
   - View recent commands
   - Re-run previous commands
   - Track execution times

9. **Settings & Configuration**
   - Change default interface
   - Set default duration
   - Configure window size
   - Set interval
   - Clear history
   - Reset to defaults

0. **Exit**

## Configuration

Settings are saved in `UI/ui_config.json`:

```json
{
  "last_interface": "eth0",
  "last_duration": 60,
  "last_window": 5,
  "last_interval": 2,
  "theme": "default",
  "history": []
}
```

## Usage Examples

### Live Detection

1. Start UI: `python3 UI/terminal_ui.py`
2. Press `1` for Live Detection
3. Press `1` for Standard Detection
4. System starts monitoring your network
5. Press Ctrl+C to stop

### Quick Capture

1. Start UI
2. Press `2` for Network Capture
3. Press `1` for Quick Capture (60s)
4. Enter network interface (default: eth0)
5. Wait for capture to complete

### Analyze Dataset

1. Start UI
2. Press `3` for File-Based Analysis
3. Press `2` for Test1.csv analysis
4. View results

### Train Models

1. Start UI
2. Press `4` for Model Training
3. Press `3` for Train All Models
4. Wait for training to complete

## Keyboard Shortcuts

- **1-9, 0**: Menu navigation
- **Enter**: Confirm selection
- **Ctrl+C**: Cancel/Stop operation
- **ESC**: N/A (use 0 to go back)

## Command History

The UI tracks your last 20 commands with timestamps. Access via:
1. Main Menu → Press `8`
2. Select command number to re-run
3. Or press `0` to return to main menu

## Customization

### Changing Default Interface

1. Main Menu → Press `9` (Settings)
2. Press `1` (Change Interface)
3. Enter new interface name (e.g., wlan0)
4. Press `7` to save settings

### Setting Custom Detection Parameters

1. Main Menu → Press `1` (Detection)
2. Press `4` (Custom Detection)
3. Enter interface, window size, interval
4. Detection starts with your parameters

## Troubleshooting

### "Rich library not installed"
The UI will auto-install rich. If it fails:
```bash
pip install rich
```

### "Permission denied" for captures
Network capture requires sudo:
```bash
sudo python3 UI/terminal_ui.py
```

### Commands not working
Verify you're in the project directory:
```bash
cd /home/kali/Documents/Code/SECIDS-CNN
python3 UI/terminal_ui.py
```

### Interface not found
List available interfaces first:
1. Main Menu → Press `2` (Capture)
2. Press `5` (List Interfaces)
3. Note your interface name
4. Update in Settings (Menu 9)

## Integration with Existing Tools

The UI integrates with:
- **Launchers/secids.sh**: Quick launcher commands
- **Tools/command_library.py**: Command shortcuts
- **Scripts/**: All analysis and training scripts
- **Auto_Update/task_scheduler.py**: Scheduler management

## Advanced Features

### Save/Load Configuration

Configuration automatically saves when:
- You change settings
- You run a command (saves to history)
- You exit the program

### Command Re-execution

Access command history and re-run any previous command:
1. Menu 8 (History)
2. Select command number
3. Command executes immediately

### Batch Operations

The UI supports batch operations through:
- Menu 3 → Option 5: Batch Analysis
- Menu 4 → Option 3: Train All Models

## Tips

1. **First-time users**: Start with Menu 5 (Setup) → Option 1 (Verify Setup)
2. **Quick monitoring**: Menu 1 → Option 1 (Standard Detection)
3. **After capturing**: Menu 3 to analyze the captured data
4. **Regular maintenance**: Menu 5 → Option 5 (Organize Files)
5. **View results**: Menu 6 for all reports and logs

## System Requirements

- Python 3.7+
- Rich library (auto-installed)
- Terminal with ANSI color support
- Konsole, GNOME Terminal, or similar

## Support

For issues or questions:
1. Check Master-Manual.md for detailed documentation
2. Review Reports/README.md for system overview
3. Check Logs/ for error messages

## Version

- **UI Version**: 1.0
- **Release Date**: January 29, 2026
- **Compatible with**: SecIDS-CNN v3.0

## Future Enhancements

- Real-time detection monitoring dashboard
- Graph/chart visualization
- Export reports to PDF
- Email notifications
- Multiple theme support
- Plugin system for custom commands

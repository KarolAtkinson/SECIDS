# File Organization System

## Overview
Automated file organization system to maintain project structure by moving loose files (.json, .md, .log, .pcap) to their designated folders.

## Components

### 1. organize_files.py
**Location:** `Scripts/organize_files.py`
**Purpose:** Automatically organizes loose files into proper directories
**Schedule:** Runs daily via task scheduler (integrated into project_cleanup.sh)

**Organized File Types:**
- **Reports (.md files)**: → `Reports/`
  - Exception: `Master-Manual.md` stays in root
- **Test Results (.json files)**: → `Stress_Test_Results/`
  - Pattern: `stress_test_report_*.json`
- **Logs (.log files)**: → `Logs/`
- **Config Files (.json)**: → `Config/`
  - command_history.json, command_shortcuts.json, dataset_config.json
- **PCAP Files (.pcap)**: → `Captures/`

### 2. project_cleanup.sh Integration
**Location:** `Launchers/project_cleanup.sh`
**Updated:** Integrated organize_files.py as step 2/7
**Schedule:** Daily execution via task scheduler (every 24 hours)

**Cleanup Steps:**
1. [1/7] Ensure folder structure exists
2. [2/7] Run automated file organization (organize_files.py)
3. [3/7] Organize remaining root directory files
4. [4/7] Organize stress test reports
5. [5/7] Organize CSV files
6. [6/7] Manage documentation
7. [7/7] Check redundant documentation

### 3. Task Scheduler Configuration
**Location:** `Auto_Update/schedulers/task_config.json`
**Task:** `dataset_cleanup`
**Interval:** Every 24 hours
**Script:** `Launchers/project_cleanup.sh`
**Status:** Active (daemon PID 3652)

## Directory Structure

```
SECIDS-CNN/
├── Master-Manual.md           # Only file allowed in root
├── Reports/                   # All .md documentation
├── Config/                    # All .json config files
├── Stress_Test_Results/       # All stress test .json reports
├── Logs/                      # All .log files
├── Captures/                  # All .pcap files
├── Scripts/
│   └── organize_files.py      # Auto-organization script
└── Launchers/
    └── project_cleanup.sh     # Daily cleanup with organization
```

## Manual Execution

Run file organization manually:
```bash
python3 Scripts/organize_files.py
```

Run full cleanup manually:
```bash
bash Launchers/project_cleanup.sh
```

## How It Works

1. **Scheduled Execution**: Task scheduler runs project_cleanup.sh every 24 hours
2. **Auto-Organization**: Script scans project root for loose files
3. **Pattern Matching**: Identifies files by extension and naming patterns
4. **Safe Moving**: Only moves files from root to designated folders
5. **Verification**: Reports which files were moved and current status

## Output Examples

**When files need organizing:**
```
✓ Moved SYSTEM_UPDATE.md → Reports/
✓ Moved stress_test_report_20260129.json → Stress_Test_Results/
✓ Moved dataset_config.json → Config/
Total files organized: 3
```

**When everything is organized:**
```
✓ All files already in correct locations
```

## Benefits

- **Automatic Maintenance**: No manual intervention needed
- **Consistent Structure**: Files always in proper locations
- **Easy Debugging**: Clear reports of file movements
- **Scheduled Updates**: Runs daily without user action
- **Safe Operations**: Only moves files, never deletes
- **Flexible**: Can be run manually anytime

## Files Modified

1. `Scripts/organize_files.py` - Created
2. `Launchers/project_cleanup.sh` - Updated with organize_files.py integration
3. `Auto_Update/schedulers/task_config.json` - Already configured for daily cleanup

## Status

✅ System Active
✅ Scheduled Daily Execution
✅ Tested and Verified
✅ Integrated with Existing Cleanup Process

---
*Last Updated: 2026-01-29*
*System Version: 2.0*

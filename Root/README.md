# Root Module Organization

This folder contains core Python modules and main entry points for the SecIDS-CNN system.

## Purpose

The Root folder organizes main system files that were previously scattered in the project root directory. This improves project structure and maintainability.

## Contents

### Main Entry Points
- **secids_main.py** - Main system entry point
- **integrated_workflow.py** - Complete workflow orchestration
- **system_integrator.py** - System integration utilities

### Test Suites
- **test_greylist.py** - Greylist system tests
- **test_integration.py** - Integration tests
- **test_validation.py** - Final validation tests
- **run_all_tests.sh** - Complete test runner

### Configuration
- **pyrightconfig.json** - Python type checking configuration
- **__init__.py** - Python package initialization

## Usage

### Running Main System
```bash
cd /home/kali/Documents/Code/SECIDS-CNN
sudo .venv_test/bin/python Root/secids_main.py
```

### Running Integrated Workflow
```bash
sudo .venv_test/bin/python Root/integrated_workflow.py --mode continuous --interface eth0
```

### Running Tests
```bash
# From project root
bash Root/run_all_tests.sh

# Or individual tests
.venv_test/bin/python Root/test_greylist.py
.venv_test/bin/python Root/test_integration.py
.venv_test/bin/python Root/test_validation.py
```

## Import Path

Python files in Root can import from project modules using:
```python
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'SecIDS-CNN'))
sys.path.insert(0, str(PROJECT_ROOT / 'Device_Profile'))
sys.path.insert(0, str(Path(__file__).parent))  # Add Root/ itself
```

## Folder Structure Integration

The Root folder is automatically maintained by the project cleanup script:
```bash
./Launchers/project_cleanup.sh
```

This ensures:
- Root folder is created if missing
- No files are incorrectly moved out of Root
- Directory structure is verified during cleanup

## Version

**Version:** 2.0.0  
**Last Updated:** 2026-02-07  
**Author:** SecIDS-CNN Team

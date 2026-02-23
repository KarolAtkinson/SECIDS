# VS Code Debug Integration Guide

**Date:** 2026-01-31  
**Status:** ✅ Configured and Ready

## Overview

Integrated the SecIDS-CNN cleanup and detection programs with VS Code's Run and Debug tools for:
- Real-time debugging with breakpoints
- Step-through code execution
- Variable inspection
- Performance profiling
- Issue identification and fault detection

## Configuration Files Created

### 1. `.vscode/launch.json` - Debug Configurations

Seven debug configurations available:

#### Cleanup Program Debuggers
- **Debug: Redundancy Detector** - Debug redundancy_detector.py
- **Debug: File Organizer** - Debug organize_files.py

#### UI and Detection Debuggers
- **Debug: Terminal UI** - Debug terminal_ui.py
- **Debug: DDoS Countermeasure** - Debug ddos_countermeasure.py

#### Generic Debuggers
- **Debug: Current File** - Debug any currently open Python file
- **Debug: Current File with Args** - Debug with command-line arguments
- **Python: Attach to Process** - Attach debugger to running process

### 2. `.vscode/tasks.json` - Build and Run Tasks

Eight tasks configured:

#### Run Tasks
- **Run: Redundancy Detector** - Execute redundancy detection
- **Run: File Organizer** - Execute file organization
- **Run: Project Cleanup Script** - Run full cleanup (default build)
- **Run: Terminal UI** - Launch SecIDS-CNN interface

#### Analysis Tasks
- **Analyze: Python Lint** - Check code quality
- **Test: Check Python Syntax** - Verify syntax validity

#### Maintenance Tasks
- **Install: Python Dependencies** - Install from requirements.txt
- **Check: Virtual Environment** - Verify Python & TensorFlow setup

### 3. `.vscode/settings.json` - Workspace Settings

Configured for optimal debugging:
- Python interpreter: `.venv_test/bin/python`
- Analysis paths for all project modules
- File exclusions for clean workspace
- Debug console settings
- Terminal environment variables

## How to Use - Debugging

### Method 1: Using Run and Debug Panel

1. **Open the Run and Debug Panel**
   - Press `Ctrl+Shift+D` (or `Cmd+Shift+D` on Mac)
   - Or click the "Run and Debug" icon in Activity Bar

2. **Select Configuration**
   - Choose from dropdown: "Debug: Redundancy Detector", "Debug: File Organizer", etc.

3. **Set Breakpoints**
   - Click left of line numbers to set breakpoints (red dots)
   - Or press `F9` on a line

4. **Start Debugging**
   - Press `F5` or click green "Start Debugging" button
   - Program will pause at breakpoints

5. **Debug Controls**
   - `F10` - Step Over (execute current line)
   - `F11` - Step Into (enter function)
   - `Shift+F11` - Step Out (exit function)
   - `F5` - Continue (run to next breakpoint)
   - `Shift+F5` - Stop debugging

### Method 2: Using Tasks

1. **Open Command Palette**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)

2. **Run Task**
   - Type "Tasks: Run Task"
   - Select task: "Run: Redundancy Detector", "Run: File Organizer", etc.

3. **Quick Build**
   - Press `Ctrl+Shift+B` - Runs default build task (Project Cleanup)

## Debugging Features Available

### Breakpoints
- **Line Breakpoints** - Pause at specific lines
- **Conditional Breakpoints** - Pause only when condition is true
  - Right-click breakpoint → Edit Breakpoint → Enter condition
- **Logpoints** - Log messages without stopping
  - Right-click line → Add Logpoint

### Variable Inspection

#### Debug Sidebar (when paused)
- **Variables** - View all local/global variables
- **Watch** - Monitor specific expressions
- **Call Stack** - See function call hierarchy

#### In Editor
- Hover over variables to see values
- Click to expand complex objects (dicts, lists, classes)

### Debug Console
- Execute Python code in current context
- Test expressions with current variable values
- Call functions interactively

### Exception Handling
- Automatically breaks on exceptions
- Shows full stack trace
- Inspect variables at exception point

## Debugging the Cleanup Programs

### Example 1: Debug Redundancy Detector

1. Open [Scripts/redundancy_detector.py](Scripts/redundancy_detector.py)
2. Set breakpoints at key locations:
   ```python
   # Line 84: When finding __pycache__
   pycache_path = Path(root) / "__pycache__"
   
   # Line 122: When calculating file hash
   file_hash = self.get_file_hash(file_path)
   
   # Line 172: When moving files
   shutil.move(str(file_path), str(trash_path))
   ```

3. Select "Debug: Redundancy Detector" from debug dropdown
4. Press `F5` to start
5. Inspect variables when paused:
   - `self.pycache_dirs` - List of found cache directories
   - `self.duplicates` - Dictionary of duplicate file groups
   - `file_hash` - Hash of current file

### Example 2: Debug File Organizer

1. Open [Scripts/organize_files.py](Scripts/organize_files.py)
2. Set breakpoints:
   ```python
   # Line 443: When detecting duplicates
   if len(paths) > 1:
   
   # Line 484: When moving redundant files
   shutil.move(str(file_path), str(trash_path))
   ```

3. Select "Debug: File Organizer"
4. Watch expressions:
   - `self.stats` - Current statistics
   - `file_hashes` - Hash dictionary
   - `paths` - Duplicate file paths

### Example 3: Debug Terminal UI

1. Open [UI/terminal_ui.py](UI/terminal_ui.py)
2. Set breakpoint at user input handling
3. Select "Debug: Terminal UI"
4. Step through menu selections
5. Inspect model loading and detection functions

## Identifying Issues and Faults

### Common Debug Scenarios

#### 1. File Not Found Errors
**Symptom:** FileNotFoundError or path issues

**Debug Strategy:**
```python
# Set breakpoint before file operation
# Inspect variables:
- file_path (is it correct?)
- Path.exists() (does file exist?)
- self.base_dir (is base directory correct?)
```

#### 2. Duplicate Detection Issues
**Symptom:** Files not detected as duplicates

**Debug Strategy:**
```python
# Breakpoint in get_file_hash()
# Check:
- file_hash value
- file_hashes dictionary
- Are hashes matching for duplicates?
```

#### 3. Performance Problems
**Symptom:** Script runs slowly

**Debug Strategy:**
- Use Logpoints to track progress
- Check loop iterations: `{len(items)} items processed`
- Inspect large data structures
- Look for nested loops

#### 4. Import/Path Errors
**Symptom:** ModuleNotFoundError

**Debug Strategy:**
```python
# Breakpoint at import
# Debug Console:
import sys
print(sys.path)  # Check if paths are correct
```

### Using Debug Console for Investigation

When paused at breakpoint:
```python
# Check file existence
Path('Reports').exists()

# List directory contents
list(Path('.').glob('*.py'))

# Test regex patterns
import re
re.match(r'.*_old.*', 'test_old.py')

# Calculate sizes
sum(f.stat().st_size for f in Path('.').rglob('*.pyc'))

# Test conditions
if condition_you_are_testing:
    print("Condition is True")
```

## Optimization with Debugging

### Performance Profiling

1. **Add timing checks:**
```python
import time
start = time.time()
# ... code to profile ...
print(f"Took {time.time() - start:.2f}s")
```

2. **Set logpoints at function entry/exit:**
- Entry: `Entering function with {len(items)} items`
- Exit: `Function complete, processed {count} items`

3. **Watch memory usage:**
```python
import sys
sys.getsizeof(large_object)
```

### Code Quality Checks

#### Run Syntax Check Task
1. Press `Ctrl+Shift+P`
2. Select "Tasks: Run Task"
3. Choose "Test: Check Python Syntax"
4. Verifies Python syntax without executing

#### Inspect Problem Panel
- Press `Ctrl+Shift+M` to open Problems panel
- Shows all errors/warnings in workspace
- Click to jump to issue location

## Quick Reference

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Start Debugging | `F5` |
| Stop Debugging | `Shift+F5` |
| Step Over | `F10` |
| Step Into | `F11` |
| Step Out | `Shift+F11` |
| Continue | `F5` |
| Toggle Breakpoint | `F9` |
| Run Task | `Ctrl+Shift+B` |
| Debug Panel | `Ctrl+Shift+D` |
| Problems Panel | `Ctrl+Shift+M` |

### Debug Configurations Quick Select

```
F5 → Select from dropdown:
├── Debug: Redundancy Detector (cleanup program)
├── Debug: File Organizer (organization program)
├── Debug: Terminal UI (main interface)
├── Debug: DDoS Countermeasure (security tool)
├── Debug: Current File (any open .py)
├── Debug: Current File with Args (with CLI args)
└── Python: Attach to Process (running process)
```

### Task Quick Launch

```
Ctrl+Shift+P → Tasks: Run Task → Select:
├── Run: Redundancy Detector
├── Run: File Organizer
├── Run: Project Cleanup Script (Ctrl+Shift+B)
├── Run: Terminal UI
├── Analyze: Python Lint
├── Test: Check Python Syntax
├── Install: Python Dependencies
└── Check: Virtual Environment
```

## Integration Benefits

### Before Debugging Setup
- ❌ Run scripts blindly, hope they work
- ❌ Add print() statements everywhere
- ❌ Restart script to test changes
- ❌ Unclear where errors occur

### After Debugging Setup
- ✅ Pause execution at any point
- ✅ Inspect all variables in real-time
- ✅ Step through code line by line
- ✅ Catch exceptions immediately with full context
- ✅ Test code snippets in Debug Console
- ✅ Profile performance bottlenecks
- ✅ Identify logic errors quickly
- ✅ Optimize code based on actual behavior

## Best Practices

1. **Set Strategic Breakpoints**
   - At function entry points
   - Before file operations
   - In loop conditions
   - Before/after external calls

2. **Use Conditional Breakpoints**
   - Only pause on specific conditions
   - Example: `file_size > 1000000` (only large files)

3. **Use Logpoints for High-Frequency Code**
   - Don't pause on every iteration
   - Log key values instead

4. **Inspect Complex Objects**
   - Expand dictionaries and lists in Variables panel
   - Use Debug Console for custom queries

5. **Keep Debug Console Open**
   - Test expressions without modifying code
   - Verify conditions quickly

## Troubleshooting

### Debugger Won't Start
**Solution:**
```bash
# Verify debugpy is installed
.venv_test/bin/pip list | grep debugpy

# Reinstall if needed
.venv_test/bin/pip install --upgrade debugpy
```

### Wrong Python Interpreter
**Solution:**
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose `.venv_test/bin/python`

### Breakpoints Not Hitting
**Solution:**
- Check file path is correct in launch.json
- Ensure `justMyCode` is set to `false`
- Verify code is actually executed

### Cannot Import Module
**Solution:**
- Check `PYTHONPATH` in settings.json
- Verify `python.analysis.extraPaths` includes module directories

## Next Steps

1. ✅ Install debugpy - Complete
2. ✅ Configure launch.json - Complete
3. ✅ Configure tasks.json - Complete
4. ✅ Update settings.json - Complete
5. ⏭️ Set breakpoints in cleanup programs
6. ⏭️ Run debug session to identify issues
7. ⏭️ Profile performance bottlenecks
8. ⏭️ Optimize based on findings

## Example Debug Session

### Finding Why Duplicates Aren't Detected

1. Open `Scripts/redundancy_detector.py`
2. Set breakpoint at line 122: `file_hash = self.get_file_hash(file_path)`
3. Press `F5`, select "Debug: Redundancy Detector"
4. When paused, check Debug Console:
   ```python
   # Check file path
   file_path
   
   # Check hash calculation
   file_hash
   
   # Check hash dictionary
   file_hashes
   
   # See if this file already has a hash entry
   file_hashes.get(file_hash)
   ```
5. Step through with `F10` to see logic flow
6. Identify issue: perhaps hash calculation fails for certain files
7. Fix code, restart debug session to verify

---

**Tools Available:**
- 7 Debug Configurations
- 8 Build/Run Tasks
- Full Python debugging with debugpy
- Real-time variable inspection
- Step-through execution
- Exception handling
- Performance profiling

**Ready to debug and optimize SecIDS-CNN programs!** 🐛🔍

---
*VS Code Debug Integration by SecIDS-CNN Development Team*

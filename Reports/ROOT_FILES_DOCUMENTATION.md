# Root Directory File Organization Policy

**Date:** January 31, 2026  
**Status:** ✅ Active Policy

---

## Overview

The SECIDS-CNN project maintains a clean root directory with **only essential files** that must be at the project root for proper system functionality. All other files are organized into category-specific folders.

---

## Critical Root Files (Protected from Cleanup)

### 1. Main Entry Points

#### `secids_main.py`
- **Purpose:** Unified CLI entry point for the entire system
- **Used By:** All launchers, quick start scripts, UI
- **Why Root:** Launchers expect it at root, simplifies imports
- **Commands:**
  ```bash
  python secids_main.py ui              # Launch UI
  python secids_main.py check           # System health check
  python secids_main.py detect file     # File detection
  python secids_main.py detect live     # Live detection
  ```

#### `system_integrator.py`
- **Purpose:** System integration layer linking all components
- **Used By:** Upgrade scripts, post-upgrade menu, health checks
- **Why Root:** Called by multiple scripts, needs central location
- **Functions:**
  - Component integration validation
  - System health monitoring
  - Cross-module communication

---

### 2. Python Configuration

#### `__init__.py`
- **Purpose:** Marks SECIDS-CNN as a Python package
- **Required By:** Python import system
- **Why Root:** Python requires this at package root
- **Impact:** Enables `from SecIDS-CNN import *` style imports
- **Cannot Be Moved:** Hard requirement of Python module system

#### `requirements.txt`
- **Purpose:** Python package dependencies
- **Used By:** pip, virtual environment setup, CI/CD
- **Why Root:** Industry standard location for dependencies
- **Commands:**
  ```bash
  pip install -r requirements.txt
  pip freeze > requirements.txt
  ```
- **Standard Practice:** Always at project root

#### `pyrightconfig.json`
- **Purpose:** Pyright/Pylance type checker configuration
- **Used By:** VS Code, Pylance, Pyright, IDEs
- **Why Root:** Type checkers look for config at project root
- **Benefits:**
  - IDE IntelliSense
  - Type error detection
  - Code completion
- **Cannot Be Moved:** Tool expects it at root

---

### 3. Documentation

#### `Master-Manual.md`
- **Purpose:** Complete system documentation and reference
- **Why Root:** Primary documentation should be easily accessible
- **Size:** 5,669 lines covering all aspects
- **Sections:** Setup, usage, architecture, troubleshooting

---

### 4. Version Control

#### `.gitignore`
- **Purpose:** Git ignore rules
- **Why Root:** Git requires this at repository root
- **Protected By:** Git, not cleanup script

---

## Files That Get Moved (Organizational Categories)

### Reports (→ `Reports/`)
- All `*_REPORT.md` files
- Analysis documents
- Test results documentation
- Change logs

**Examples:**
```
SYSTEM_UPGRADE_REPORT_20260131.md → Reports/
CLEANUP_MODULARIZATION_REPORT.md  → Reports/
FILE_ORGANIZATION_SYSTEM.md       → Reports/
```

---

### Scripts (→ `Scripts/`)
- Utility Python scripts
- Analysis tools
- Testing scripts
- Data processing scripts

**Examples:**
```
analyze_threat_origins.py  → Scripts/
verify_packages.py         → Scripts/
test_enhanced_model.py     → Scripts/
organize_files.py          → Scripts/
```

**Exceptions:** Main entry points stay in root (secids_main.py, system_integrator.py)

---

### Tools (→ `Tools/`)
- Reusable tool modules
- Command libraries
- Workflow managers
- Helper utilities

**Examples:**
```
command_library.py         → Tools/
csv_workflow_manager.py    → Tools/
pipeline_orchestrator.py   → Tools/
dataset_path_helper.py     → Tools/
```

---

### Configuration (→ `Config/`)
- JSON configuration files
- Settings files
- Command history
- Dataset configurations

**Examples:**
```
command_history.json       → Config/
command_shortcuts.json     → Config/
dataset_config.json        → Config/
command_favorites.json     → Config/
```

**Exceptions:** Root configs stay in root (pyrightconfig.json, requirements.txt)

---

### Models (→ `Models/`)
- Trained model files (`.h5`, `.pkl`)
- Model weights
- Saved models

**Examples:**
```
SecIDS-CNN.h5             → Models/
model_weights.pkl         → Models/
```

---

### Logs (→ `Logs/`)
- Application logs (`.log`)
- Debug output
- Runtime logs

**Examples:**
```
application.log           → Logs/
debug_20260131.log       → Logs/
```

---

### Captures (→ `Captures/`)
- Network packet captures (`.pcap`)
- Traffic recordings

**Examples:**
```
capture_1769451948.pcap   → Captures/
test_traffic.pcap         → Captures/
```

---

### Archives (→ `Archives/`)
- Historical CSV datasets
- Old training data
- Archived results

**Examples:**
```
cicids2017_cleaned.csv    → Archives/
old_training_data.csv     → Archives/
```

---

## Cleanup Script Behavior

### Whitelist Protection

The cleanup script (`Launchers/cleanup_modules/root_organization.sh`) maintains a whitelist:

```bash
whitelist=(
    "secids_main.py"
    "system_integrator.py"
    "__init__.py"
    "requirements.txt"
    "pyrightconfig.json"
    "Master-Manual.md"
    ".gitignore"
)
```

**Protection Logic:**
1. Check if file matches whitelist
2. If whitelisted: Skip, leave in root
3. If not whitelisted: Move to appropriate category folder

---

### Automatic Organization

When cleanup runs, it:

1. **Verifies whitelist** - Ensures critical files stay in root
2. **Categorizes loose files** - Identifies file types
3. **Moves to folders** - Places files in correct directories
4. **Reports results** - Shows what was organized

**Safe to Run:** Cleanup will never move critical files.

---

## Testing File Organization

### Verify Critical Files Protected

```bash
# Run cleanup
./Launchers/project_cleanup_modular.sh --task organize

# Verify files still in root
ls -lh *.py *.json *.txt *.md
```

**Expected Output:**
```
__init__.py
Master-Manual.md
pyrightconfig.json
requirements.txt
secids_main.py
system_integrator.py
```

---

### Check Files Were Moved

```bash
# Check Reports folder
ls Reports/*_REPORT.md

# Check Scripts folder
ls Scripts/*.py | head -5

# Check Config folder
ls Config/*.json
```

---

## Developer Guidelines

### Adding New Root Files

**Before adding a file to root, ask:**

1. ✅ Is it a main entry point?
2. ✅ Is it required by a tool (pip, git, IDE)?
3. ✅ Does Python require it at root?
4. ✅ Is it the primary documentation?

**If YES to any:** File can stay in root, add to whitelist
**If NO to all:** File should go in a category folder

---

### Updating Whitelist

To protect a new file from cleanup:

1. Edit `Launchers/cleanup_modules/root_organization.sh`
2. Add filename to whitelist array:
   ```bash
   whitelist=(
       "secids_main.py"
       "system_integrator.py"
       "__init__.py"
       "requirements.txt"
       "pyrightconfig.json"
       "Master-Manual.md"
       ".gitignore"
       "your_new_file.py"    # ← Add here
   )
   ```
3. Document why in comments
4. Update this documentation

---

### Creating New Categories

If files don't fit existing categories:

1. **Create folder:**
   ```bash
   mkdir NewCategory
   ```

2. **Add to cleanup script:**
   ```bash
   # In root_organization.sh, add:
   for file in *.newtype; do
       if [ -f "$file" ]; then
           mv "$file" NewCategory/ 2>/dev/null && organized_count=$((organized_count + 1))
       fi
   done
   ```

3. **Update directory structure in Master-Manual.md**

4. **Test cleanup:**
   ```bash
   ./Launchers/project_cleanup_modular.sh --task organize
   ```

---

## Common Questions

### Q: Why is `secids_main.py` in root and not in `Scripts/`?

**A:** It's the main entry point, not a utility script. Launchers expect it at root, and keeping it there:
- Simplifies launcher scripts
- Makes it easy to find
- Follows convention for main entry points
- Reduces import complexity

---

### Q: Can I move `requirements.txt` to `Config/`?

**A:** **No.** `pip install -r requirements.txt` is an industry-standard command that expects the file at project root. Moving it would:
- Break installation instructions
- Confuse new developers
- Violate Python conventions
- Require custom pip commands

---

### Q: Why not put all `.json` files in `Config/`?

**A:** Some JSON files have specific purposes:
- `pyrightconfig.json` - Must be at root for Pyright
- `command_*.json` - User configs, belong in Config/
- `dataset_config.json` - Application config, belongs in Config/

The cleanup script handles this automatically.

---

### Q: What if I accidentally move a critical file?

**A:** The system will break. To fix:

1. **Check symptoms:**
   ```bash
   python secids_main.py check  # Will fail with import errors
   ```

2. **Move file back to root:**
   ```bash
   # Example: if secids_main.py was moved to Scripts/
   mv Scripts/secids_main.py .
   ```

3. **Verify fix:**
   ```bash
   python secids_main.py check
   ```

---

### Q: How do I know if a file should be in root?

**Decision Tree:**

```
Is it called by launchers in Launchers/?
├─ YES → Check if it's a main entry point
│         ├─ YES → Root
│         └─ NO → Tools/
└─ NO → Check if it's a Python/IDE config
         ├─ YES → Root (if tool requires it)
         └─ NO → Appropriate category folder
```

---

## File Organization Summary

| Category | Location | Purpose | Auto-Moved |
|----------|----------|---------|------------|
| Main Entry Points | Root | Primary executables | No ✅ |
| Python Configs | Root | Python/IDE requirements | No ✅ |
| Documentation | Root | Master-Manual.md only | No ✅ |
| Reports | Reports/ | Analysis, change logs | Yes ✓ |
| Scripts | Scripts/ | Utility scripts | Yes ✓ |
| Tools | Tools/ | Reusable modules | Yes ✓ |
| Config | Config/ | App configurations | Yes ✓ |
| Models | Models/ | Trained models | Yes ✓ |
| Logs | Logs/ | Application logs | Yes ✓ |
| Captures | Captures/ | PCAP files | Yes ✓ |
| Archives | Archives/ | Historical datasets | Yes ✓ |

---

## Cleanup Commands

### Quick Cleanup
```bash
# Fast essential cleanup (5-10 seconds)
./Launchers/project_cleanup_modular.sh --quick
```

### Full Cleanup
```bash
# Complete organization (30-40 seconds)
./Launchers/project_cleanup_modular.sh
```

### Organize Files Only
```bash
# Just organize loose files (2-5 seconds)
./Launchers/project_cleanup_modular.sh --task organize
```

---

## Maintenance

This policy is maintained by the cleanup script and enforced automatically. The whitelist ensures critical files are never moved, even if cleanup runs multiple times.

**Last Updated:** January 31, 2026  
**Next Review:** When new root files are added  
**Policy Owner:** System Architecture Team

---

## Related Documentation

- [Master-Manual.md](../Master-Manual.md) - Complete system documentation
- [CLEANUP_MODULARIZATION_REPORT.md](CLEANUP_MODULARIZATION_REPORT.md) - Cleanup system details
- [FILE_ORGANIZATION_SYSTEM.md](FILE_ORGANIZATION_SYSTEM.md) - Organization guidelines
- [Launchers/cleanup_modules/root_organization.sh](../Launchers/cleanup_modules/root_organization.sh) - Implementation

---

**Status:** ✅ Policy Active - Enforced by Cleanup Script  
**Protection:** Automated via whitelist in cleanup modules  
**Violations:** None - Script prevents accidental moves

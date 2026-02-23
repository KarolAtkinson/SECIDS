# Redundancy Detection & Cleanup - Quick Reference

## Quick Commands

### Run Redundancy Detection
```bash
cd /home/kali/Documents/Code/SECIDS-CNN
.venv_test/bin/python Scripts/redundancy_detector.py
```

### Run File Organization (includes redundancy cleanup)
```bash
.venv_test/bin/python Scripts/organize_files.py
```

### Run Full Project Cleanup
```bash
bash Launchers/project_cleanup.sh
```

### Check What Was Moved to TrashDump
```bash
find TrashDump -type f | grep -v ".venv"
```

### Review TrashDump Contents Before Deletion
```bash
ls -lhR TrashDump/
```

### Empty TrashDump (CAUTION: Permanent deletion)
```bash
# Review first!
ls -R TrashDump/

# If satisfied, empty it
rm -rf TrashDump/*
```

## What Gets Detected

### 1. Python Cache Files
- `__pycache__/` directories
- `*.pyc` bytecode files
- `*.pyo` optimized bytecode
- **Action:** Removed immediately (auto-regenerated)

### 2. Duplicate Files
- Files with identical MD5 hash
- Compares all non-large files
- **Action:** Keeps first, moves duplicates to TrashDump/

### 3. Redundant Patterns
Files matching these patterns:
- `*_old.*` - Old versions
- `*_backup.*` - Backups
- `*.bak` - Backup extension
- `*_copy.*` - Copies
- `*~` - Editor backups
- `*.tmp`, `*.temp` - Temporary files
- **Action:** Moved to TrashDump/

## Excluded from Scanning

These directories are automatically excluded:
- `.venv_test/` - Testing virtual environment
- `.venv/` - Other virtual environments
- `__pycache__/` - Python cache (removed separately)
- `.git/` - Git repository
- `node_modules/` - Node.js packages
- `.pytest_cache/` - Test cache
- `TrashDump/` - Already trashed files

## File Types Excluded from Duplicate Detection

Large or data files not scanned for duplicates:
- `*.csv` - Dataset files (too large)
- `*.pcap` - Network captures (too large)
- `*.h5` - Model files (too large)
- `*.log` - Log files (expected duplicates)
- Files over 10MB

## Safety Features

1. **No Direct Deletion:** Files moved to TrashDump/ first
2. **Timestamped:** Each moved file gets unique timestamp
3. **Directory Structure Preserved:** TrashDump/ mirrors original structure
4. **Reports Generated:** Detailed log of all actions
5. **Original Kept:** Always keeps at least one copy of duplicates

## Integration

### With File Organization System
```python
# organize_files.py runs these automatically:
1. File organization (move to proper directories)
2. Python cache cleanup
3. .pyc file cleanup
4. Duplicate detection
5. Redundant pattern detection
```

### With Project Cleanup
```bash
# project_cleanup.sh step 3 now includes:
- Standard file organization
- Redundancy detection
- Cache cleanup
- Duplicate removal
```

## Maintenance Schedule

### Daily (if actively coding)
```bash
# Quick cache cleanup
find . -type d -name "__pycache__" -not -path "./.venv*" -exec rm -rf {} +
find . -name "*.pyc" -not -path "./.venv*" -delete
```

### Weekly
```bash
# Full redundancy scan
.venv_test/bin/python Scripts/redundancy_detector.py
```

### Monthly
```bash
# Review and empty TrashDump
ls -lhR TrashDump/
# After review:
rm -rf TrashDump/*
```

## Reports Location

All redundancy cleanup reports saved to:
```
Reports/REDUNDANCY_CLEANUP_REPORT_YYYYMMDD_HHMMSS.md
```

Contains:
- Summary of actions taken
- List of files moved
- Statistics by category
- Recommendations

## Troubleshooting

### "No such file or directory" error
**Cause:** Virtual environment not activated  
**Solution:**
```bash
cd /home/kali/Documents/Code/SECIDS-CNN
source .venv_test/bin/activate
python Scripts/redundancy_detector.py
```

### "Permission denied" error
**Cause:** Script not executable  
**Solution:**
```bash
chmod +x Scripts/redundancy_detector.py
chmod +x Scripts/organize_files.py
```

### Duplicate detection too aggressive
**Cause:** Files legitimately have same content  
**Solution:** Check TrashDump/ before emptying, restore if needed:
```bash
# Find file in TrashDump
find TrashDump -name "filename*"

# Restore to original location
mv TrashDump/path/to/file_TIMESTAMP.ext path/to/file.ext
```

### TrashDump growing too large
**Cause:** Not reviewing/emptying regularly  
**Solution:**
```bash
# Check size
du -sh TrashDump/

# Review old files (over 30 days)
find TrashDump -type f -mtime +30

# Remove old files after review
find TrashDump -type f -mtime +30 -delete
```

## Best Practices

1. ✅ **Always review TrashDump/** before permanent deletion
2. ✅ **Run redundancy checks weekly** to keep project clean
3. ✅ **Check reports** to understand what was removed
4. ✅ **Keep .gitignore updated** to prevent re-adding redundant files
5. ✅ **Test after cleanup** to ensure nothing broke
6. ❌ **Don't skip review** - automated detection can make mistakes
7. ❌ **Don't delete TrashDump immediately** - wait 24-48 hours

## Statistics Example

From typical run:
```
__pycache__ directories: 4 removed (saving ~236 KB)
.pyc files: 13 removed
Duplicate files: 3 found
Redundant files: 0 moved
Total moved to TrashDump: 3 files
```

## Advanced Usage

### Custom Duplicate Detection
```python
# Modify redundancy_detector.py
# Line ~80: Adjust size threshold
if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
    continue
```

### Add Custom Redundant Patterns
```python
# Modify redundancy_detector.py
# Line ~25: Add patterns
REDUNDANT_PATTERNS = [
    "*_old.*", "*_backup.*", "*.bak", "*_copy.*", "*~",
    "*.tmp", "*.temp", "*_test_old.*", "*_deprecated.*",
    "*_draft.*",  # Add your pattern
]
```

### Exclude Additional Directories
```python
# Modify redundancy_detector.py
# Line ~20: Add exclusions
EXCLUDE_DIRS = {
    ".venv_test", ".venv", "__pycache__", ".git",
    "Model_Tester/.venv", "SecIDS-CNN/.venv",
    "node_modules", ".pytest_cache", "TrashDump",
    "YourCustomDir",  # Add your exclusion
}
```

---

**Last Updated:** 2026-01-31  
**Version:** 1.0  
**Maintainer:** SecIDS-CNN Development Team

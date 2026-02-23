# MD_*.csv Naming Convention - Quick Reference

## Overview
All master datasets in SecIDS-CNN now follow the `MD_*.csv` naming convention for consistency and easy identification.

## Standard Format
```
MD_<identifier>.csv
```

## Examples

### Primary Dataset
```
MD_1.csv              Primary master dataset (formerly master_dataset_20260129.csv)
```

### Additional Datasets
```
MD_2.csv              Secondary or updated dataset
MD_3.csv              Third version
MD_enhanced.csv       Enhanced/processed version
MD_20260129.csv       Timestamped version (YYYYMMDD)
MD_filtered.csv       Filtered dataset
MD_combined.csv       Combined from multiple sources
```

## Special Cases

### Test Files (Preserved Names)
```
Test1.csv             Testing dataset 1
Test2.csv             Testing dataset 2
```

### Temporary/Working Files
```
temp_*.csv            Temporary processing files
converted_*.csv       PCAP conversion output (before moving to MD_*)
```

## Directory Structure
```
SecIDS-CNN/
├── datasets/
│   ├── MD_1.csv          ← Primary master dataset
│   ├── MD_2.csv          ← Additional datasets
│   ├── Test1.csv         ← Test files
│   └── Test2.csv
├── Results/
│   ├── detection_results_*.csv
│   ├── threat_report_*.md
│   └── threat_report_*.json
└── Archives/
    └── (historical training data)
```

## Tools Using MD_*.csv

### 1. csv_workflow_manager.py
**Creates:** `MD_*.csv` files from training results
```python
dest = self.secids_datasets_dir / f"MD_{timestamp}.csv"
```

### 2. dataset_path_helper.py  
**Searches:** For `MD_*.csv` files automatically
```python
master_files = list(datasets_dir.glob('MD_*.csv'))
```

### 3. terminal_ui.py
**References:** `MD_1.csv` as master dataset
```python
self.analyze_csv("SecIDS-CNN/datasets/MD_1.csv")
```

### 4. Master-Manual.md
**Documents:** `MD_1.csv` as active dataset
```markdown
Active Dataset: MD_1.csv (90,105 rows)
```

## Workflow

### Creating New Master Dataset

1. **From Training Results:**
   ```bash
   # csv_workflow_manager automatically creates MD_*.csv
   python3 Tools/csv_workflow_manager.py
   ```

2. **From PCAP Conversion:**
   ```bash
   # Convert PCAP to CSV
   python3 Tools/pcap_to_secids_csv.py -i capture.pcap -o converted_data.csv
   
   # Manually rename to MD_* format
   mv converted_data.csv SecIDS-CNN/datasets/MD_2.csv
   ```

3. **From Enhanced Dataset:**
   ```bash
   # Enhance dataset
   python3 Tools/create_enhanced_dataset.py input.pcap MD_enhanced.csv
   
   # Move to datasets directory
   mv MD_enhanced.csv SecIDS-CNN/datasets/
   ```

### Using Master Datasets

#### Via Terminal UI
```bash
bash Launchers/secids-ui
# Menu 3 → Option 4: Analyze Master Dataset (MD_1.csv)
```

#### Via Command Line
```bash
# Activate virtual environment
source .venv_test/bin/activate

# Run threat detection
python3 SecIDS-CNN/run_model.py file SecIDS-CNN/datasets/MD_1.csv
```

#### Batch Analysis
```bash
# Analyze all MD_*.csv files
python3 SecIDS-CNN/run_model.py file SecIDS-CNN/datasets/MD_*.csv
```

## File Management

### Listing Master Datasets
```bash
ls -lh SecIDS-CNN/datasets/MD_*.csv
```

### Checking Dataset Info
```bash
# Count rows
wc -l SecIDS-CNN/datasets/MD_1.csv

# View first few lines
head SecIDS-CNN/datasets/MD_1.csv

# Get file size
du -h SecIDS-CNN/datasets/MD_1.csv
```

### Organizing Files
```bash
# Auto-organize all files (moves CSVs to correct locations)
bash Launchers/project_cleanup.sh
```

## Naming Guidelines

### ✅ DO
- Use `MD_` prefix for all master datasets
- Use descriptive identifiers: `MD_enhanced`, `MD_filtered`
- Use timestamps when needed: `MD_20260129`
- Keep Test1.csv and Test2.csv for testing

### ❌ DON'T
- Don't use `master_dataset_*.csv` (old convention)
- Don't use `improved_dataset_*.csv` (old convention)
- Don't use spaces in filenames
- Don't use special characters except underscore

## Migration from Old Names

If you have old-style dataset names:
```bash
# Rename old master datasets
mv master_dataset_20260129.csv MD_1.csv
mv improved_dataset_20260128.csv MD_2.csv
mv enhanced_dataset_final.csv MD_enhanced.csv
```

## Verification

### Check Naming Convention
```bash
# Run test suite to verify all files follow convention
python3 Tools/final_test_suite.py
```

### Check Tool Compatibility
```bash
# Verify tools recognize MD_*.csv files
python3 Tools/dataset_path_helper.py
```

## Quick Commands

```bash
# Create new master dataset from multiple CSVs
python3 Tools/create_comprehensive_dataset.py

# List all master datasets with details
ls -lh SecIDS-CNN/datasets/MD_*.csv

# Count total master datasets
ls SecIDS-CNN/datasets/MD_*.csv | wc -l

# Get combined size of all master datasets
du -ch SecIDS-CNN/datasets/MD_*.csv | tail -1

# Find most recent master dataset
ls -t SecIDS-CNN/datasets/MD_*.csv | head -1

# Run detection on specific dataset
source .venv_test/bin/activate
python3 SecIDS-CNN/run_model.py file SecIDS-CNN/datasets/MD_1.csv
```

## Current Dataset Status

**Primary Dataset:** MD_1.csv  
**Location:** `/home/kali/Documents/Code/SECIDS-CNN/SecIDS-CNN/datasets/MD_1.csv`  
**Rows:** 90,105  
**Columns:** 13  
**Size:** 8.94 MB  
**Threats:** 22.4% attack traffic  

## Related Documentation

- [Master-Manual.md](../Master-Manual.md) - Section 5.4 Dataset Management
- [FRONTEND_TESTING_REPORT.md](FRONTEND_TESTING_REPORT.md) - Complete test results
- [README.md](README.md) - System overview

---

**Last Updated:** January 29, 2026  
**Convention Version:** 1.0  
**Status:** ✅ Implemented and tested

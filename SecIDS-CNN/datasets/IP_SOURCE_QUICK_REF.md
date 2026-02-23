# ip_source Field - Quick Reference Card

## Overview
The `ip_source` field has been added to all SecIDS-CNN datasets to enable IP-based threat tracking and analysis.

## Field Specifications
- **Column Number:** 14 (last column)
- **Data Type:** String (IPv4 address)
- **Format:** xxx.xxx.xxx.xxx
- **Purpose:** Track source IP addresses for threat analysis

## Dataset Changes
**Before:** 13 columns, 8.94 MB  
**After:** 14 columns, 10.06 MB  
**Change:** +1 column (ip_source), +1.12 MB

## Quick Commands

### View Column Structure
```bash
head -1 SecIDS-CNN/datasets/MD_1.csv | tr ',' '\n' | nl
```

### Check Dataset with IP Sources
```bash
head -3 SecIDS-CNN/datasets/MD_1.csv
```

### Run Detection Test
```bash
source .venv_test/bin/activate
python3 SecIDS-CNN/run_model.py file MD_1.csv
```

### Create New Dataset with IP Sources
```bash
python3 Tools/add_ip_source.py input.csv output.csv
```

### Analyze IP Patterns in Results
```bash
# Count unique IPs
cut -d',' -f14 Results/detection_results_*.csv | sort | uniq | wc -l

# Find top attack source IPs
grep "Attack" Results/detection_results_*.csv | cut -d',' -f14 | sort | uniq -c | sort -rn | head -10
```

## IP Generation Rules

### Benign Traffic
- **Range:** 192.168.1.10-100
- **Pattern:** Internal network IPs
- **Reason:** Normal traffic from known sources

### Attack Traffic  
- **Range:** 192.168.0-255.1-254
- **Pattern:** Varied source IPs
- **Reason:** Simulates distributed attacks

## Tool Integration

### add_ip_source.py
Adds ip_source to existing datasets or creates new ones
```bash
python3 Tools/add_ip_source.py <input> [output]
```

### pcap_to_secids_csv.py
Now automatically extracts and includes source IPs from packets
```bash
python3 Tools/pcap_to_secids_csv.py -i capture.pcap -o output.csv
```

## Whitelist/Blacklist Integration
- Automatically checks IPs against Device_Profile/whitelists/
- Automatically checks IPs against Device_Profile/Blacklist/
- Reports statistics during dataset creation

## Model Compatibility
✅ Backward compatible with 13-column datasets  
✅ Forward compatible with 14-column datasets  
✅ Automatically drops string columns for prediction  
✅ No retraining required

## Available Datasets
- **MD_1.csv** - Primary (14 cols, 90,105 rows, 10.06 MB)
- **MD_20260129_145407.csv** - New (14 cols, 90,105 rows, 10.06 MB)
- **MD_1_backup.csv** - Original backup (13 cols)

## Detection Results
All results now include the ip_source field:
```csv
...is_ddos,Label,source_file,ip_source,prediction,probability
...1,Benign,dataset.csv,192.168.1.34,Attack,0.9255932569503784
```

## Documentation
📖 Reports/IP_SOURCE_ENHANCEMENT_REPORT.md - Complete details  
📖 Master-Manual.md Section 5.4 - Updated dataset info  
📖 Tools/add_ip_source.py - Enhancement tool documentation

## Status: ✅ Production Ready
- ip_source field added to all datasets
- Detection tested: 19,111 records/sec
- Whitelist/blacklist integration complete
- All tools updated and working

---
*Last Updated: January 29, 2026*  
*Enhancement Version: 2.0*

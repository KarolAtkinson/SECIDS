# Auto-Update & Blacklist System Documentation
**Date:** January 28, 2026  
**System:** SECIDS-CNN Autonomous Management

---

## Overview

Implemented two critical systems for autonomous operation and threat intelligence:

1. **Auto-Update System**: Background monitoring and automatic task execution
2. **Blacklist System**: Persistent threat tracking and intelligence gathering

---

## 1. Auto-Update System

### Purpose
Monitors system health and automatically triggers maintenance tasks when thresholds are exceeded.

### Location
`Auto_Update/`

### Components

#### A. Task Scheduler (`Auto_Update/task_scheduler.py`)
**Autonomous task management and execution**

**Features:**
- Configurable task intervals (hours)
- Automatic sub-routine triggering
- Task success/failure tracking
- Daemon mode for continuous operation
- Emergency cleanup triggers

**Managed Tasks:**
```python
{
  'dataset_cleanup': {
    'interval': 24 hours,
    'script': 'Launchers/project_cleanup.sh'
  },
  'whitelist_update': {
    'interval': 168 hours (weekly),
    'script': 'Device_Profile/device_info/capture_device_info.py'
  },
  'dataset_refinement': {
    'interval': 72 hours (3 days),
    'script': 'Scripts/refine_datasets.py'
  },
  'model_validation': {
    'interval': 48 hours,
    'script': 'Scripts/test_enhanced_model.py'
  },
  'blacklist_cleanup': {
    'interval': 168 hours (weekly)
  }
}
```

**Usage:**
```bash
# Show task status
python3 Auto_Update/task_scheduler.py --status

# Run specific task
python3 Auto_Update/task_scheduler.py --run dataset_cleanup

# Run as background daemon (checks every hour)
python3 Auto_Update/task_scheduler.py --daemon

# Custom check interval (seconds)
python3 Auto_Update/task_scheduler.py --daemon --interval 1800
```

**Configuration:**
- File: `Auto_Update/schedulers/task_config.json`
- Auto-created on first run
- Customizable intervals and thresholds

#### B. System Monitor (`Auto_Update/monitors/system_monitor.py`)
**Real-time system health monitoring**

**Monitors:**
- **Disk Space**: Total, used, free, percentage
- **Datasets**: CSV count, refined count, total size
- **Captures**: PCAP files, size
- **Blacklist**: Threat profile count
- **TrashDump**: File count, size

**Thresholds:**
- Disk space > 80% → Trigger cleanup
- Raw datasets > 10 → Trigger refinement
- Result files > 20 → Trigger cleanup
- PCAP files > 5 → Trigger processing
- Threat profiles > 1000 → Trigger cleanup
- TrashDump > 100MB → Trigger empty

**Usage:**
```bash
# Check system status
python3 Auto_Update/monitors/system_monitor.py

# Status saved to: Auto_Update/monitors/system_status.json
```

**Sample Output:**
```
============================================================
SYSTEM STATUS REPORT
============================================================
Timestamp: 2026-01-28T17:29:00

Disk Space:
  Total: 154.36 GB
  Used: 29.13 GB (19.7%)
  Free: 118.65 GB

Datasets:
  Total CSV files: 10
  Refined datasets: 8
  Raw datasets: 1
  Total size: 4.28 MB

Packet Captures:
  PCAP files: 6
  Total size: 596.48 MB
  ⚠️  Action needed: Process captures

Blacklist:
  Threat profiles: 1

RECOMMENDED ACTIONS:
  • capture_processing
============================================================
```

---

## 2. Blacklist System

### Purpose
Permanently tracks confirmed threats not in whitelist. Stores comprehensive intelligence on attack sources for continuous improvement.

### Location
`Device_Profile/Blacklist/`

### Structure
```
Device_Profile/Blacklist/
├── threat_profiles/       # Individual threat JSON files
│   └── threat_<id>.json
├── blocked_ips/          # Blocked IP database
│   └── blocked_ips.json
└── attack_patterns/      # Pattern database
    └── patterns.json
```

### Components

#### A. Blacklist Manager (`Device_Profile/device_info/blacklist_manager.py`)
**Comprehensive threat intelligence system**

**Features:**
- Automatic threat profiling
- Unique threat ID generation (MD5-based)
- Severity calculation (CRITICAL/HIGH/MEDIUM/LOW)
- Occurrence tracking
- IP blocking status
- Attack pattern recognition
- Persistent storage (JSON)

**Threat Profile Structure:**
```json
{
  "threat_id": "0be1f43dc668",
  "timestamp": "2026-01-28T17:29:00.123456",
  "src_ip": "10.0.0.100",
  "dst_ip": "192.168.112.143",
  "dst_port": 80,
  "protocol": "TCP",
  "threat_probability": 0.95,
  "flow_packets": 1500,
  "flow_bytes": 500000,
  "attack_type": "DDoS",
  "severity": "CRITICAL",
  "additional_info": {},
  "first_seen": "2026-01-28T17:29:00",
  "last_seen": "2026-01-28T17:29:00",
  "occurrence_count": 1
}
```

**Severity Calculation:**
```python
Score = (probability * 40) + (packet_score * 30) + (bytes_score * 30)

CRITICAL: score >= 80
HIGH:     score >= 60
MEDIUM:   score >= 40
LOW:      score < 40
```

**API Methods:**
```python
# Add threat
threat_id = manager.add_threat(threat_data)

# Check if IP is blacklisted
is_blocked = manager.is_blacklisted('10.0.0.100')

# Get threat profile
profile = manager.get_threat_profile(threat_id)

# Get all threats from IP
threats = manager.get_ip_threats('10.0.0.100')

# Get statistics
stats = manager.get_statistics()

# Unblock IP
manager.unblock_ip('10.0.0.100')

# Export blacklist
manager.export_blacklist('blacklist_export.json')
```

**Statistics:**
```python
{
  'blocked_ips': 1,
  'total_threats': 1,
  'attack_patterns': 1,
  'severity_breakdown': {
    'CRITICAL': 1,
    'HIGH': 0,
    'MEDIUM': 0,
    'LOW': 0
  }
}
```

---

## Integration with Live Capture

### New Command-Line Options
```bash
--enable-blacklist    Enable blacklist tracking (remember threats)
```

### Workflow
1. **Threat Detection**: Model identifies threat
2. **Whitelist Check**: Verify not legitimate traffic
3. **Blacklist Add**: Store threat intelligence
4. **Countermeasure**: Apply blocking if enabled

### Usage Example
```bash
# Full protection with whitelist and blacklist
sudo python3 Tools/continuous_live_capture.py \
  --iface eth0 \
  --enable-whitelist \
  --enable-blacklist \
  --enable-countermeasure \
  --auto-block
```

### Live Capture Output (Enhanced)
```
[17:06:42] Window #1: 22 flows | Threats: 7 | Total: 22 flows

  ✓ Filtered 5 false positive(s) via whitelist

  ⚠️  THREAT ALERT - 2 confirmed malicious flows!
     Port:   443 | Packets:  26 | Bytes:   53730 | Threat Level: 100.0%
       → Blacklisted: 0be1f43dc668
     Port: 40590 | Packets:  46 | Bytes:    9172 | Threat Level:  99.9%
       → Blacklisted: 3a7c89d2f154

Blacklist Statistics:
  Blocked IPs: 2
  Total threats tracked: 2
  Attack patterns recorded: 2
  Severity breakdown: {'CRITICAL': 2, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
```

---

## Autonomous Operation

### How It Works

**1. Continuous Monitoring**
```bash
# Start scheduler daemon (runs in background)
python3 Auto_Update/task_scheduler.py --daemon --interval 3600 &
```

**2. Automatic Checks (Every Hour)**
- System monitor scans disk, datasets, captures, blacklist
- Identifies actions needed
- Triggers appropriate tasks

**3. Task Execution**
- Dataset cleanup runs every 24 hours
- Whitelist update runs weekly
- Dataset refinement runs every 3 days
- Model validation runs every 2 days
- Blacklist cleanup runs weekly

**4. Emergency Triggers**
- Disk space > 80% → Immediate cleanup
- CSV files > 50 → Immediate organization
- PCAP files > 5 → Process captures

### Setting Up Autonomous Mode

**Option 1: Manual Daemon**
```bash
cd /home/kali/Documents/Code/SECIDS-CNN
nohup python3 Auto_Update/task_scheduler.py --daemon &
```

**Option 2: System Service (Recommended)**
```bash
# Create systemd service
sudo nano /etc/systemd/system/secids-autoupdate.service

[Unit]
Description=SECIDS-CNN Auto-Update Daemon
After=network.target

[Service]
Type=simple
User=kali
WorkingDirectory=/home/kali/Documents/Code/SECIDS-CNN
ExecStart=/usr/bin/python3 /home/kali/Documents/Code/SECIDS-CNN/Auto_Update/task_scheduler.py --daemon
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable secids-autoupdate
sudo systemctl start secids-autoupdate
```

---

## Blacklist Intelligence

### Data Retention
- **Threat Profiles**: 90 days (configurable)
- **Blocked IPs**: Permanent (manual unblock required)
- **Attack Patterns**: Last 1000 patterns

### Automatic Cleanup
- Runs weekly via task scheduler
- Removes profiles older than 90 days
- Keeps blocked IP list intact

### Export & Backup
```bash
# Export blacklist for analysis
python3 -c "
from Device_Profile.device_info.blacklist_manager import BlacklistManager
manager = BlacklistManager()
manager.export_blacklist('blacklist_backup.json')
"
```

---

## Configuration Files

### Task Configuration
**File:** `Auto_Update/schedulers/task_config.json`
```json
{
  "tasks": {
    "dataset_cleanup": {
      "enabled": true,
      "interval_hours": 24,
      "script": "Launchers/project_cleanup.sh"
    }
  },
  "thresholds": {
    "max_csv_files": 50,
    "max_refined_age_days": 30,
    "max_blacklist_age_days": 90
  }
}
```

### System Status
**File:** `Auto_Update/monitors/system_status.json`
- Updated by system monitor
- Contains latest system health snapshot
- Used by scheduler for decision making

---

## Benefits

### Auto-Update System:
✅ **Autonomous**: Runs without manual intervention  
✅ **Preventive**: Triggers cleanup before problems occur  
✅ **Efficient**: Scheduled tasks during low-usage periods  
✅ **Reliable**: Daemon mode with automatic restarts  
✅ **Customizable**: Configurable intervals and thresholds  

### Blacklist System:
✅ **Persistent Memory**: Never forgets a threat  
✅ **Intelligence Gathering**: Tracks attack patterns  
✅ **Severity Scoring**: Prioritizes critical threats  
✅ **Historical Data**: Builds threat database over time  
✅ **Export Capability**: Share intelligence with other systems  

---

## File Locations

```
Auto_Update/
├── task_scheduler.py           # Main scheduler
├── monitors/
│   ├── system_monitor.py       # System health monitoring
│   └── system_status.json      # Latest status
├── schedulers/
│   └── task_config.json        # Task configuration
└── logs/
    └── scheduler_YYYYMMDD.log  # Daily logs

Device_Profile/Blacklist/
├── threat_profiles/
│   └── threat_*.json           # Individual threats
├── blocked_ips/
│   └── blocked_ips.json        # Blocked IP database
└── attack_patterns/
    └── patterns.json           # Attack patterns
```

---

## Testing

### Test Blacklist Manager
```bash
python3 Device_Profile/device_info/blacklist_manager.py
```

### Test System Monitor
```bash
python3 Auto_Update/monitors/system_monitor.py
```

### Test Task Scheduler
```bash
# Check status
python3 Auto_Update/task_scheduler.py --status

# Run test task
python3 Auto_Update/task_scheduler.py --run dataset_cleanup
```

### Test Live Capture with All Systems
```bash
sudo python3 Tools/continuous_live_capture.py \
  --iface eth0 \
  --enable-whitelist \
  --enable-blacklist \
  --enable-countermeasure
```

---

## Future Enhancements

### Auto-Update:
- Web dashboard for monitoring
- Email/SMS alerts for critical issues
- Automatic model retraining triggers
- Cloud backup integration

### Blacklist:
- Geo-IP enrichment
- Threat intel feed integration
- Shared blacklist across multiple instances
- Machine learning for pattern recognition
- Automatic IOC (Indicators of Compromise) export

---

**System Status:** ✅ Fully Operational  
**Last Updated:** January 28, 2026  
**Maintainer:** SECIDS-CNN Development Team

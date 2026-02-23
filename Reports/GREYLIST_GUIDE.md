# SecIDS-CNN Greylist System - Complete Guide

## Overview

The greylist system adds intelligent threat classification to SecIDS-CNN, providing a middle ground between automatic blocking (blacklist) and automatic allowing (whitelist). This enables human-in-the-loop decision-making for ambiguous threats.

---

## What is the Greylist?

The **greylist** is a holding area for **potential threats** that fall between definite attacks and benign traffic. Instead of automatically blocking these IPs, the system alerts you and requests a decision.

### Threat Classification

All detected threats are classified into three categories based on ML model confidence:

| List | Probability Range | Action | Rationale |
|------|------------------|--------|-----------|
| **Whitelist** | < 50% | Trust (no action) | Low confidence - likely false positive |
| **Greylist** | 50% - 75% | Alert user for decision | Moderate confidence - requires verification |
| **Blacklist** | > 75% | Auto-block immediately | High confidence - definite threat |

---

## How It Works

### Automatic Classification

When a threat is detected:

1. **Model predicts** threat probability (0.0 - 1.0)
2. **Greylist manager classifies** based on thresholds:
   - `probability < 0.5` → Whitelist candidate (benign)
   - `0.5 ≤ probability ≤ 0.75` → **Greylist** (user decision required)
   - `probability > 0.75` → Blacklist (auto-block)

3. **Actions taken:**
   - **Whitelist**: No countermeasures, traffic allowed
   - **Greylist**: Alert generated, countermeasures suspended, user prompted
   - **Blacklist**: Immediate IP blocking via iptables

### User Decision Process

For greylisted threats:

```
🚨 GREYLIST ALERT - USER DECISION REQUIRED
───────────────────────────────────────────
  Potential threat detected from: 192.168.1.100
  Threat probability: 62.3%
  Destination port: 80
  Flow packets: 142
  Flow bytes: 8,524
  
  ⚠️  This IP has been seen 3 times
  First seen: 2026-02-03T14:30:22
  Last seen: 2026-02-03T14:35:18
  
  What action should be taken?
    [1] Move to BLACKLIST and deploy countermeasures (block IP)
    [2] Move to WHITELIST (trust this IP)
    [3] Keep on GREYLIST (continue monitoring)
    [4] Skip this decision (will be asked again)
  
  Enter choice [1-4]: _
```

### Decision Outcomes

**Option 1: Move to Blacklist**
- IP removed from greylist
- Added to permanent blacklist
- Countermeasures deployed immediately
- Logged with reason

**Option 2: Move to Whitelist**
- IP removed from greylist
- Added to permanent whitelist
- Future threats from this IP ignored
- Logged with reason

**Option 3: Keep on Greylist**
- IP stays on greylist
- Continue monitoring
- Will be asked again on next detection
- Logged with reason

**Option 4: Skip Decision**
- Decision postponed
- IP stays on greylist
- Will be asked again immediately next time

---

## File Structure

### New Files Created

```
Device_Profile/
├── greylist_manager.py          # Core greylist management
├── list_manager.py               # Unified list management
└── greylist/                     # Greylist data directory
    ├── greylist.json            # Current greylist
    ├── greylist_history.json    # Decision history
    └── greylist_report_*.json   # Periodic reports
```

### Integration Files Modified

```
integrated_workflow.py            # Main workflow (greylist integration)
Countermeasures/ddos_countermeasure.py  # Respects greylist
```

---

## Usage

### Running with Greylist (Automatic)

The greylist is automatically enabled in the integrated workflow:

```bash
# Standard workflow with greylist
sudo python3 integrated_workflow.py --mode full --interface eth0 --duration 60

# Continuous monitoring with greylist
sudo python3 integrated_workflow.py --mode continuous --interface eth0
```

### Manual Greylist Management

**Test greylist system:**
```bash
cd Device_Profile
python3 greylist_manager.py
```

**Manage lists manually:**
```bash
cd Device_Profile
python3 list_manager.py
```

---

## Configuration

### Adjusting Thresholds

Edit `Device_Profile/greylist_manager.py`:

```python
class GreylistManager:
    # Threat probability thresholds
    WHITELIST_THRESHOLD = 0.5      # Below this = benign
    GREYLIST_LOW = 0.5             # Greylist range start
    GREYLIST_HIGH = 0.75           # Greylist range end
    BLACKLIST_THRESHOLD = 0.75     # Above this = threat
```

**Example Adjustments:**

**More Aggressive (block more):**
```python
WHITELIST_THRESHOLD = 0.4      # Lower whitelist bar
GREYLIST_LOW = 0.4
GREYLIST_HIGH = 0.65           # Lower blacklist bar
BLACKLIST_THRESHOLD = 0.65
```

**More Conservative (ask user more often):**
```python
WHITELIST_THRESHOLD = 0.6      # Higher whitelist bar
GREYLIST_LOW = 0.6
GREYLIST_HIGH = 0.85           # Higher blacklist bar
BLACKLIST_THRESHOLD = 0.85
```

### Auto-Expiry Settings

Old greylist entries auto-expire after 24 hours by default.

Edit `Device_Profile/greylist_manager.py`:

```python
def cleanup_expired(self, max_age_hours: int = 24):  # Change this value
```

---

## Workflow Integration

### Detection Flow with Greylist

```
┌────────────────────┐
│  Packet Capture    │
└──────────┬─────────┘
           │
┌──────────▼─────────┐
│ Threat Detection   │
│  (ML Prediction)   │
└──────────┬─────────┘
           │
           │ Probability calculated
           ▼
┌──────────────────────────────────────┐
│      Greylist Classification         │
│                                      │
│  < 50%     │  50-75%    │  > 75%   │
│ Whitelist  │  Greylist  │ Blacklist│
└────┬───────┴─────┬──────┴────┬─────┘
     │             │            │
     ▼             ▼            ▼
  Allow    ┌──────────────┐  Block
           │ User Decision│  Immediately
           └──────┬───────┘
                  │
         ┌────────┼────────┐
         ▼        ▼        ▼
    Blacklist  Greylist  Whitelist
     (Block)   (Monitor) (Allow)
```

### Integration Points

1. **Integrated Workflow** (`integrated_workflow.py`)
   - Lines 95-105: Greylist manager initialization
   - Lines 300-330: Threat classification
   - Lines 370-400: Decision processing

2. **Countermeasures** (`ddos_countermeasure.py`)
   - Lines 40-50: List manager integration
   - Lines 235-250: Whitelist/greylist checks

3. **List Manager** (`list_manager.py`)
   - Unified whitelist/blacklist/greylist management
   - Automatic transitions between lists
   - Persistent storage

---

## Monitoring & Statistics

### Real-Time Status

During workflow execution:

```
================================================================================
  SYSTEM STATUS
================================================================================
  Packets Captured: 15,342
  Flows Analyzed: 1,234
  Threats Detected: 12
    ├─ Auto-blocked (Blacklist): 8
    ├─ Pending Decision (Greylist): 3
    └─ False Positives (Whitelist): 1
  Countermeasures Deployed: 8
  Greylist Status:
    ├─ Current size: 3
    ├─ Pending decisions: 2
    ├─ Moved to blacklist: 5
    ├─ Moved to whitelist: 2
    └─ Kept monitoring: 1
================================================================================
```

### Greylist Statistics

At workflow end:

```
================================================================================
  GREYLIST STATISTICS
================================================================================
  Current greylist size: 3
  Pending decisions: 0
  Total alerts: 15
  Moved to blacklist: 8
  Moved to whitelist: 3
  Kept on greylist: 4
  Auto-expired: 2
  Total decisions: 15
================================================================================
```

### Reports

**Greylist Report** (automatically generated):
```
Device_Profile/greylist/greylist_report_20260203_143022.json
```

Contains:
- Current greylist entries
- Decision history (last 50)
- Statistics summary
- Timestamps and metadata

**Lists Report** (manually generated):
```bash
cd Device_Profile
python3 list_manager.py
```

Exports: `Device_Profile/lists_report_*.json`

---

## List Files

### Greylist File (`greylist/greylist.json`)

```json
{
  "192.168.1.100": {
    "ip": "192.168.1.100",
    "first_seen": "2026-02-03T14:30:22",
    "last_seen": "2026-02-03T14:35:18",
    "occurrences": 3,
    "threat_data": [
      {
        "probability": 0.623,
        "dst_port": 80,
        "flow_packets": 142,
        "flow_bytes": 8524
      }
    ],
    "status": "pending_decision"
  }
}
```

### Whitelist File (`whitelists/ip_whitelist.json`)

```json
{
  "192.168.1.1": {
    "added": "2026-02-03T14:30:22",
    "reason": "Router - verified safe",
    "metadata": {
      "previous_status": "greylist",
      "moved_at": "2026-02-03T14:35:00"
    }
  }
}
```

### Blacklist File (`Blacklist/ip_blacklist.json`)

```json
{
  "10.0.0.50": {
    "added": "2026-02-03T14:32:15",
    "reason": "User confirmed threat from greylist",
    "metadata": {
      "previous_status": "greylist",
      "moved_at": "2026-02-03T14:32:15",
      "greylist_data": {
        "occurrences": 5,
        "threat_data": [...]
      }
    }
  }
}
```

---

## Common Scenarios

### Scenario 1: Legitimate Service Triggering Greylist

**Problem:** Your web server IP keeps appearing in greylist

**Solution:**
1. When prompted, choose option `[2]` to whitelist
2. Or manually add to whitelist:
   ```bash
   cd Device_Profile
   python3 -c "from list_manager import ListManager; m = ListManager(); m.add_to_whitelist('192.168.1.100', 'Web server')"
   ```

### Scenario 2: Suspicious But Unsure

**Problem:** IP showing moderate threat probability but you're not sure

**Solution:**
1. Choose option `[3]` to keep on greylist
2. Continue monitoring
3. If threat persists or increases → move to blacklist
4. If threat was false alarm → move to whitelist

### Scenario 3: Known Attacker

**Problem:** You recognize the IP as a known threat source

**Solution:**
1. Choose option `[1]` to blacklist immediately
2. Countermeasures deploy automatically
3. IP permanently blocked

### Scenario 4: Bulk Decision Making

**Problem:** Many greylist alerts during high traffic

**Solution:**
- Decisions are queued and processed sequentially
- Can choose option `[4]` to skip and come back later
- Review greylist report after traffic subsides
- Manually process decisions from report

---

## Troubleshooting

### Issue: Too Many Greylist Alerts

**Cause:** Greylist range too wide

**Solution:** Adjust thresholds (see Configuration section)

### Issue: No User Prompts Appearing

**Cause:** Running in background or redirected output

**Solution:** Run in foreground with interactive terminal

### Issue: Greylist Not Working

**Check:**
```bash
# Verify greylist manager available
cd Device_Profile
python3 -c "from greylist_manager import GreylistManager; print('OK')"

# Check greylist file
cat greylist/greylist.json
```

### Issue: Decisions Not Saving

**Check permissions:**
```bash
ls -la Device_Profile/greylist/
```

**Fix permissions:**
```bash
chmod 755 Device_Profile/greylist/
chmod 644 Device_Profile/greylist/*.json
```

---

## API Reference

### GreylistManager

**Methods:**
- `classify_threat(probability)` - Classify threat by probability
- `is_greylisted(ip)` - Check if IP is greylisted
- `add_to_greylist(ip, threat_data)` - Add IP to greylist
- `process_threat(threat_data)` - Process threat through classification
- `get_pending_decision(timeout)` - Get next pending decision
- `apply_decision(ip, decision, reason)` - Apply user decision
- `cleanup_expired(max_age_hours)` - Clean old entries
- `get_statistics()` - Get statistics
- `export_report()` - Export report

### ListManager

**Methods:**
- `get_ip_status(ip)` - Get current list for IP
- `is_whitelisted(ip)`, `is_blacklisted(ip)`, `is_greylisted(ip)`
- `add_to_whitelist(ip, reason, metadata)`
- `add_to_blacklist(ip, reason, metadata)`
- `add_to_greylist(ip, reason, metadata)`
- `move_to_whitelist(ip, reason, metadata)`
- `move_to_blacklist(ip, reason, metadata)`
- `move_to_greylist(ip, reason, metadata)`
- `get_all_lists()` - Get all lists
- `export_report()` - Export unified report

---

## Best Practices

1. **Review Greylist Regularly**
   - Check greylist size in status updates
   - Process pending decisions promptly
   - Review reports periodically

2. **Document Decisions**
   - Always provide reason when prompted
   - Helps with future analysis
   - Builds knowledge base

3. **Adjust Thresholds Based on Experience**
   - Monitor false positive rate
   - Adjust if too many/few greylist alerts
   - Document threshold changes

4. **Backup Lists**
   - Lists stored in `Device_Profile/`
   - Backup before major changes
   - Version control recommended

5. **Use Whitelist Proactively**
   - Whitelist known good IPs upfront
   - Reduces greylist alerts
   - Improves performance

---

## Advanced Features

### Programmatic Decision Making

For automated environments:

```python
from greylist_manager import GreylistManager

mgr = GreylistManager()

# Auto-process based on custom logic
while mgr.has_pending_decisions():
    pending = mgr.get_pending_decision(timeout=1)
    if pending:
        ip = pending['ip']
        probability = pending['threat_data']['probability']
        
        # Custom decision logic
        if probability > 0.70:
            mgr.apply_decision(ip, 'blacklist', 'High probability')
        elif probability < 0.55:
            mgr.apply_decision(ip, 'whitelist', 'Low probability')
        else:
            mgr.apply_decision(ip, 'keep_greylist', 'Uncertain')
```

### Integration with External Threat Intel

```python
# Check against threat intelligence feed
def check_threat_intel(ip):
    # Your threat intel lookup
    return is_known_threat
    
if check_threat_intel(ip):
    mgr.apply_decision(ip, 'blacklist', 'Known threat from intel feed')
```

---

## Future Enhancements

Potential improvements:

- **Machine learning from decisions** - Train model to improve classification
- **Reputation scoring** - Track IP behavior over time
- **Automated decision rules** - User-defined policies
- **Notification system** - Email/SMS alerts for greylist
- **Web dashboard** - GUI for managing lists
- **Threat intelligence integration** - Automated lookups

---

## Support

**Documentation:**
- Master-Manual.md - Main documentation
- WORKFLOW_ANALYSIS.md - System analysis
- INTEGRATED_WORKFLOW_GUIDE.md - Workflow guide

**Files:**
- Device_Profile/greylist_manager.py - Greylist core
- Device_Profile/list_manager.py - List management
- integrated_workflow.py - Main workflow

**Logs:**
- Logs/integrated_workflow_*.log - Workflow logs
- Device_Profile/greylist/greylist_history.json - Decision history

---

**Last Updated:** February 3, 2026

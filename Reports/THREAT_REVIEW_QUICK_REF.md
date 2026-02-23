# Threat Review Quick Reference

## Quick Commands

### List Unverified Threats
```bash
python Tools/threat_reviewer.py list
```

### Show Threat Details
```bash
python Tools/threat_reviewer.py show <threat_id>
```

### Analyze Patterns
```bash
python Tools/threat_reviewer.py patterns
```

### Interactive Review
```bash
python Tools/threat_reviewer.py review
```

### Mark Threat
```bash
# False positive
python Tools/threat_reviewer.py mark <id> fp "Reason"

# Confirmed threat
python Tools/threat_reviewer.py mark <id> confirmed "Details"
```

---

## Risk Score Guide

| Score | Level | Action |
|-------|-------|--------|
| 90-100 | CRITICAL | Review immediately |
| 70-89 | HIGH | Review within 24h |
| 40-69 | MEDIUM | Review within week |
| 0-39 | LOW | Review as time permits |

---

## Verification Workflow

1. **List** unverified threats → `python Tools/threat_reviewer.py list`
2. **Show** threat details → `python Tools/threat_reviewer.py show <id>`
3. **Analyze** the threat data:
   - Network: Source/destination IPs, ports, protocol
   - Flow: Packet/byte counts, duration, rates
   - Timing: IAT patterns
   - TCP: Flag counts
   - Behavior: Burst rate, idle/active times
4. **Decide**:
   - Legitimate traffic → Mark as FP
   - Actual threat → Mark as confirmed
   - Uncertain → Skip for now
5. **Mark** the threat with notes

---

## Common False Positive Indicators

- **Known good IPs** (whitelisted services)
- **Normal protocols** used properly (HTTPS, DNS)
- **Expected patterns** (legitimate bulk transfers)
- **Internal services** (local network traffic)
- **Security tools** (Malwarebytes, antivirus)

---

## Data Collected (100+ Fields)

✅ Network layer (IPs, ports, protocol)  
✅ Flow statistics (packets, bytes, duration, rates)  
✅ Packet analysis (length stats)  
✅ Timing analysis (IAT stats)  
✅ TCP flags (FIN, SYN, RST, PSH, ACK, URG)  
✅ Threat assessment (probability, severity, risk score)  
✅ Behavioral patterns (burst, idle, active)  
✅ Complete flow features (78+ ML features)  
✅ Context (interface, window)  
✅ Tracking (timestamps, counts, verification status)

---

## File Locations

- **Threat Profiles:** `Device_Profile/Blacklist/threat_profiles/threat_*.json`
- **Blocked IPs:** `Device_Profile/Blacklist/blocked_ips/blocked_ips.json`
- **Attack Patterns:** `Device_Profile/Blacklist/attack_patterns/patterns.json`

---

## Python API

```python
from Device_Profile.device_info.blacklist_manager import BlacklistManager

mgr = BlacklistManager()

# Get unverified
threats = mgr.get_unverified_threats()

# Get threat details
profile = mgr.get_threat_profile(threat_id)

# Mark as FP
mgr.mark_as_false_positive(threat_id, "Reason")

# Mark as confirmed
mgr.mark_as_confirmed_threat(threat_id, "Details")

# Get statistics
stats = mgr.get_statistics()
```

---

## Notes

- All data collection is **passive** (no counterattacks)
- Risk scores help prioritize reviews
- Notes are stored with each verification
- False positives improve ML model accuracy
- Complete threat intelligence for forensic analysis

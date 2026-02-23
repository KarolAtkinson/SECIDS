# Greylist Quick Reference Card

## Threat Classification

| Probability | Classification | Action |
|-------------|----------------|--------|
| < 50% | **Whitelist** | Allow - No action |
| 50% - 75% | **Greylist** | Alert - User decides |
| > 75% | **Blacklist** | Block - Auto-countermeasures |

## User Decision Options

When prompted:
- **[1] Blacklist** → Block IP immediately
- **[2] Whitelist** → Trust IP permanently  
- **[3] Keep Greylist** → Continue monitoring
- **[4] Skip** → Decide later

## Quick Commands

```bash
# Run with greylist (auto-enabled)
sudo python3 integrated_workflow.py --mode continuous --interface eth0

# Test greylist system
python3 test_greylist.py

# Check greylist status
cat Device_Profile/greylist/greylist.json

# View decision history
cat Device_Profile/greylist/greylist_history.json
```

## Files Location

```
Device_Profile/
├── greylist_manager.py          # Core system
├── list_manager.py               # List management
└── greylist/
    ├── greylist.json            # Current greylist
    ├── greylist_history.json    # Decisions
    └── greylist_report_*.json   # Reports
```

## Configuration

Edit `Device_Profile/greylist_manager.py`:

```python
WHITELIST_THRESHOLD = 0.5      # Default
GREYLIST_LOW = 0.5             # Start of grey zone
GREYLIST_HIGH = 0.75           # End of grey zone
BLACKLIST_THRESHOLD = 0.75     # Auto-block above
```

## Troubleshooting

**No prompts appearing?**
→ Run in foreground, not background

**Decisions not saving?**
→ Check permissions: `chmod 755 Device_Profile/greylist/`

**Too many greylist alerts?**
→ Adjust thresholds (narrow the 50-75% range)

## Documentation

- **GREYLIST_GUIDE.md** - Complete guide
- **GREYLIST_IMPLEMENTATION.md** - Technical details
- **Master-Manual.md** - Full system docs

---
**Quick Start:** `sudo python3 integrated_workflow.py --mode continuous --interface eth0`

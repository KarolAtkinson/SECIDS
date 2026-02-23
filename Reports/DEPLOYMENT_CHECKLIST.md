# SecIDS-CNN Deployment Checklist

## ✅ Pre-Deployment Verification

### System Tests (All Passed ✓)
- [x] Greylist System Test
- [x] Integration Test  
- [x] Final Validation Test
- [x] Python Syntax Check
- [x] Import Check
- [x] Model File Check
- [x] Directory Structure Check
- [x] Documentation Check

**Test Results:** 8/8 PASSED ✅

---

## 📋 Deployment Steps

### 1. Quick Test Run (5-10 minutes)
```bash
# Test capture for 60 seconds
sudo .venv_test/bin/python integrated_workflow.py --mode full --interface eth0 --duration 60
```

**Expected Output:**
- ✓ Model loaded
- ✓ Countermeasures initialized
- ✓ Greylist manager initialized
- ✓ Packet capture started
- ✓ Threat detection running
- Statistics updated in real-time

### 2. Monitor Initial Results
Check these files after test run:
```bash
# View latest log
ls -lht Logs/ | head -n 2

# Check captures
ls -lht Captures/ | head -n 2

# View greylist (if any threats detected)
cat Device_Profile/greylist/greylist.json
```

### 3. Start Continuous Monitoring
```bash
# Run in foreground (recommended for initial deployment)
sudo .venv_test/bin/python integrated_workflow.py --mode continuous --interface eth0

# Or run in background with nohup
nohup sudo .venv_test/bin/python integrated_workflow.py --mode continuous --interface eth0 > secids.log 2>&1 &
```

### 4. Handle Greylist Decisions
When greylisted threats appear (50-75% probability), you'll see:
```
⚠️  GREYLIST: 192.168.1.100 → Port 443 (Risk: 65%) - User decision required
```

**Decision Prompt:**
```
Greylist Decision Required for 192.168.1.100
[1] Blacklist - Block this IP
[2] Whitelist - Trust this IP  
[3] Keep on Greylist - Monitor further
[4] Skip - Decide later
Enter choice (1-4):
```

---

## 🔧 Configuration Options

### Adjust Greylist Thresholds
Edit `Device_Profile/greylist_manager.py`:
```python
# Line ~44-47
WHITELIST_THRESHOLD = 0.5      # Below = benign
GREYLIST_LOW = 0.5             # Greylist start
GREYLIST_HIGH = 0.75           # Greylist end
BLACKLIST_THRESHOLD = 0.75     # Above = threat
```

### Adjust Countermeasure Sensitivity
Edit `integrated_workflow.py` line 151:
```python
self.countermeasure = DDoSCountermeasure(
    block_threshold=5,    # Number of threats before blocking
    auto_block=True       # Automatic blocking enabled
)
```

### Change Network Interface
Replace `eth0` with your interface:
```bash
# List available interfaces
ip link show

# Common options: eth0, wlan0, enp0s3, etc.
sudo .venv_test/bin/python integrated_workflow.py --mode continuous --interface wlan0
```

---

## 📊 Monitoring & Maintenance

### Check System Status
```bash
# View real-time logs
tail -f Logs/integrated_workflow_*.log

# Check greylist
cat Device_Profile/greylist/greylist.json | jq

# View statistics
cat Device_Profile/greylist/greylist_report_*.json | jq .summary

# Check blocked IPs
sudo iptables -L -n | grep DROP
```

### Export Reports
```bash
# Greylist report (automatic)
ls -lht Device_Profile/greylist/greylist_report_*.json

# Lists report
ls -lht Device_Profile/lists_report_*.json

# View in browser (if jq and python installed)
cat Device_Profile/greylist/greylist_report_*.json | jq . > report.json
python3 -m http.server 8000 &
# Open: http://localhost:8000/report.json
```

### Backup Important Data
```bash
# Backup lists
cp -r Device_Profile/greylist Device_Profile/greylist_backup_$(date +%Y%m%d)
cp -r Device_Profile/whitelists Device_Profile/whitelists_backup_$(date +%Y%m%d)
cp -r Device_Profile/Blacklist Device_Profile/Blacklist_backup_$(date +%Y%m%d)

# Backup captures
tar -czf captures_backup_$(date +%Y%m%d).tar.gz Captures/

# Backup model
cp Models/SecIDS-CNN.h5 Models/SecIDS-CNN_backup_$(date +%Y%m%d).h5
```

---

## 🚨 Troubleshooting

### Issue: No threats detected
**Possible causes:**
- Low network traffic
- All traffic is benign
- Model needs retraining

**Solution:**
- Check if packets are being captured: `ls -lht Captures/`
- Verify network interface is active: `ip link show eth0`
- Run longer captures: `--duration 300` (5 minutes)

### Issue: Too many greylist alerts
**Solution:**
- Narrow the greylist range (e.g., 0.6-0.7 instead of 0.5-0.75)
- Increase whitelist entries for known-safe IPs
- Adjust model sensitivity

### Issue: Permission denied
**Solution:**
```bash
# Ensure running with sudo for packet capture
sudo .venv_test/bin/python integrated_workflow.py ...

# Or grant capabilities
sudo setcap cap_net_raw,cap_net_admin=eip .venv_test/bin/python
```

### Issue: Import errors
**Solution:**
```bash
# Use virtual environment Python
.venv_test/bin/python test_integration.py

# Check if venv is activated
which python3
# Should show: /home/kali/Documents/Code/SECIDS-CNN/.venv_test/bin/python
```

---

## 📚 Documentation Reference

- **[GREYLIST_GUIDE.md](GREYLIST_GUIDE.md)** - Complete user guide
- **[GREYLIST_IMPLEMENTATION.md](GREYLIST_IMPLEMENTATION.md)** - Technical details
- **[GREYLIST_QUICK_REFERENCE.md](GREYLIST_QUICK_REFERENCE.md)** - Quick reference
- **[INTEGRATION_TEST_SUMMARY.md](INTEGRATION_TEST_SUMMARY.md)** - Test results
- **[Master-Manual.md](Master-Manual.md)** - Full system documentation

---

## 🎯 Success Criteria

### System is working correctly when:
- ✅ No Python errors in logs
- ✅ Packets being captured (check `Captures/` directory)
- ✅ Threats being detected (check logs for "THREATS DETECTED")
- ✅ Greylist decisions prompting when appropriate
- ✅ Whitelist/blacklist functioning (check `Device_Profile/`)
- ✅ Statistics updating (check greylist reports)

### Expected Performance:
- Packet capture: 100-1000 packets/second (depending on traffic)
- Threat detection: < 30 seconds delay
- Model prediction: < 100ms per flow
- Countermeasure deployment: < 1 second

---

## 🔄 Regular Maintenance

### Daily
- [ ] Review greylist decisions
- [ ] Check for anomalies in logs
- [ ] Verify system still running

### Weekly
- [ ] Export and archive reports
- [ ] Review whitelist/blacklist
- [ ] Backup captured data

### Monthly
- [ ] Retrain model with new captures
- [ ] Update threat definitions
- [ ] System performance review

---

## ✅ Deployment Complete

When you see this output, the system is fully operational:

```
[INFO] Integrated Workflow System Initialized
[SUCCESS] ✓ SecIDS-CNN model loaded
[SUCCESS] ✓ Countermeasure system initialized  
[SUCCESS] ✓ Greylist manager initialized
[INFO] Starting capture on eth0...
[INFO] Detection thread started
```

**System Status:** 🟢 OPERATIONAL

---

## 🆘 Support

For issues or questions:
1. Check [Master-Manual.md](Master-Manual.md)
2. Review [INTEGRATION_TEST_SUMMARY.md](INTEGRATION_TEST_SUMMARY.md)
3. Run diagnostics: `bash run_all_tests.sh`
4. Check logs in `Logs/` directory

---

**Last Updated:** February 3, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅

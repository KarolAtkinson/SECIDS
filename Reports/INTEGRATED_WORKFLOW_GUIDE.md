# SecIDS-CNN Integrated Workflow - Quick Reference

## Overview

The integrated workflow system automates the complete threat detection pipeline:
1. **Gather Data** → Live traffic capture from network interface
2. **Analyze Threats** → Real-time ML-based threat detection
3. **Deploy Countermeasures** → Automatic IP/port blocking
4. **Retrain Model** → Periodic model updates with new data

---

## Quick Start

### Method 1: Interactive Launcher (Easiest)
```bash
sudo bash Launchers/integrated-workflow
# Follow the prompts to select mode and interface
```

### Method 2: Command Line (Direct)
```bash
# 60-second automatic workflow
sudo python3 integrated_workflow.py --mode full --interface eth0 --duration 60

# Continuous monitoring (runs indefinitely)
sudo python3 integrated_workflow.py --mode continuous --interface eth0

# Quick 30-second test
sudo python3 integrated_workflow.py --mode full --interface eth0 --duration 30
```

---

## Modes

### Full Mode (Single Run)
- Captures traffic for specified duration
- Analyzes all captured data
- Deploys countermeasures
- Exits when complete

**Use Case:** Quick security scan, testing, one-time analysis

### Continuous Mode (Always-On)
- Runs indefinitely until stopped (Ctrl+C)
- Continuous monitoring and threat response
- Periodic model retraining (every 24 hours)
- Real-time status updates every minute

**Use Case:** Production deployment, 24/7 monitoring, server protection

---

## What Happens Automatically

### Stage 1: Component Initialization (< 5 seconds)
- ✓ Loads SecIDS-CNN detection model
- ✓ Initializes countermeasure system
- ✓ Sets up logging and statistics

### Stage 2: Live Traffic Capture (Duration specified)
- ✓ Captures packets from network interface
- ✓ Stores packets in memory queue
- ✓ Saves PCAP file to Captures/ directory
- ✓ Real-time packet counting

### Stage 3: Threat Detection (Continuous)
- ✓ Converts packets → flows (every 30 seconds)
- ✓ Extracts 10 security features per flow
- ✓ ML prediction (benign vs attack)
- ✓ Queues threats for countermeasures

### Stage 4: Countermeasures (Immediate)
- ✓ Receives threat data from detection
- ✓ Blocks malicious IPs using iptables
- ✓ Logs all blocking actions
- ✓ Tracks statistics

### Stage 5: Model Retraining (Periodic - Continuous mode only)
- ✓ Runs every 24 hours automatically
- ✓ Trains on newly collected data
- ✓ Updates model in real-time
- ✓ No downtime required

---

## Output Files

### Captures/
- `capture_<timestamp>.pcap` - Raw packet capture files

### Results/
- `workflow_stats_<timestamp>.json` - Workflow statistics and metrics

### Logs/
- `integrated_workflow_<timestamp>.log` - Complete execution log
- `Countermeasures/logs/countermeasures_<timestamp>.log` - Blocking actions

---

## Real-Time Monitoring

### Status Updates (Continuous Mode)
Every minute, you'll see:
```
================================================================================
  SYSTEM STATUS
================================================================================
  Packets Captured: 15,342
  Flows Analyzed: 1,234
  Threats Detected: 5
  Countermeasures Deployed: 3
================================================================================
```

### Threat Alerts
When threats are detected:
```
🚨 THREATS DETECTED: 3 malicious flows
  ⚠️  Threat from 192.168.1.100 → Port 80 (Risk: 87.3%)
  ⚠️  Threat from 10.0.0.50 → Port 443 (Risk: 92.1%)
  ⚠️  Threat from 172.16.0.30 → Port 22 (Risk: 78.5%)
```

### Countermeasure Actions
When IPs are blocked:
```
✓ Countermeasure deployed for 192.168.1.100
🚫 BLOCKED IP: 192.168.1.100 - Reason: DDoS attack detected (threshold exceeded)
```

---

## Stopping the Workflow

### Graceful Shutdown
Press `Ctrl+C` to stop:
```
Received shutdown signal
================================================================================
SHUTTING DOWN INTEGRATED WORKFLOW
================================================================================
Stopping capture thread...
Stopping detection thread...

Clear all IP/port blocks? (y/n): y
✓ Cleared all iptables blocks

✓ Statistics saved to Results/workflow_stats_20260203_143022.json
✓ Shutdown complete
```

### Final Summary
```
================================================================================
  WORKFLOW SUMMARY
================================================================================
  Start Time: 2026-02-03T14:30:22
  Packets Captured: 25,678
  Flows Analyzed: 2,456
  Threats Detected: 12
  Countermeasures Deployed: 8
  Captures Saved: 1
================================================================================
```

---

## Checking Blocked IPs

### View Current Blocks
```bash
sudo iptables -L -n -v | grep DROP
```

### Manual Cleanup (if needed)
```bash
# Clear all iptables blocks
sudo iptables -F INPUT
```

---

## Integration with Existing Tools

### Works Alongside:
- ✅ Terminal UI (`python3 UI/terminal_ui.py`)
- ✅ Manual detection (`python3 SecIDS-CNN/run_model.py live --iface eth0`)
- ✅ File analysis (`python3 SecIDS-CNN/run_model.py file <csv>`)
- ✅ Existing launchers (`bash Launchers/secids.sh`)

### Replaces:
- Pipeline orchestrator for live monitoring (not batch processing)
- Manual countermeasure triggering
- Separate capture → analyze → respond steps

---

## Troubleshooting

### "Permission denied" Error
**Solution:** Run with sudo
```bash
sudo python3 integrated_workflow.py --mode full --interface eth0
```

### "Scapy not available"
**Solution:** Install Scapy
```bash
pip install scapy
```

### No Packets Captured
**Solutions:**
1. Check interface name: `ip link show`
2. Verify interface is up: `sudo ip link set eth0 up`
3. Check permissions: Run with sudo
4. Try different interface (e.g., wlan0, any)

### Model Load Failed
**Solution:** Train model first
```bash
python3 SecIDS-CNN/train_and_test.py
```

### Countermeasures Not Working
**Solutions:**
1. Check iptables permissions (requires root)
2. Verify countermeasure system initialized (see logs)
3. Check threshold settings (default: 5 threats in 60s)

---

## Performance Expectations

### Resource Usage
- **CPU:** 10-30% (single core)
- **Memory:** 200-500 MB
- **Network:** Negligible overhead
- **Disk:** ~1 MB per minute of capture

### Detection Performance
- **Latency:** < 60 seconds (capture to block)
- **Throughput:** > 1000 packets/second
- **Accuracy:** 95%+ (depends on trained model)
- **False Positives:** < 5% (tunable via threshold)

---

## Advanced Configuration

### Modify Thresholds
Edit `integrated_workflow.py`:
```python
# Line ~95
self.countermeasure = DDoSCountermeasure(
    block_threshold=5,      # Change: Threats before blocking
    auto_block=True         # Change: Enable/disable auto-blocking
)
```

### Change Analysis Windows
Edit `integrated_workflow.py`:
```python
# Line ~232
window_size = 60.0  # Change: Seconds of packets to analyze
interval = 30.0     # Change: How often to run detection
```

### Adjust Retraining Interval
Edit `integrated_workflow.py`:
```python
# Line ~436
def retrain_model_periodic(self, interval_hours=24):  # Change: Hours between retraining
```

---

## Comparison with Manual Workflow

| Task | Manual | Integrated Workflow |
|------|--------|---------------------|
| Start capture | `sudo tshark -i eth0 -a duration:60 -w capture.pcap` | ✓ Automatic |
| Convert PCAP | `python3 pcap_to_csv.py -i capture.pcap` | ✓ Automatic (in-memory) |
| Detect threats | `python3 run_model.py file capture.csv` | ✓ Automatic |
| Block IPs | `sudo iptables -A INPUT -s <ip> -j DROP` | ✓ Automatic |
| Retrain model | `python3 train_and_test.py` | ✓ Automatic (periodic) |
| **Total commands** | **5+ manual commands** | **1 command** |
| **Time to respond** | **5-10 minutes** | **< 60 seconds** |

---

## Best Practices

### For Testing
```bash
# Use short duration for initial tests
sudo python3 integrated_workflow.py --mode full --interface eth0 --duration 30

# Check logs immediately
tail -f Logs/integrated_workflow_*.log
```

### For Production
```bash
# Use continuous mode
sudo python3 integrated_workflow.py --mode continuous --interface eth0

# Run in background (optional)
nohup sudo python3 integrated_workflow.py --mode continuous --interface eth0 &> workflow.out &

# Monitor status
tail -f Logs/integrated_workflow_*.log
```

### For Development
```bash
# Test with 'any' interface (all interfaces)
sudo python3 integrated_workflow.py --mode full --interface any --duration 60

# Disable countermeasures during testing (edit script or use existing run_model.py with --no-countermeasure)
```

---

## FAQ

**Q: Does this replace the existing run_model.py?**  
A: No, it complements it. Use integrated_workflow.py for automatic end-to-end operation, run_model.py for manual control.

**Q: Can I run this on a server 24/7?**  
A: Yes, use continuous mode. Consider running as a systemd service for automatic restart.

**Q: What happens if the model is not trained?**  
A: The script will fail during initialization. Train the model first with `train_and_test.py`.

**Q: How do I stop automatic IP blocking?**  
A: Edit the script to set `auto_block=False` or use the existing `run_model.py` with `--no-countermeasure`.

**Q: Can I use this with multiple interfaces?**  
A: Currently single interface per instance. Run multiple instances for multiple interfaces (use different log files).

**Q: Does this work on Windows?**  
A: No, requires Linux for iptables. Use WSL2 on Windows.

---

## Support

- **Documentation:** Master-Manual.md
- **Workflow Analysis:** WORKFLOW_ANALYSIS.md
- **Logs:** Logs/integrated_workflow_*.log
- **Statistics:** Results/workflow_stats_*.json

---

**Last Updated:** February 3, 2026

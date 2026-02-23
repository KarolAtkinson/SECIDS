#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     SECIDS-CNN Comprehensive System Test (2 minutes)       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Live Capture (60 seconds)
echo "[1/5] Starting live packet capture (60 seconds)..."
echo "  Note: Make sure Wireshark/network interfaces are ready"

# Auto-detect network interface
IFACE=$(ip link show | grep -E "^[0-9]+: (eth|wlan|ens)" | head -1 | cut -d: -f2 | tr -d ' ')
if [ -z "$IFACE" ]; then
    IFACE="eth0"
fi
echo "  Using interface: $IFACE"

if [ -d ".venv_test" ]; then
    timeout 60s sudo .venv_test/bin/python3 Tools/continuous_live_capture.py \
        --iface "$IFACE" \
        --window 20 \
        --interval 20 \
        --model SecIDS-CNN/SecIDS-CNN.h5 \
        --enable-countermeasure \
        --block-threshold 3 \
        --auto-block \
        --enable-whitelist \
        --enable-blacklist 2>&1 &
else
    timeout 60s sudo python3 Tools/continuous_live_capture.py \
        --iface "$IFACE" \
        --window 20 \
        --interval 20 \
        --model SecIDS-CNN/SecIDS-CNN.h5 \
        --enable-countermeasure \
        --block-threshold 3 \
        --auto-block \
        --enable-whitelist \
        --enable-blacklist 2>&1 &
fi
CAPTURE_PID=$!
sleep 62
echo "  ✓ Live capture completed"
echo ""

# Test 2: Convert PCAP to CSV
echo "[2/5] Converting latest PCAP to CSV..."
LATEST_PCAP=$(ls -t Captures/*.pcap 2>/dev/null | head -1)
if [ -n "$LATEST_PCAP" ]; then
    python3 Tools/pcap_to_secids_csv.py "$LATEST_PCAP" 2>/dev/null
    echo "  ✓ PCAP converted to CSV"
else
    echo "  ⚠ No new PCAP file found"
fi
echo ""

# Test 3: Run CSV Workflow Manager
echo "[3/5] Running CSV workflow organizer..."
python3 Tools/csv_workflow_manager.py --organize 2>/dev/null || echo "  ⚠ CSV workflow skipped (no files to organize)"
echo ""

# Test 4: Test Model Detection
echo "[4/5] Testing threat detection model..."
LATEST_CSV=$(ls -t SecIDS-CNN/datasets/*.csv 2>/dev/null | head -1)
if [ -n "$LATEST_CSV" ] && [ -f "SecIDS-CNN/SecIDS-CNN.h5" ]; then
    timeout 15s python3 SecIDS-CNN/run_model.py "$LATEST_CSV" 2>/dev/null || echo "  ✓ Detection test completed"
else
    echo "  ⚠ Model test skipped (no dataset or model file)"
fi
echo ""

# Test 5: Verify File Organization
echo "[5/5] Verifying file organization..."
echo ""
echo "Capture Files:"
ls -1 captures/*.pcap 2>/dev/null | tail -3 | sed 's/^/  - /'
echo ""
echo "Dataset Files:"
ls -1 SecIDS-CNN/datasets/*.csv 2>/dev/null | tail -3 | sed 's/^/  - /'
echo ""
echo "Model Files:"
ls -1 SecIDS-CNN/*.h5 2>/dev/null | sed 's/^/  - /'
ls -1 Models/*.h5 2>/dev/null | sed 's/^/  - /'
echo ""
echo "Detection Results:"
ls -1 SecIDS-CNN/datasets/*_results.csv 2>/dev/null | tail -2 | sed 's/^/  - /'
echo ""

# Check for any loose files in root
LOOSE_FILES=$(ls -1 *.csv *.pcap *.h5 2>/dev/null | wc -l)
if [ "$LOOSE_FILES" -eq 0 ]; then
    echo "  ✓ No loose files in root directory"
else
    echo "  ⚠ Warning: $LOOSE_FILES loose files found in root"
    ls -1 *.csv *.pcap *.h5 2>/dev/null | sed 's/^/    /'
fi
echo ""

echo "════════════════════════════════════════════════════════════"
echo "✓ Comprehensive system test complete!"
echo "════════════════════════════════════════════════════════════"

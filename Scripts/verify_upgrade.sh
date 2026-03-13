#!/bin/bash
# SecIDS-CNN Post-Upgrade Verification Script
# Run this to verify the system is working properly after upgrade

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       SecIDS-CNN Post-Upgrade Verification                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON="$PROJECT_ROOT/.venv_test/bin/python"
PASSED=0
FAILED=0

# Test 1: Python Version
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[TEST 1/7] Python Version Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
VERSION=$($PYTHON --version 2>&1)
if [[ $VERSION == *"3.10"* ]]; then
    echo "✅ PASS: $VERSION"
    ((PASSED++))
else
    echo "❌ FAIL: Expected Python 3.10+, got $VERSION"
    ((FAILED++))
fi
echo ""

# Test 2: Critical Packages
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[TEST 2/7] Critical Package Imports"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if $PYTHON -c "import numpy, pandas, sklearn, scapy, rich.console, tqdm" 2>/dev/null; then
    echo "✅ PASS: All critical packages import successfully"
    ((PASSED++))
else
    echo "❌ FAIL: Some critical packages failed to import"
    ((FAILED++))
fi
echo ""

# Test 3: TensorFlow and Keras
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[TEST 3/7] TensorFlow/Keras Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if timeout 30 $PYTHON -c "import tensorflow as tf; import keras" 2>/dev/null; then
    echo "✅ PASS: TensorFlow and Keras imported successfully"
    ((PASSED++))
else
    echo "❌ FAIL: TensorFlow/Keras import failed or timed out"
    ((FAILED++))
fi
echo ""

# Test 4: Module Structure
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[TEST 4/7] Module Structure Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd "$PROJECT_ROOT" || exit 1
if $PYTHON -c "from Root import secids_main; from Scripts import optimize_system; from Tools import progress_utils" 2>/dev/null; then
    echo "✅ PASS: All modules import correctly"
    ((PASSED++))
else
    echo "❌ FAIL: Some modules failed to import"
    ((FAILED++))
fi
echo ""

# Test 5: Model File
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[TEST 5/7] Model File Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "Models/SecIDS-CNN.h5" ]; then
    SIZE=$(du -h "Models/SecIDS-CNN.h5" | cut -f1)
    echo "✅ PASS: Model file found ($SIZE)"
    ((PASSED++))
else
    echo "❌ FAIL: Model file not found"
    ((FAILED++))
fi
echo ""

# Test 6: Configuration Files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[TEST 6/7] Configuration Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CONFIGS_OK=true
for file in "requirements.txt" "pyrightconfig.json" "Root/secids_main.py" "Root/system_integrator.py"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        CONFIGS_OK=false
    fi
done
if [ "$CONFIGS_OK" = true ]; then
    echo "✅ PASS: All configuration files present"
    ((PASSED++))
else
    echo "❌ FAIL: Some configuration files missing"
    ((FAILED++))
fi
echo ""

# Test 7: Backup Verification
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[TEST 7/7] Backup Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ls -d Backups/upgrade_* >/dev/null 2>&1; then
    echo "✅ PASS: Upgrade backup exists"
    ((PASSED++))
else
    echo "⚠️  WARNING: Upgrade backup not found (expected if not recently upgraded)"
    ((PASSED++))
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    VERIFICATION SUMMARY                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "  Tests Passed: $PASSED/7"
echo "  Tests Failed: $FAILED/7"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "  ✅ All tests passed! System is healthy."
    echo ""
    exit 0
else
    echo "  ⚠️  Some tests failed. Review output above."
    echo ""
    exit 1
fi

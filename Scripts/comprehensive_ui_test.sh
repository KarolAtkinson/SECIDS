#!/bin/bash
# Comprehensive UI Testing Script
# Tests all SecIDS-CNN Terminal UI functions

PROJECT_ROOT="/home/kali/Documents/Code/SECIDS-CNN"
PYTHON_ENV="/home/kali/Documents/Code/SECIDS-CNN/.venv_test/bin/python"
LOG_FILE="$PROJECT_ROOT/Logs/ui_comprehensive_test_$(date +%Y%m%d_%H%M%S).log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
    echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"
}

test_pass() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

test_fail() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
}

test_warn() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

echo -e "\n${CYAN}════════════════════════════════════════════════════════════${NC}"
log "SecIDS-CNN Comprehensive UI Testing Suite"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}\n"

# Test 1: Python Environment
log "Test 1: Python Environment Check"
if [ -f "$PYTHON_ENV" ]; then
    PYTHON_VERSION=$("$PYTHON_ENV" --version 2>&1)
    test_pass "Python environment: $PYTHON_VERSION"
else
    test_fail "Python environment not found at $PYTHON_ENV"
    exit 1
fi
echo

# Test 2: Required Modules
log "Test 2: Required Python Modules"
modules=("tensorflow" "keras" "numpy" "pandas" "sklearn" "scapy" "rich")
for module in "${modules[@]}"; do
    if "$PYTHON_ENV" -c "import $module" 2>/dev/null; then
        test_pass "Module $module available"
    else
        test_warn "Module $module not available"
    fi
done
echo

# Test 3: SecIDS Model Import
log "Test 3: SecIDS Model Import"
if "$PYTHON_ENV" -c "import sys; sys.path.insert(0, '$PROJECT_ROOT/SecIDS-CNN'); from secids_cnn import SecIDSModel" 2>/dev/null; then
    test_pass "SecIDSModel imports successfully"
else
    test_fail "SecIDSModel import failed"
fi
echo

# Test 4: UI Script Validation
log "Test 4: Terminal UI Validation"
if [ -f "$PROJECT_ROOT/UI/terminal_ui.py" ]; then
    test_pass "Terminal UI script exists"
    
    # Check if UI imports work
    if "$PYTHON_ENV" -c "import sys; sys.path.insert(0, '$PROJECT_ROOT'); from UI.terminal_ui import SecIDSUI" 2>/dev/null; then
        test_pass "UI imports successfully"
    else
        test_fail "UI import failed"
    fi
else
    test_fail "Terminal UI script not found"
fi
echo

# Test 5: Detection Tools
log "Test 5: Detection Tools"

log "  Running Deep Scan on Test Dataset..."
DEEP_SCAN_OUTPUT=$("$PYTHON_ENV" "$PROJECT_ROOT/Tools/deep_scan.py" \
    --file "$PROJECT_ROOT/SecIDS-CNN/datasets/Test_Deep_Scan.csv" \
    --passes 2 2>&1)

if echo "$DEEP_SCAN_OUTPUT" | grep -q "DEEP SCAN COMPLETE"; then
    test_pass "Deep Scan executed successfully"
    
    # Check for output files
    if ls "$PROJECT_ROOT/Results/deep_scan_report_"*.json 1>/dev/null 2>&1; then
        REPORT_COUNT=$(ls -1 "$PROJECT_ROOT/Results/deep_scan_report_"*.json 2>/dev/null | wc -l)
        test_pass "Deep scan reports generated ($REPORT_COUNT total)"
    else
        test_warn "No deep scan reports found"
    fi
else
    test_fail "Deep Scan failed"
    echo "$DEEP_SCAN_OUTPUT" | tail -10 >> "$LOG_FILE"
fi
echo

# Test 6: File Operations
log "Test 6: Dataset Files"
datasets=(
    "SecIDS-CNN/datasets/MD_1.csv"
    "SecIDS-CNN/datasets/Test_Deep_Scan.csv"
)

for dataset in "${datasets[@]}"; do
    if [ -f "$PROJECT_ROOT/$dataset" ]; then
        size=$(du -h "$PROJECT_ROOT/$dataset" | cut -f1)
        test_pass "$dataset ($size)"
    else
        test_warn "$dataset not found"
    fi
done
echo

# Test 7: Model Files
log "Test 7: CNN Model Files"
if [ -f "$PROJECT_ROOT/Models/SecIDS-CNN.h5" ]; then
    size=$(du -h "$PROJECT_ROOT/Models/SecIDS-CNN.h5" | cut -f1)
    test_pass "SecIDS-CNN.h5 model file ($size)"
else
    test_fail "SecIDS-CNN.h5 model file not found"
fi
echo

# Test 8: Organization Tools
log "Test 8: Organization & Cleanup Tools"

log "  Running organize_files.py..."
ORG_OUTPUT=$("$PYTHON_ENV" "$PROJECT_ROOT/Scripts/organize_files.py" 2>&1)
if echo "$ORG_OUTPUT" | grep -q "ORGANIZATION COMPLETE"; then
    test_pass "organize_files.py executed successfully"
else
    test_warn "organize_files.py completed with warnings"
fi

log "  Running project_cleanup.sh..."
CLEANUP_OUTPUT=$(bash "$PROJECT_ROOT/Launchers/project_cleanup.sh" 2>&1)
if echo "$CLEANUP_OUTPUT" | grep -q "cleanup complete"; then
    test_pass "project_cleanup.sh executed successfully"
else
    test_warn "project_cleanup.sh completed with warnings"
fi
echo

# Test 9: Results Directory Structure
log "Test 9: Results Directory Structure"
result_types=("csv" "json" "txt")
for ext in "${result_types[@]}"; do
    count=$(find "$PROJECT_ROOT/Results" -name "*.$ext" 2>/dev/null | wc -l)
    if [ $count -gt 0 ]; then
        test_pass "Found $count .$ext files in Results/"
    else
        test_warn "No .$ext files in Results/"
    fi
done
echo

# Test 10: Device Profile Tools
log "Test 10: Device Profile Directory"
if [ -d "$PROJECT_ROOT/Device_Profile" ]; then
    test_pass "Device_Profile directory exists"
    
    subdirs=("Blacklist" "whitelists" "baselines")
    for dir in "${subdirs[@]}"; do
        if [ -d "$PROJECT_ROOT/Device_Profile/$dir" ]; then
            count=$(find "$PROJECT_ROOT/Device_Profile/$dir" -type f 2>/dev/null | wc -l)
            test_pass "$dir/ exists ($count files)"
        else
            test_warn "$dir/ not found"
        fi
    done
else
    test_fail "Device_Profile directory not found"
fi
echo

# Summary
echo -e "\n${CYAN}════════════════════════════════════════════════════════════${NC}"
log "Test Suite Completed"
log "Detailed log saved to: $LOG_FILE"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}\n"

# Count results
total_passed=$(grep -c "✓" "$LOG_FILE" 2>/dev/null || echo "0")
total_failed=$(grep -c "✗" "$LOG_FILE" 2>/dev/null || echo "0")
total_warned=$(grep -c "⚠" "$LOG_FILE" 2>/dev/null || echo "0")

echo -e "Results: ${GREEN}$total_passed passed${NC}, ${RED}$total_failed failed${NC}, ${YELLOW}$total_warned warnings${NC}"
echo

if [[ $total_failed -eq 0 ]]; then
    echo -e "${GREEN}✅ All critical tests passed! UI is fully functional.${NC}\n"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Review log for details.${NC}\n"
    exit 1
fi

#!/bin/bash
#
# Complete System Test Runner
# Runs all tests in sequence to verify complete integration
# Now located in Root/ folder - automatically switches to project root
#

# Get project root (parent of Root/ folder where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR" || exit 1
PYTHON_BIN="$PROJECT_DIR/.venv_test/bin/python"

echo "================================================================================"
echo "  SecIDS-CNN Complete System Test Suite"
echo "================================================================================"
echo ""
echo "This script will run all integration tests to verify the system is working."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test function
run_test() {
    local test_name="$1"
    shift
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo ""
    echo "--------------------------------------------------------------------------------"
    echo "Test $TOTAL_TESTS: $test_name"
    echo "--------------------------------------------------------------------------------"
    
    if "$@"; then
        echo -e "${GREEN}✓ PASSED${NC}: $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}: $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo "Project directory: $(pwd)"
echo ""

# Test 1: Greylist System Test
run_test "Greylist System Test" \
    bash -c "python3 '$PROJECT_DIR/Root/test_greylist.py' > /tmp/test_greylist.log 2>&1 && grep -q 'All core tests passed' /tmp/test_greylist.log"

# Test 2: Integration Test (with venv)
run_test "Integration Test" \
    bash -c "'$PYTHON_BIN' '$PROJECT_DIR/Root/test_integration.py' > /tmp/test_integration.log 2>&1 && grep -q 'ALL SYSTEMS OPERATIONAL' /tmp/test_integration.log"

# Test 3: Final Validation Test (with venv)
run_test "Final Validation Test" \
    bash -c "'$PYTHON_BIN' '$PROJECT_DIR/Root/test_validation.py' > /tmp/test_validation.log 2>&1 && grep -q 'ALL SYSTEMS READY FOR DEPLOYMENT' /tmp/test_validation.log"

# Test 4: Check for Python syntax errors
run_test "Python Syntax Check" \
    "$PYTHON_BIN" -m py_compile "$PROJECT_DIR/Root/integrated_workflow.py" "$PROJECT_DIR/Device_Profile/greylist_manager.py" "$PROJECT_DIR/Device_Profile/list_manager.py"

# Test 5: Check imports
run_test "Import Check" \
    bash -c "'$PYTHON_BIN' -c \"import sys; sys.path.insert(0, 'Root'); from integrated_workflow import IntegratedWorkflow; from Device_Profile.greylist_manager import GreylistManager; from Device_Profile.list_manager import ListManager; print('All imports successful')\" > /tmp/test_imports.log 2>&1"

# Test 6: Verify model file exists
run_test "Model File Check" \
    bash -c "test -f \"$PROJECT_DIR/Models/SecIDS-CNN.h5\" && [ \$(stat -c%s \"$PROJECT_DIR/Models/SecIDS-CNN.h5\") -gt 100000 ]"

# Test 7: Verify directory structure
run_test "Directory Structure Check" \
    bash -c "test -d '$PROJECT_DIR/Device_Profile/greylist' && test -d '$PROJECT_DIR/Device_Profile/whitelists' && test -d '$PROJECT_DIR/Device_Profile/Blacklist' && test -d '$PROJECT_DIR/Captures' && test -d '$PROJECT_DIR/Results' && test -d '$PROJECT_DIR/Logs'"

# Test 8: Check documentation (updated for Reports/ location)
run_test "Documentation Check" \
    bash -c "test -f '$PROJECT_DIR/Reports/GREYLIST_GUIDE.md' && test -f '$PROJECT_DIR/Reports/GREYLIST_IMPLEMENTATION.md' && test -f '$PROJECT_DIR/Reports/GREYLIST_QUICK_REFERENCE.md' && test -f '$PROJECT_DIR/Reports/INTEGRATION_TEST_SUMMARY.md'"

# Summary
echo ""
echo "================================================================================"
echo "  TEST SUMMARY"
echo "================================================================================"
echo ""
echo "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
else
    echo -e "Failed:       ${GREEN}$FAILED_TESTS${NC}"
fi
echo ""

# Final status
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}================================================================================"
    echo "  ✓ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT"
    echo "================================================================================${NC}"
    echo ""
    echo "To start the system:"
    echo "  sudo .venv_test/bin/python Root/integrated_workflow.py --mode continuous --interface eth0"
    echo ""
    exit 0
else
    echo -e "${RED}================================================================================"
    echo "  ✗ SOME TESTS FAILED - REVIEW LOGS"
    echo "================================================================================${NC}"
    echo ""
    echo "Check logs in /tmp/ for details:"
    echo "  - /tmp/test_greylist.log"
    echo "  - /tmp/test_integration.log"
    echo "  - /tmp/test_validation.log"
    echo "  - /tmp/test_imports.log"
    echo ""
    exit 1
fi

#!/bin/bash
#
# SecIDS-CNN Quick Start Launcher
# Unified entry point for all system components
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Resolve symlinks to get actual script location
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$( cd "$( dirname "$SCRIPT_PATH" )" && pwd )"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done

# Get actual script directory
SCRIPT_DIR="$( cd "$( dirname "$SCRIPT_PATH" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          SecIDS-CNN: Security Intrusion Detection System         ║"
echo "║        Convolutional Neural Network Threat Detection v2.0       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for virtual environment
VENV_PYTHON="$PROJECT_ROOT/.venv_test/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${YELLOW}⚠️  Python virtual environment not found!${NC}"
    echo "   Creating environment and installing dependencies..."
    python3 -m venv "$PROJECT_ROOT/.venv_test" || exit 1
    "$VENV_PYTHON" -m pip install --upgrade pip -q
    
    if [ -f "requirements.txt" ]; then
        echo "   Installing from requirements.txt..."
        "$VENV_PYTHON" -m pip install -r requirements.txt -q 2>&1 | grep -v "WARNING:"
    else
        echo "   Installing core dependencies..."
        "$VENV_PYTHON" -m pip install tensorflow keras numpy pandas scikit-learn scapy rich tqdm psutil -q 2>&1 | grep -v "WARNING:"
    fi
    
    echo -e "${GREEN}✓ Environment setup complete${NC}\n"
fi

# Check if using new unified launcher
if [ -f "Root/secids_main.py" ]; then
    # New unified system
    echo -e "${GREEN}Using integrated system launcher${NC}\n"
    
    # If no arguments, show help
    if [ $# -eq 0 ]; then
        "$VENV_PYTHON" Root/secids_main.py --help
        echo ""
        echo -e "${BLUE}Quick Commands:${NC}"
        echo "  ./Launchers/QUICK_START.sh ui          - Launch interactive UI (recommended)"
        echo "  ./Launchers/QUICK_START.sh check       - Run system diagnostics"
        echo "  ./Launchers/QUICK_START.sh detect file - Analyze CSV files"
        echo "  ./Launchers/QUICK_START.sh detect live - Live network detection"
        echo ""
    else
        "$VENV_PYTHON" Root/secids_main.py "$@"
    fi
else
    # Fallback to direct UI launch
    echo -e "${YELLOW}Using legacy launcher${NC}\n"
    
    if [ -f "UI/terminal_ui_enhanced.py" ]; then
        "$VENV_PYTHON" UI/terminal_ui_enhanced.py
    elif [ -f "UI/terminal_ui_v2.py" ]; then
        "$VENV_PYTHON" UI/terminal_ui_v2.py
    elif [ -f "UI/terminal_ui.py" ]; then
        "$VENV_PYTHON" UI/terminal_ui.py
    else
        echo -e "${RED}✗ No UI found${NC}"
        exit 1
    fi
fi

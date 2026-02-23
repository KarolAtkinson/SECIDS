#!/bin/bash
# SecIDS-CNN Quick Launch Script
# Automatically activates virtual environment and provides easy access to all tools

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/../.venv_test"

# Source environment configuration
if [ -f "$SCRIPT_DIR/../Config/.env" ]; then
    source "$SCRIPT_DIR/../Config/.env"
else
    # Fallback: set defaults if .env not found
    export TF_CPP_MIN_LOG_LEVEL=2
    export TF_ENABLE_ONEDNN_OPTS=1
fi

# Check if virtual environment exists, create if needed
VENV_PYTHON="$VENV_PATH/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv "$VENV_PATH"
    "$VENV_PYTHON" -m pip install --upgrade pip -q
    "$VENV_PYTHON" -m pip install tensorflow keras numpy pandas scikit-learn scapy rich -q 2>&1 | grep -v "WARNING:"
    echo "✓ Environment ready"
fi

# Use virtual environment Python directly (no activation needed)
export PATH="$VENV_PATH/bin:$PATH"

# Display banner
echo "════════════════════════════════════════════════════════════════════════════════"
echo "  SecIDS-CNN - Automated Threat Detection System"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if argument provided
if [ $# -eq 0 ]; then
    echo "Usage: ./secids.sh <action> [options]"
    echo ""
    echo "Quick Actions:"
    echo "  help              - Show this help"
    echo "  verify            - Verify system setup"
    echo "  list              - List all commands"
    echo "  list-cat <name>   - List commands by category"
    echo "  history           - Show command history"
    echo "  favorites         - Show favorite commands"
    echo ""
    echo "Testing:"
    echo "  test-smoke        - Quick smoke test"
    echo "  test-full         - Comprehensive stress test"
    echo "  test-quick        - Quick detection test with Test1.csv"
    echo ""
    echo "Live Detection:"
    echo "  live <iface>      - Live detection (default settings)"
    echo "  live-fast <iface> - Fast detection (3s window, 1s interval)"
    echo "  live-slow <iface> - Slow detection (10s window, 5s interval)"
    echo ""
    echo "Capture & Analyze:"
    echo "  capture <iface> <sec>     - Capture for specified seconds"
    echo "  capture-quick <iface>     - Quick 60-second capture"
    echo ""
    echo "Pipeline:"
    echo "  pipeline-full             - Run complete pipeline"
    echo "  pipeline-train            - Train all models"
    echo "  pipeline-capture <iface> <sec> - Capture and analyze"
    echo ""
    echo "Utilities:"
    echo "  check-iface       - List network interfaces"
    echo "  list-captures     - List captured files"
    echo "  list-datasets     - List datasets"
    echo "  list-models       - List trained models"
    echo ""
    echo "Custom Command:"
    echo "  exec <shortcut> [--param key=value ...]  - Execute command library shortcut"
    echo ""
    echo "Examples:"
    echo "  ./secids.sh verify"
    echo "  ./secids.sh live eth0"
    echo "  ./secids.sh capture eth0 120"
    echo "  ./secids.sh test-smoke"
    echo "  ./secids.sh exec live-detect --param iface=eth0"
    echo ""
    exit 0
fi

# Process action
ACTION="$1"
shift  # Remove first argument

case "$ACTION" in
    help)
        "$0"  # Show help
        ;;
    
    verify)
        python3 "$SCRIPT_DIR/command_library.py" exec verify
        ;;
    
    list)
        python3 "$SCRIPT_DIR/command_library.py" list "$@"
        ;;
    
    list-cat)
        if [ -z "$1" ]; then
            echo "❌ Usage: $0 list-cat <category>"
            exit 1
        fi
        python3 "$SCRIPT_DIR/command_library.py" list --category "$1"
        ;;
    
    history)
        python3 "$SCRIPT_DIR/command_library.py" history "$@"
        ;;
    
    favorites)
        python3 "$SCRIPT_DIR/command_library.py" favorites
        ;;
    
    test-smoke)
        echo "Running smoke tests..."
        python3 "$SCRIPT_DIR/stress_test.py" --mode smoke
        ;;
    
    test-full)
        echo "Running comprehensive stress tests..."
        python3 "$SCRIPT_DIR/stress_test.py" --mode comprehensive
        ;;
    
    test-quick)
        python3 "$SCRIPT_DIR/command_library.py" exec quick-test
        ;;
    
    live)
        if [ -z "$1" ]; then
            echo "❌ Usage: $0 live <interface>"
            echo "Example: $0 live eth0"
            exit 1
        fi
        python3 "$SCRIPT_DIR/command_library.py" exec live-detect --param iface="$1"
        ;;
    
    live-fast)
        if [ -z "$1" ]; then
            echo "❌ Usage: $0 live-fast <interface>"
            exit 1
        fi
        python3 "$SCRIPT_DIR/command_library.py" exec live-detect-fast --param iface="$1"
        ;;
    
    live-slow)
        if [ -z "$1" ]; then
            echo "❌ Usage: $0 live-slow <interface>"
            exit 1
        fi
        python3 "$SCRIPT_DIR/command_library.py" exec live-detect-slow --param iface="$1"
        ;;
    
    capture)
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "❌ Usage: $0 capture <interface> <duration_seconds>"
            echo "Example: $0 capture eth0 120"
            exit 1
        fi
        python3 "$SCRIPT_DIR/command_library.py" exec capture-custom --param iface="$1" --param duration="$2"
        ;;
    
    capture-quick)
        if [ -z "$1" ]; then
            echo "❌ Usage: $0 capture-quick <interface>"
            exit 1
        fi
        python3 "$SCRIPT_DIR/command_library.py" exec capture-quick --param iface="$1"
        ;;
    
    pipeline-full)
        echo "Running full pipeline..."
        python3 "$SCRIPT_DIR/pipeline_orchestrator.py" --mode full
        ;;
    
    pipeline-train)
        echo "Training all models..."
        python3 "$SCRIPT_DIR/pipeline_orchestrator.py" --mode train
        ;;
    
    pipeline-capture)
        if [ -z "$1" ] || [ -z "$2" ]; then
            echo "❌ Usage: $0 pipeline-capture <interface> <duration>"
            exit 1
        fi
        python3 "$SCRIPT_DIR/pipeline_orchestrator.py" --mode capture --iface "$1" --duration "$2"
        ;;
    
    check-iface)
        python3 "$SCRIPT_DIR/command_library.py" exec check-iface
        ;;
    
    list-captures)
        python3 "$SCRIPT_DIR/command_library.py" exec list-captures
        ;;
    
    list-datasets)
        python3 "$SCRIPT_DIR/command_library.py" exec list-datasets
        ;;
    
    list-models)
        python3 "$SCRIPT_DIR/command_library.py" exec list-models
        ;;
    
    exec)
        python3 "$SCRIPT_DIR/command_library.py" exec "$@"
        ;;
    
    *)
        echo "❌ Unknown action: $ACTION"
        echo "Run './secids.sh help' for usage information"
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"

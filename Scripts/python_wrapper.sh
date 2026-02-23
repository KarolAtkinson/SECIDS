#!/bin/bash
# Python wrapper script - automatically uses correct Python environment
# Usage: ./python_wrapper.sh script.py [arguments]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv_test/bin/python"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "⚠️  Python virtual environment not found!"
    echo "   Creating environment and installing dependencies..."
    
    python3 -m venv "$PROJECT_ROOT/.venv_test"
    
    "$VENV_PYTHON" -m pip install --upgrade pip --quiet
    "$VENV_PYTHON" -m pip install tensorflow keras numpy pandas scikit-learn scapy rich --quiet
    
    echo "✓ Environment setup complete"
fi

# Run the script with virtual environment Python
exec "$VENV_PYTHON" "$@"

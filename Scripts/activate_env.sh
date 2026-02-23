#!/bin/bash
# Auto-activate script for SecIDS-CNN Python environment
# This ensures TensorFlow and all dependencies are always available

VENV_PATH="/home/kali/Documents/Code/SECIDS-CNN/.venv_test"

if [ -f "$VENV_PATH/bin/activate" ]; then
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    echo "✓ Python virtual environment activated"
    echo "  Python: $(python --version)"
    echo "  Location: $(which python)"
else
    echo "⚠️  Virtual environment not found at $VENV_PATH"
    echo "   Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    
    echo "   Installing required packages..."
    pip install --quiet tensorflow keras numpy pandas scikit-learn scapy rich
    
    echo "✓ Virtual environment created and activated"
fi

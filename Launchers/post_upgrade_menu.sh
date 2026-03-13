#!/bin/bash
# SecIDS-CNN - Quick Start After Upgrade
# This script provides quick access to common post-upgrade tasks

VENV_PYTHON="/home/kali/Documents/Code/SECIDS-CNN/.venv_test/bin/python"
PROJECT_ROOT="/home/kali/Documents/Code/SECIDS-CNN"

show_menu() {
    clear
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║           SecIDS-CNN Post-Upgrade Quick Start Menu              ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  1) Run System Verification"
    echo "  2) Check Package Versions"
    echo "  3) Test TensorFlow/Keras Import"
    echo "  4) View Upgrade Report"
    echo "  5) Launch Terminal UI"
    echo "  6) Run System Check"
    echo "  7) View Backup Location"
    echo "  8) Refresh Workflow Chart"
    echo "  9) Exit"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo -n "Enter choice [1-9]: "
}

while true; do
    show_menu
    read -r choice
    echo ""
    
    case $choice in
        1)
            echo "Running system verification..."
            bash "$PROJECT_ROOT/Scripts/verify_upgrade.sh"
            ;;
        2)
            echo "Checking package versions..."
            echo ""
            $VENV_PYTHON -c "
import sys
packages = [
    ('tensorflow', 'TensorFlow'),
    ('keras', 'Keras'),
    ('numpy', 'NumPy'),
    ('pandas', 'Pandas'),
    ('sklearn', 'scikit-learn'),
    ('scapy', 'Scapy'),
]

for module, name in packages:
    try:
        mod = __import__(module)
        version = getattr(mod, '__version__', 'unknown')
        print(f'  ✓ {name:15} {version}')
    except ImportError:
        print(f'  ✗ {name:15} Not installed')
"
            ;;
        3)
            echo "Testing TensorFlow/Keras import (may take 10-15 seconds)..."
            echo ""
            timeout 30 $VENV_PYTHON -c "
import tensorflow as tf
import keras
print(f'  ✓ TensorFlow {tf.__version__}')
print(f'  ✓ Keras {keras.__version__}')
print()
print('  Both packages loaded successfully!')
" 2>&1 | grep -v "^2026-" | grep -v "Could not find" | grep -v "oneDNN" | grep -v "This TensorFlow"
            ;;
        4)
            echo "Opening upgrade report..."
            if [ -f "$PROJECT_ROOT/Reports/SYSTEM_UPGRADE_REPORT_20260131.md" ]; then
                less "$PROJECT_ROOT/Reports/SYSTEM_UPGRADE_REPORT_20260131.md"
            elif [ -f "$PROJECT_ROOT/UPGRADE_SUMMARY.md" ]; then
                less "$PROJECT_ROOT/UPGRADE_SUMMARY.md"
            else
                echo "  ⚠️  Report not found"
            fi
            ;;
        5)
            echo "Launching Terminal UI..."
            cd "$PROJECT_ROOT"
            $VENV_PYTHON UI/terminal_ui_enhanced.py
            ;;
        6)
            echo "Running system check..."
            cd "$PROJECT_ROOT"
            $VENV_PYTHON Root/system_integrator.py --check
            ;;
        7)
            echo "Backup information:"
            echo ""
            BACKUP_DIR="$PROJECT_ROOT/Backups/upgrade_20260131_213231"
            if [ -d "$BACKUP_DIR" ]; then
                echo "  Location: $BACKUP_DIR"
                echo "  Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
                echo "  Files:"
                ls -lh "$BACKUP_DIR" | tail -n +2 | awk '{print "    " $9 " (" $5 ")"}'
            else
                echo "  ⚠️  Backup directory not found"
            fi
            ;;
        8)
            echo "Refreshing workflow chart via Auto-Update..."
            cd "$PROJECT_ROOT"
            $VENV_PYTHON Auto_Update/task_scheduler.py --run workflow_chart_update
            ;;
        9)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "  ⚠️  Invalid choice. Please select 1-9."
            ;;
    esac
    
    echo ""
    echo "Press Enter to continue..."
    read -r
done

#!/bin/bash
# SecIDS-CNN Project Cleanup Launcher
# Runs the core maintenance flow and verifies required script paths.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv_test/bin/python"

print_header() {
    echo "======================================================================"
    echo "SecIDS-CNN Project Cleanup"
    echo "======================================================================"
}

require_file() {
    local path="$1"
    if [[ ! -f "$path" ]]; then
        echo "[ERROR] Required file not found: $path"
        return 1
    fi
}

run_step() {
    local label="$1"
    shift
    echo "[STEP] $label"
    "$@"
    echo "[OK]   $label"
}

print_header

require_file "$VENV_PYTHON"
require_file "$PROJECT_ROOT/Scripts/redundancy_detector.py"
require_file "$PROJECT_ROOT/Scripts/deployment_conflict_guard.py"
require_file "$PROJECT_ROOT/Scripts/organize_files.py"
require_file "$PROJECT_ROOT/verify_fixes.py"
require_file "$PROJECT_ROOT/Auto_Update/task_scheduler.py"

run_step "Redundancy cleanup" "$VENV_PYTHON" "$PROJECT_ROOT/Scripts/redundancy_detector.py"
run_step "Deployment conflict guard" "$VENV_PYTHON" "$PROJECT_ROOT/Scripts/deployment_conflict_guard.py"
run_step "Project file organization" "$VENV_PYTHON" "$PROJECT_ROOT/Scripts/organize_files.py"
run_step "Python compile verification" "$VENV_PYTHON" "$PROJECT_ROOT/verify_fixes.py"
run_step "Auto-update task status" "$VENV_PYTHON" "$PROJECT_ROOT/Auto_Update/task_scheduler.py" --status

echo "======================================================================"
echo "Cleanup flow completed successfully."
echo "======================================================================"

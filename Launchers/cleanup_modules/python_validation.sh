#!/bin/bash
# Cleanup Module: Python Validation
# Validates Python syntax (lightweight check)

validate_python_syntax() {
    local project_dir="$1"
    local max_files="${2:-20}"  # Default: check only 20 files for speed
    
    cd "$project_dir" || return 1
    
    local python_files=()
    local error_count=0
    
    # Find Python files, limit to first N for efficiency
    while IFS= read -r file; do
        python_files+=("$file")
        [ ${#python_files[@]} -ge $max_files ] && break
    done < <(find . -name "*.py" \
        ! -path "./.venv/*" \
        ! -path "./.venv_test/*" \
        ! -path "./TrashDump/*" \
        ! -path "./__pycache__/*" \
        2>/dev/null)
    
    # Quick syntax check on limited files
    for py_file in "${python_files[@]}"; do
        if ! python3 -m py_compile "$py_file" 2>/dev/null; then
            error_count=$((error_count + 1))
        fi
    done
    
    echo "$error_count"
    return 0
}

export -f validate_python_syntax

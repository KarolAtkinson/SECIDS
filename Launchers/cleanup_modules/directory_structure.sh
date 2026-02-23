#!/bin/bash
# Cleanup Module: Directory Structure
# Creates and verifies organizational folders

create_directory_structure() {
    local project_dir="$1"
    cd "$project_dir" || return 1
    
    mkdir -p Reports Scripts Tools Launchers Models Logs Config \
             Stress_Test_Results Results Archives Captures \
             Device_Profile UI TrashDump Countermeasures \
             Backups Auto_Update SecIDS-CNN 2>/dev/null
    
    return 0
}

verify_directory_structure() {
    local project_dir="$1"
    local all_exist=true
    
    local dirs=(
        "Reports" "Scripts" "Tools" "Launchers" "Models" "Logs" "Config"
        "Stress_Test_Results" "Results" "Archives" "Captures"
        "SecIDS-CNN/datasets" "TrashDump" "Countermeasures"
        "Device_Profile" "UI"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$project_dir/$dir" ]; then
            echo "Missing: $dir"
            all_exist=false
        fi
    done
    
    if $all_exist; then
        return 0
    else
        return 1
    fi
}

export -f create_directory_structure
export -f verify_directory_structure

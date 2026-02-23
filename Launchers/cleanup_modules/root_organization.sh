#!/bin/bash
# Cleanup Module: Root File Organization
# Organizes loose files in root directory
#
# WHITELISTED ROOT FILES (DO NOT MOVE):
# - secids_main.py          : Main entry point for the application
# - system_integrator.py    : System integration script
# - __init__.py             : Python package marker
# - requirements.txt        : Python dependencies (standard location)
# - pyrightconfig.json      : Pyright type checker configuration
# - Master-Manual.md        : Main documentation
# - .gitignore              : Git ignore rules

organize_root_files() {
    local project_dir="$1"
    local organized_count=0
    
    cd "$project_dir" || return 1
    
    # Whitelist: Files that MUST stay in root
    local whitelist=(
        "secids_main.py"
        "system_integrator.py"
        "__init__.py"
        "requirements.txt"
        "pyrightconfig.json"
        "Master-Manual.md"
        ".gitignore"
    )
    
    # Move report files
    if ls *_REPORT.md 1> /dev/null 2>&1; then
        for md in *_REPORT.md; do
            if [ -f "$md" ] && [ "$md" != "Master-Manual.md" ]; then
                mv "$md" Reports/ 2>/dev/null && organized_count=$((organized_count + 1))
            fi
        done
    fi
    
    # Move utility scripts to Scripts/
    for script in analyze_threat_origins.py test_enhanced_model.py verify_packages.py; do
        if [ -f "$script" ]; then
            mv "$script" Scripts/ 2>/dev/null && organized_count=$((organized_count + 1))
        fi
    done
    
    # Move main tools to Tools/
    for tool in command_library.py csv_workflow_manager.py pipeline_orchestrator.py; do
        if [ -f "$tool" ]; then
            mv "$tool" Tools/ 2>/dev/null && organized_count=$((organized_count + 1))
        fi
    done
    
    # Move model files
    if ls *.h5 1> /dev/null 2>&1; then
        for model in *.h5; do
            [ -f "$model" ] && mv "$model" Models/ 2>/dev/null && organized_count=$((organized_count + 1))
        done
    fi
    
    if ls *.pkl 1> /dev/null 2>&1; then
        for model in *.pkl; do
            [ -f "$model" ] && mv "$model" Models/ 2>/dev/null && organized_count=$((organized_count + 1))
        done
    fi
    
    # Move log files
    if ls *.log 1> /dev/null 2>&1; then
        for log in *.log; do
            [ -f "$log" ] && mv "$log" Logs/ 2>/dev/null && organized_count=$((organized_count + 1))
        done
    fi
    
    # Move config files (excluding whitelisted root configs)
    for config in command_history.json command_shortcuts.json command_favorites.json dataset_config.json; do
        if [ -f "$config" ]; then
            mv "$config" Config/ 2>/dev/null && organized_count=$((organized_count + 1))
        fi
    done
    
    # Move any other loose .json files (excluding whitelist)
    for json_file in *.json; do
        if [ -f "$json_file" ]; then
            local is_whitelisted=false
            for wl in "${whitelist[@]}"; do
                if [ "$json_file" = "$wl" ]; then
                    is_whitelisted=true
                    break
                fi
            done
            if [ "$is_whitelisted" = false ]; then
                mv "$json_file" Config/ 2>/dev/null && organized_count=$((organized_count + 1))
            fi
        fi
    done
    
    # Move PCAP files
    if ls *.pcap 1> /dev/null 2>&1; then
        for pcap in *.pcap; do
            [ -f "$pcap" ] && mv "$pcap" Captures/ 2>/dev/null && organized_count=$((organized_count + 1))
        done
    fi
    
    # Move any loose utility .py files (excluding whitelist and specific patterns)
    for py_file in *.py; do
        if [ -f "$py_file" ]; then
            local is_whitelisted=false
            for wl in "${whitelist[@]}"; do
                if [ "$py_file" = "$wl" ]; then
                    is_whitelisted=true
                    break
                fi
            done
            # Also skip if it matches known script patterns
            case "$py_file" in
                secids_main.py|system_integrator.py|__init__.py)
                    is_whitelisted=true
                    ;;
            esac
            if [ "$is_whitelisted" = false ]; then
                mv "$py_file" Scripts/ 2>/dev/null && organized_count=$((organized_count + 1))
            fi
        fi
    done
    
    # Move any loose .txt files (excluding requirements.txt)
    for txt_file in *.txt; do
        if [ -f "$txt_file" ] && [ "$txt_file" != "requirements.txt" ]; then
            mv "$txt_file" Config/ 2>/dev/null && organized_count=$((organized_count + 1))
        fi
    done
    
    echo "$organized_count"
    return 0
}

export -f organize_root_files

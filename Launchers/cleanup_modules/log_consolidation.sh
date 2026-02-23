#!/bin/bash
# Cleanup Module: Log Consolidation
# Merges duplicate log directories

consolidate_logs() {
    local project_dir="$1"
    local count=0
    
    cd "$project_dir" || return 1
    
    if [ -d "logs" ]; then
        mkdir -p "Logs"
        
        # Move files from logs/ to Logs/
        if ls logs/*.log 1> /dev/null 2>&1; then
            mv logs/*.log Logs/ 2>/dev/null
            count=$(ls -1 Logs/*.log 2>/dev/null | wc -l)
        fi
        
        # Remove empty logs/ directory
        if [ -d "logs" ] && [ -z "$(ls -A logs)" ]; then
            rmdir logs
        fi
    fi
    
    echo "$count"
    return 0
}

export -f consolidate_logs

#!/bin/bash
# Cleanup Module: Detection Results
# Organizes detection results from SecIDS-CNN/ to Results/

organize_detection_results() {
    local project_dir="$1"
    local result_count=0
    
    cd "$project_dir" || return 1
    
    # Ensure Results folder exists
    mkdir -p "Results"
    
    # Move detection results from SecIDS-CNN/ to Results/
    if [ -d "SecIDS-CNN" ]; then
        if ls SecIDS-CNN/*detection_results*.csv 1> /dev/null 2>&1; then
            mv SecIDS-CNN/*detection_results*.csv "Results/" 2>/dev/null
            result_count=$((result_count + $(ls -1 Results/*detection_results*.csv 2>/dev/null | wc -l)))
        fi
        
        if ls SecIDS-CNN/*_report_*.json 1> /dev/null 2>&1; then
            mv SecIDS-CNN/*_report_*.json "Results/" 2>/dev/null
            result_count=$((result_count + $(ls -1 Results/*_report_*.json 2>/dev/null | wc -l)))
        fi
    fi
    
    # Move markdown reports from Results/ to Reports/
    if [ -d "Results" ] && ls Results/*.md 1> /dev/null 2>&1; then
        mkdir -p "Reports"
        mv Results/*.md "Reports/" 2>/dev/null
    fi
    
    echo "$result_count"
    return 0
}

export -f organize_detection_results

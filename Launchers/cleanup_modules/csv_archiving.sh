#!/bin/bash
# Cleanup Module: CSV Archive
# Archives CSV files to proper locations

archive_csv_files() {
    local project_dir="$1"
    local archived_count=0
    
    cd "$project_dir" || return 1
    
    # Move root CSVs to Archives
    if ls *.csv 1> /dev/null 2>&1; then
        for csv in *.csv; do
            if [ -f "$csv" ]; then
                mv "$csv" "Archives/" 2>/dev/null && archived_count=$((archived_count + 1))
            fi
        done
    fi
    
    echo "$archived_count"
    return 0
}

export -f archive_csv_files

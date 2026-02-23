#!/bin/bash
# Project Cleanup & Organization Script
# Automatically maintains proper file structure
# Updated: 2026-01-31

PROJECT_DIR="/home/kali/Documents/Code/SECIDS-CNN"
cd "$PROJECT_DIR" || exit 1

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Progress bar function
show_progress() {
    local current=$1
    local total=$2
    local task_name=$3
    local percent=$((current * 100 / total))
    local filled=$((percent / 2))
    local empty=$((50 - filled))
    
    printf "\r${CYAN}[%-50s]${NC} %3d%% - %s" \
        "$(printf '#%.0s' $(seq 1 $filled))$(printf ' %.0s' $(seq 1 $empty))" \
        "$percent" \
        "$task_name"
}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Project Cleanup & Organization (Enhanced)          ║${NC}"
echo -e "${BLUE}║         Includes Redundancy Detection & Removal             ║${NC}"
echo -e "${BLUE}║         With Progress Tracking & Percentage Display         ║${NC}"
echo -e "${BLUE}║                   Updated 2026-01-31                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Total tasks for progress calculation
TOTAL_TASKS=12
CURRENT_TASK=0

# Flag for upgrade mode
UPGRADE_MODE=false
if [ "$1" = "--upgrade" ] || [ "$1" = "-u" ]; then
    UPGRADE_MODE=true
    echo -e "${CYAN}🔄 Running in UPGRADE MODE${NC}"
    echo
fi

# Counters
moved_count=0
removed_count=0
organized_count=0
archived_count=0
consolidated_count=0
pycache_removed=0
pyc_removed=0
duplicates_removed=0

# 0. Create organizational folders if they don't exist
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Creating folder structure"
mkdir -p Root Reports Scripts Tools Launchers Models Logs Config Stress_Test_Results Results Archives Captures Device_Profile UI TrashDump Countermeasures
echo -e "\n  ${GREEN}✓${NC} All organizational folders exist (including Root/)"
echo

# 1. Merge duplicate log directories
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Consolidating log directories"
if [ -d "logs" ]; then
    mkdir -p "Logs"
    
    # Move files from logs/ to Logs/
    if ls logs/*.log 1> /dev/null 2>&1; then
        mv logs/*.log Logs/ 2>/dev/null
        count=$(ls -1 Logs/*.log 2>/dev/null | wc -l)
        echo -e "\n  ${GREEN}✓${NC} Merged $count log files from logs/ to Logs/"
    fi
    
    # Remove empty logs/ directory
    if [ -d "logs" ] && [ -z "$(ls -A logs)" ]; then
        rmdir logs
        echo -e "  ${GREEN}✓${NC} Removed empty logs/ directory"
    fi
else
    echo -e "\n  ${GREEN}✓${NC} No duplicate log directory found"
fi
echo

# Run automated file organization script
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Running file organization"
if [ -f "Scripts/organize_files.py" ]; then
    # Use virtual environment Python if available
    if [ -f ".venv_test/bin/python" ]; then
        .venv_test/bin/python Scripts/organize_files.py
    else
        python3 Scripts/organize_files.py
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} File organization and redundancy cleanup complete"
    else
        echo -e "  ${RED}✗${NC} File organization encountered errors"
    fi
else
    echo -e "  ${YELLOW}!${NC} organize_files.py not found, skipping automated organization"
fi

echo

# 2. Organize loose files in root directory
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Organizing remaining root files"
echo

# Move report files
if ls *_REPORT.md 1> /dev/null 2>&1; then
    for md in *_REPORT.md; do
        if [ -f "$md" ] && [ "$md" != "Master-Manual.md" ]; then
            mv "$md" Reports/
            echo -e "  ${GREEN}✓${NC} Moved $md to Reports/"
            organized_count=$((organized_count + 1))
        fi
    done
fi

# Move utility scripts to Scripts/
for script in analyze_threat_origins.py test_enhanced_model.py verify_packages.py; do
    if [ -f "$script" ]; then
        mv "$script" Scripts/
        echo -e "  ${GREEN}✓${NC} Moved $script to Scripts/"
        organized_count=$((organized_count + 1))
    fi
done

# Move main tools to Tools/
for tool in command_library.py csv_workflow_manager.py pipeline_orchestrator.py; do
    if [ -f "$tool" ]; then
        mv "$tool" Tools/
        echo -e "  ${GREEN}✓${NC} Moved $tool to Tools/"
        organized_count=$((organized_count + 1))
    fi
done

# Move launcher scripts to Launchers/
for launcher in csv_workflow.sh project_cleanup.sh QUICK_START.sh secids.sh; do
    if [ -f "$launcher" ]; then
        mv "$launcher" Launchers/
        echo -e "  ${GREEN}✓${NC} Moved $launcher to Launchers/"
        organized_count=$((organized_count + 1))
    fi
done

# Move model files
if ls *.h5 1> /dev/null 2>&1; then
    for model in *.h5; do
        if [ -f "$model" ]; then
            mv "$model" Models/
            echo -e "  ${GREEN}✓${NC} Moved $model to Models/"
            organized_count=$((organized_count + 1))
        fi
    done
fi

if ls *.pkl 1> /dev/null 2>&1; then
    for model in *.pkl; do
        if [ -f "$model" ]; then
            mv "$model" Models/
            echo -e "  ${GREEN}✓${NC} Moved $model to Models/"
            organized_count=$((organized_count + 1))
        fi
    done
fi

# Move log files
if ls *.log 1> /dev/null 2>&1; then
    for log in *.log; do
        if [ -f "$log" ]; then
            mv "$log" Logs/
            echo -e "  ${GREEN}✓${NC} Moved $log to Logs/"
            organized_count=$((organized_count + 1))
        fi
    done
fi

# Move config files
for config in command_history.json command_shortcuts.json command_favorites.json dataset_config.json; do
    if [ -f "$config" ]; then
        mv "$config" Config/
        echo -e "  ${GREEN}✓${NC} Moved $config to Config/"
        organized_count=$((organized_count + 1))
    fi
done

# Ensure .env is in Config folder (correct location)
if [ -f "Config/.env" ]; then
    echo -e "  ${GREEN}✓${NC} .env file present in Config/ (correct location)"
else
    # Check if .env is in root (old location) and move it
    if [ -f ".env" ]; then
        mv ".env" "Config/.env"
        echo -e "  ${GREEN}✓${NC} Moved .env from root to Config/ (correct location)"
    else
        echo -e "  ${CYAN}ℹ${NC} .env file not found (TensorFlow config may be needed)"
    fi
fi

# Move PCAP files
if ls *.pcap 1> /dev/null 2>&1; then
    for pcap in *.pcap; do
        if [ -f "$pcap" ]; then
            mv "$pcap" Captures/
            echo -e "  ${GREEN}✓${NC} Moved $pcap to Captures/"
            organized_count=$((organized_count + 1))
        fi
    done
fi

temp_organized=$organized_count
organized_count=0

if [ $temp_organized -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Root directory already organized"
fi

# 3. Move stress test reports to Stress_Test_Results/
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Organizing stress test reports"
echo

if ls stress_test_report_*.json 1> /dev/null 2>&1; then
    mv stress_test_report_*.json Stress_Test_Test_Results/ 2>/dev/null
    count=$(ls -1 Stress_Test_Results/stress_test_report_*.json 2>/dev/null | wc -l)
    echo -e "  ${GREEN}✓${NC} Moved $count stress test reports"
    moved_count=$((moved_count + count))
else
    echo -e "  ${GREEN}✓${NC} No stress test reports to move"
fi
echo

# 4. Organize detection results from SecIDS-CNN/ to Results/
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Organizing detection results"
echo

# Ensure Results folder exists for detection output
if [ ! -d "Results" ]; then
    mkdir -p "Results"
    echo -e "  ${GREEN}✓${NC} Created Results folder for detection output"
fi

# Move detection results from SecIDS-CNN/ to Results/
if [ -d "SecIDS-CNN" ]; then
    result_count=0
    
    if ls SecIDS-CNN/*detection_results*.csv 1> /dev/null 2>&1; then
        mv SecIDS-CNN/*detection_results*.csv "Results/" 2>/dev/null
        result_count=$((result_count + $(ls -1 Results/*detection_results*.csv 2>/dev/null | wc -l)))
    fi
    
    if ls SecIDS-CNN/*_report_*.json 1> /dev/null 2>&1; then
        mv SecIDS-CNN/*_report_*.json "Results/" 2>/dev/null
        result_count=$((result_count + $(ls -1 Results/*_report_*.json 2>/dev/null | wc -l)))
    fi
    
    if [ $result_count -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} Moved $result_count detection result files to Results/"
        organized_count=$((organized_count + result_count))
    else
        echo -e "  ${GREEN}✓${NC} No detection results to move"
    fi
fi

# Move markdown reports from Results/ to Reports/
report_count=0
if [ -d "Results" ] && ls Results/*.md 1> /dev/null 2>&1; then
    mkdir -p "Reports"
    mv Results/*.md "Reports/" 2>/dev/null
    report_count=$(ls -1 Reports/*_report_*.md 2>/dev/null | wc -l)
    if [ $report_count -gt 0 ]; then
        echo -e "  ${GREEN}✓${NC} Moved $report_count markdown reports from Results/ to Reports/"
        organized_count=$((organized_count + report_count))
    fi
fi
echo

# 5. Archive old CSV files
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Archiving CSV files"
echo

# Move root CSVs to Archives
if ls *.csv 1> /dev/null 2>&1; then
    for csv in *.csv; do
        if [ -f "$csv" ]; then
            mv "$csv" "Archives/"
            echo -e "  ${GREEN}✓${NC} Archived $csv"
            archived_count=$((archived_count + 1))
        fi
    done
else
    echo -e "  ${GREEN}✓${NC} No CSV files in root directory to archive"
fi

# Check for misplaced CSVs
csv_count=$(find . -maxdepth 1 -name "*.csv" 2>/dev/null | wc -l)
if [ $csv_count -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} All CSV files properly organized"
fi
echo

# 6. Handle README files and consolidate to Master-Manual
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Managing documentation"
echo

# Function to consolidate markdown to Master-Manual
consolidate_to_master() {
    local md_file="$1"
    local title=$(head -n 1 "$md_file" 2>/dev/null | sed 's/#//g' | xargs)
    
    if [ -z "$title" ]; then
        return 1
    fi
    
    # Check if title already exists in Master-Manual.md
    if grep -q "$title" Master-Manual.md 2>/dev/null; then
        return 1
    fi
    
    # Check if this is a report/documentation file
    if echo "$md_file" | grep -iE "REPORT|SUMMARY|UPDATE|ENHANCEMENT|FIX|INTEGRATION" > /dev/null; then
        # Append to Master-Manual.md
        {
            echo ""
            echo ""
            echo "---"
            echo ""
            echo "# $title"
            echo "*Consolidated from: $(basename "$md_file")*"
            echo "*Date: $(date +%Y-%m-%d)*"
            echo ""
            tail -n +2 "$md_file"  # Skip first line (title)
            echo ""
        } >> Master-Manual.md
        
        echo -e "  ${CYAN}📝${NC} Consolidated $(basename "$md_file") to Master-Manual.md"
        consolidated_count=$((consolidated_count + 1))
        return 0
    fi
    
    return 1
}

# Move standalone READMEs and reports to Reports/ (after consolidating)
readme_moved=0

# Check for all markdown files in root (except Master-Manual.md and README.md)
if ls *.md 1> /dev/null 2>&1; then
    for md_file in *.md; do
        if [ -f "$md_file" ] && [ "$md_file" != "Master-Manual.md" ] && [ "$md_file" != "README.md" ]; then
            # Try to consolidate first
            consolidate_to_master "$md_file"
            
            # Then move to Reports/
            if [ -f "$md_file" ]; then
                mv "$md_file" Reports/
                echo -e "  ${GREEN}✓${NC} Moved $md_file to Reports/"
                readme_moved=1
            fi
        fi
    done
fi

if [ $readme_moved -eq 0 ] && [ $consolidated_count -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} All documentation files properly organized"
elif [ $consolidated_count -gt 0 ]; then
    echo -e "  ${CYAN}ℹ${NC} Consolidated $consolidated_count files to Master-Manual.md"
fi

# 7. Check and remove redundant README files
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Checking redundant documentation"
echo

# Check if Master-Manual.md has the new content
if grep -q "CSV Workflow Manager" Master-Manual.md && \
   grep -q "TrashDump - Automatic Cleanup" Master-Manual.md && \
   grep -q "Countermeasures System" Master-Manual.md; then
    
    echo -e "  ${GREEN}✓${NC} Master-Manual.md contains all documentation"
    
    # Remove redundant READMEs from subsystem folders
    if [ -f "csv_workflow_manager_README.md" ]; then
        rm "csv_workflow_manager_README.md"
        echo -e "  ${GREEN}✓${NC} Removed csv_workflow_manager_README.md"
        removed_count=$((removed_count + 1))
    fi
    
    if [ -f "TrashDump/README.md" ]; then
        rm "TrashDump/README.md"
        echo -e "  ${GREEN}✓${NC} Removed TrashDump/README.md"
        removed_count=$((removed_count + 1))
    fi
    
    if [ -f "Countermeasures/README.md" ]; then
        rm "Countermeasures/README.md"
        echo -e "  ${GREEN}✓${NC} Removed Countermeasures/README.md"
        removed_count=$((removed_count + 1))
    fi
    
    if [ $removed_count -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} No redundant files to remove"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Master-Manual.md not fully updated, keeping README files"
fi
echo

# Verify directory structure
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Verifying directory structure"
echo

# Check key directories exist
dirs=(
    "Root"
    "Reports"
    "Scripts"
    "Tools"
    "Launchers"
    "Models"
    "Logs"
    "Config"
    "Stress_Test_Results"
    "Results"
    "Archives"
    "Captures"
    "SecIDS-CNN/datasets"
    "TrashDump"
    "Countermeasures"
    "Device_Profile"
    "UI"
)

all_exist=true
for dir in "${dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "  ${RED}✗${NC} Missing directory: $dir"
        all_exist=false
    fi
done

if $all_exist; then
    echo -e "  ${GREEN}✓${NC} All required directories exist"
fi
echo

# 8. Validate file locations
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Validating file locations"
echo

# Check for misplaced files
validation_issues=0

# Check datasets folder for unexpected file types
if [ -d "SecIDS-CNN/datasets" ]; then
    # Count non-CSV, non-allowed-MD files
    for file_type in "*.txt" "*.log" "*.json"; do
        if ls SecIDS-CNN/datasets/$file_type 1> /dev/null 2>&1; then
            echo -e "  ${YELLOW}⚠${NC} Unexpected file type in datasets/: $file_type"
            validation_issues=$((validation_issues + 1))
        fi
    done
    
    # Check for markdown files (but allow reference docs)
    if ls SecIDS-CNN/datasets/*.md 1> /dev/null 2>&1; then
        for md_file in SecIDS-CNN/datasets/*.md; do
            if [ -f "$md_file" ]; then
                basename=$(basename "$md_file")
                # Allow specific reference documents
                if [[ "$basename" != "IP_SOURCE_QUICK_REF.md" && "$basename" != "MD_NAMING_CONVENTION.md" && "$basename" != "DATASET_README.md" && "$basename" != "COLUMNS.md" ]]; then
                    echo -e "  ${YELLOW}⚠${NC} Unexpected markdown in datasets/: $basename"
                    validation_issues=$((validation_issues + 1))
                fi
            fi
        done
    fi
fi

# Check Results folder for unexpected file types
if [ -d "Results" ]; then
    for file_type in "*.txt" "*.log" "*.py"; do
        if ls Results/$file_type 1> /dev/null 2>&1; then
            echo -e "  ${YELLOW}⚠${NC} Unexpected file type in Results/: $file_type"
            validation_issues=$((validation_issues + 1))
        fi
    done
fi

if [ $validation_issues -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} All files are in their correct locations"
    echo -e "  ${CYAN}ℹ${NC} Note: Dataset reference files (*.md) are intentionally kept in datasets/"
else
    echo -e "  ${YELLOW}⚠${NC} Found $validation_issues potential file location issues"
fi
echo

# 9. Run debug scan on Python files
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Running Python debug scan"
echo
cd "$PROJECT_DIR"
python_errors=0
python_errors=$(find . -name "*.py" ! -path "./.venv/*" ! -path "./.venv_test/*" ! -path "./TrashDump/*" ! -path "./__pycache__/*" -exec python -m py_compile {} \; 2>&1 | grep -c "SyntaxError\|IndentationError" || true)

if [ $python_errors -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} All Python files compile successfully"
else
    echo -e "  ${YELLOW}⚠${NC} Found $python_errors Python files with errors"
    echo -e "  ${CYAN}💡${NC} Run 'python Scripts/production_debug_scan.py' for detailed analysis"
fi

# 10. System Upgrade (if requested)
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "System upgrade check"
echo

if [ "$UPGRADE_MODE" = true ]; then
    echo -e "  ${CYAN}🔄${NC} Running system upgrade..."
    
    # Check if upgrade script exists
    if [ -f "Scripts/system_upgrade.py" ]; then
        # Use virtual environment Python if available
        if [ -f ".venv_test/bin/python" ]; then
            PYTHON_CMD=".venv_test/bin/python"
        else
            PYTHON_CMD="python3"
        fi
        
        # Run upgrade
        $PYTHON_CMD Scripts/system_upgrade.py
        
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓${NC} System upgrade completed successfully"
        else
            echo -e "  ${YELLOW}⚠${NC} System upgrade completed with warnings"
        fi
        
        # Run verification
        if [ -f "Scripts/verify_upgrade.sh" ]; then
            echo -e "  ${CYAN}ℹ${NC} Running post-upgrade verification..."
            bash Scripts/verify_upgrade.sh
        fi
    else
        echo -e "  ${RED}✗${NC} Upgrade script not found: Scripts/system_upgrade.py"
        echo -e "  ${CYAN}💡${NC} Skipping upgrade"
    fi
else
    echo -e "  ${GREEN}✓${NC} Upgrade not requested (use --upgrade flag to run)"
    echo -e "  ${CYAN}💡${NC} Run: ./Launchers/project_cleanup.sh --upgrade"
fi
echo

# Summary
echo
CURRENT_TASK=$((CURRENT_TASK + 1))
show_progress $CURRENT_TASK $TOTAL_TASKS "Generating summary report"
echo
echo
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Cleanup Summary:${NC}"
echo -e "  Stress test reports moved:  $moved_count"
echo -e "  Files organized:             $temp_organized"
echo -e "  Detection results moved:     $organized_count"
echo -e "  CSV files archived:          $archived_count"
echo -e "  Files consolidated to Master: $consolidated_count"
echo -e "  Redundant files removed:     $removed_count"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo
echo -e "${GREEN}✓ Project cleanup complete! (100%)${NC}"
if [ $consolidated_count -gt 0 ]; then
    echo -e "${CYAN}📝 $consolidated_count file(s) consolidated to Master-Manual.md${NC}"
fi
echo -e "${CYAN}ℹ Run 'python3 Scripts/organize_files.py' for detailed organization${NC}"
echo

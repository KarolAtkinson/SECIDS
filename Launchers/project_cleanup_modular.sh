#!/bin/bash
# Project Cleanup & Organization Script - Modular Version
# Efficiently maintains proper file structure using sub-routines
# Updated: 2026-01-31 - Resource-Optimized

PROJECT_DIR="/home/kali/Documents/Code/SECIDS-CNN"
MODULES_DIR="$PROJECT_DIR/Launchers/cleanup_modules"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

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

# Load cleanup modules
load_modules() {
    if [ -d "$MODULES_DIR" ]; then
        for module in "$MODULES_DIR"/*.sh; do
            [ -f "$module" ] && source "$module"
        done
        return 0
    else
        echo -e "${RED}Error: Cleanup modules not found at $MODULES_DIR${NC}"
        return 1
    fi
}

# Parse command line arguments
UPGRADE_MODE=false
QUICK_MODE=false
FULL_MODE=true
SELECTED_TASKS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --upgrade|-u)
            UPGRADE_MODE=true
            shift
            ;;
        --quick|-q)
            QUICK_MODE=true
            # FULL_MODE stays true for quick mode
            shift
            ;;
        --task|-t)
            SELECTED_TASKS+=("$2")
            FULL_MODE=false  # Only disable full mode for specific tasks
            shift 2
            ;;
        --help|-h)
            cat << EOF
Usage: $0 [OPTIONS]

Options:
  --upgrade, -u        Run system upgrade after cleanup
  --quick, -q          Quick cleanup (essential tasks only)
  --task, -t <name>    Run specific task(s) only
  --help, -h           Show this help message

Available Tasks:
  directories          Create/verify directory structure
  logs                 Consolidate log directories
  organize             Organize root files
  python-organize      Run Python organize_files.py script
  csv                  Archive CSV files
  results              Organize detection results
  python-check         Validate Python syntax (quick)
  upgrade              Run system upgrade

Examples:
  $0                           # Full cleanup
  $0 --quick                   # Quick cleanup
  $0 --upgrade                 # Full cleanup + upgrade
  $0 --task directories        # Only check directories
  $0 --task organize --task csv  # Only organize files and archive CSVs

EOF
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main execution
main() {
    cd "$PROJECT_DIR" || exit 1
    
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║      Project Cleanup & Organization (Modular v2.0)         ║${NC}"
    echo -e "${BLUE}║         Resource-Optimized with Sub-Routines                ║${NC}"
    echo -e "${BLUE}║                Updated 2026-01-31                           ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    if [ "$UPGRADE_MODE" = true ]; then
        echo -e "${CYAN}🔄 Running in UPGRADE MODE${NC}"
    fi
    
    if [ "$QUICK_MODE" = true ]; then
        echo -e "${CYAN}⚡ Running in QUICK MODE${NC}"
    fi
    echo
    
    # Load cleanup modules
    if ! load_modules; then
        echo -e "${RED}Failed to load cleanup modules. Exiting.${NC}"
        exit 1
    fi
    
    # Counters
    local moved_count=0
    local organized_count=0
    local archived_count=0
    local result_count=0
    local python_errors=0
    
    # Define tasks
    declare -A tasks
    tasks[directories]="Create/verify directories"
    tasks[logs]="Consolidate logs"
    tasks[organize]="Organize root files"
    tasks[python-organize]="Run Python organizer"
    tasks[csv]="Archive CSV files"
    tasks[results]="Organize detection results"
    tasks[python-check]="Python syntax check"
    
    if [ "$UPGRADE_MODE" = true ]; then
        tasks[upgrade]="System upgrade"
    fi
    
    # Determine which tasks to run
    local tasks_to_run=()
    
    if [ "$FULL_MODE" = true ]; then
        if [ "$QUICK_MODE" = true ]; then
            # Quick mode: essential tasks only
            tasks_to_run=("directories" "organize" "csv")
        else
            # Full mode: all tasks except upgrade (unless specified)
            tasks_to_run=("directories" "logs" "organize" "python-organize" "csv" "results" "python-check")
            if [ "$UPGRADE_MODE" = true ]; then
                tasks_to_run+=("upgrade")
            fi
        fi
    else
        # Specific tasks mode
        tasks_to_run=("${SELECTED_TASKS[@]}")
    fi
    
    local total_tasks=${#tasks_to_run[@]}
    local current_task=0
    
    # Safety check
    if [ $total_tasks -eq 0 ]; then
        echo -e "${YELLOW}⚠ No tasks to run${NC}"
        exit 0
    fi
    
    # Execute tasks
    for task in "${tasks_to_run[@]}"; do
        current_task=$((current_task + 1))
        show_progress $current_task $total_tasks "${tasks[$task]:-$task}"
        
        case $task in
            directories)
                if create_directory_structure "$PROJECT_DIR"; then
                    echo -e "\n  ${GREEN}✓${NC} All organizational folders exist"
                else
                    echo -e "\n  ${YELLOW}⚠${NC} Some directories could not be created"
                fi
                ;;
                
            logs)
                moved_count=$(consolidate_logs "$PROJECT_DIR")
                if [ $moved_count -gt 0 ]; then
                    echo -e "\n  ${GREEN}✓${NC} Merged $moved_count log files"
                else
                    echo -e "\n  ${GREEN}✓${NC} No duplicate log directory found"
                fi
                ;;
                
            organize)
                organized_count=$(organize_root_files "$PROJECT_DIR")
                if [ $organized_count -gt 0 ]; then
                    echo -e "\n  ${GREEN}✓${NC} Organized $organized_count files"
                else
                    echo -e "\n  ${GREEN}✓${NC} Root directory already organized"
                fi
                ;;
                
            python-organize)
                if [ -f "$PROJECT_DIR/Scripts/organize_files.py" ]; then
                    echo -e "\n  ${CYAN}Running Python file organizer...${NC}"
                    if [ -f "$PROJECT_DIR/.venv_test/bin/python" ]; then
                        "$PROJECT_DIR/.venv_test/bin/python" "$PROJECT_DIR/Scripts/organize_files.py" 2>/dev/null
                    else
                        python3 "$PROJECT_DIR/Scripts/organize_files.py" 2>/dev/null
                    fi
                    [ $? -eq 0 ] && echo -e "  ${GREEN}✓${NC} Python organizer complete"
                else
                    echo -e "\n  ${YELLOW}⚠${NC} organize_files.py not found"
                fi
                ;;
                
            csv)
                archived_count=$(archive_csv_files "$PROJECT_DIR")
                if [ $archived_count -gt 0 ]; then
                    echo -e "\n  ${GREEN}✓${NC} Archived $archived_count CSV files"
                else
                    echo -e "\n  ${GREEN}✓${NC} No CSV files to archive"
                fi
                ;;
                
            results)
                result_count=$(organize_detection_results "$PROJECT_DIR")
                if [ $result_count -gt 0 ]; then
                    echo -e "\n  ${GREEN}✓${NC} Organized $result_count detection results"
                else
                    echo -e "\n  ${GREEN}✓${NC} No detection results to organize"
                fi
                ;;
                
            python-check)
                python_errors=$(validate_python_syntax "$PROJECT_DIR" 20)
                if [ $python_errors -eq 0 ]; then
                    echo -e "\n  ${GREEN}✓${NC} Python syntax check passed (20 files)"
                else
                    echo -e "\n  ${YELLOW}⚠${NC} Found $python_errors files with syntax errors"
                fi
                ;;
                
            upgrade)
                echo -e "\n  ${CYAN}🔄${NC} Running system upgrade..."
                if [ -f "$PROJECT_DIR/Scripts/system_upgrade.py" ]; then
                    if [ -f "$PROJECT_DIR/.venv_test/bin/python" ]; then
                        PYTHON_CMD="$PROJECT_DIR/.venv_test/bin/python"
                    else
                        PYTHON_CMD="python3"
                    fi
                    
                    $PYTHON_CMD "$PROJECT_DIR/Scripts/system_upgrade.py"
                    
                    if [ $? -eq 0 ]; then
                        echo -e "  ${GREEN}✓${NC} System upgrade completed"
                    else
                        echo -e "  ${YELLOW}⚠${NC} System upgrade completed with warnings"
                    fi
                else
                    echo -e "  ${RED}✗${NC} Upgrade script not found"
                fi
                ;;
                
            *)
                echo -e "\n  ${RED}✗${NC} Unknown task: $task"
                ;;
        esac
        echo
    done
    
    # Summary
    show_progress $total_tasks $total_tasks "Generating summary"
    echo
    echo
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Cleanup Summary:${NC}"
    echo -e "  Tasks executed:              $total_tasks"
    echo -e "  Log files moved:             $moved_count"
    echo -e "  Root files organized:        $organized_count"
    echo -e "  CSV files archived:          $archived_count"
    echo -e "  Detection results organized: $result_count"
    if [ $python_errors -gt 0 ]; then
        echo -e "  Python syntax errors:        ${YELLOW}$python_errors${NC}"
    fi
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${GREEN}✓ Project cleanup complete! (100%)${NC}"
    echo
    
    if [ "$QUICK_MODE" = false ] && [ ${#SELECTED_TASKS[@]} -eq 0 ]; then
        echo -e "${CYAN}💡 Tip: Use --quick for faster cleanup of essential tasks${NC}"
        echo -e "${CYAN}💡 Tip: Use --task <name> to run specific tasks only${NC}"
    fi
    echo
}

# Run main function
main "$@"

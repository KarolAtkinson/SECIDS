#!/bin/bash
# CSV Workflow Manager Quick Launcher
# Usage: ./csv_workflow.sh [action] [options]

PROJECT_DIR="/home/kali/Documents/Code/SECIDS-CNN"
MANAGER="$PROJECT_DIR/csv_workflow_manager.py"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         CSV Workflow Manager - Quick Launcher              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Default action
ACTION="${1:-status}"
DRY_RUN="${2:-}"

# Navigate to project
cd "$PROJECT_DIR" || exit 1

# Execute based on action
case "$ACTION" in
    status|s)
        echo -e "${BLUE}📊 Checking CSV workflow status...${NC}\n"
        python3 "$MANAGER" --action status
        ;;
    
    full|f)
        if [ "$DRY_RUN" == "--dry-run" ] || [ "$DRY_RUN" == "-d" ]; then
            echo -e "${YELLOW}🔍 Running FULL workflow (dry-run)...${NC}\n"
            python3 "$MANAGER" --action full --dry-run
        else
            echo -e "${GREEN}🚀 Running FULL workflow...${NC}\n"
            python3 "$MANAGER" --action full
        fi
        ;;
    
    organize|o)
        if [ "$DRY_RUN" == "--dry-run" ] || [ "$DRY_RUN" == "-d" ]; then
            echo -e "${YELLOW}🔍 Organizing CSVs (dry-run)...${NC}\n"
            python3 "$MANAGER" --action organize --dry-run
        else
            echo -e "${GREEN}📁 Organizing CSV files...${NC}\n"
            python3 "$MANAGER" --action organize
        fi
        ;;
    
    train|t)
        MODEL="${3:-unified}"
        if [ "$DRY_RUN" == "--dry-run" ] || [ "$DRY_RUN" == "-d" ]; then
            echo -e "${YELLOW}🔍 Training models (dry-run)...${NC}\n"
            python3 "$MANAGER" --action train --model "$MODEL" --dry-run
        else
            echo -e "${GREEN}🧠 Training models ($MODEL)...${NC}\n"
            python3 "$MANAGER" --action train --model "$MODEL"
        fi
        ;;
    
    transfer|x)
        if [ "$DRY_RUN" == "--dry-run" ] || [ "$DRY_RUN" == "-d" ]; then
            echo -e "${YELLOW}🔍 Transferring results (dry-run)...${NC}\n"
            python3 "$MANAGER" --action transfer --dry-run
        else
            echo -e "${GREEN}📤 Transferring results to datasets...${NC}\n"
            python3 "$MANAGER" --action transfer
        fi
        ;;
    
    detect|d)
        if [ "$DRY_RUN" == "--dry-run" ] || [ "$DRY_RUN" == "-d" ]; then
            echo -e "${YELLOW}🔍 Running detection (dry-run)...${NC}\n"
            python3 "$MANAGER" --action detect --dry-run
        else
            echo -e "${GREEN}🔍 Running improved detection...${NC}\n"
            python3 "$MANAGER" --action detect
        fi
        ;;
    
    help|h|--help|-h)
        echo -e "${GREEN}CSV Workflow Manager - Usage${NC}\n"
        echo "Quick commands:"
        echo "  ./csv_workflow.sh status          - Show workflow status"
        echo "  ./csv_workflow.sh full             - Run full workflow"
        echo "  ./csv_workflow.sh full --dry-run   - Preview full workflow"
        echo "  ./csv_workflow.sh organize         - Organize CSV files"
        echo "  ./csv_workflow.sh train            - Train models"
        echo "  ./csv_workflow.sh transfer         - Transfer results"
        echo "  ./csv_workflow.sh detect           - Run improved detection"
        echo ""
        echo "Shortcuts:"
        echo "  s  = status"
        echo "  f  = full"
        echo "  o  = organize"
        echo "  t  = train"
        echo "  x  = transfer"
        echo "  d  = detect"
        echo ""
        echo "Options:"
        echo "  --dry-run, -d  - Preview without making changes"
        echo ""
        echo "Examples:"
        echo "  ./csv_workflow.sh s              # Status"
        echo "  ./csv_workflow.sh f -d           # Full dry-run"
        echo "  ./csv_workflow.sh t unified      # Train unified model"
        ;;
    
    *)
        echo -e "${RED}❌ Unknown action: $ACTION${NC}\n"
        echo "Use './csv_workflow.sh help' for usage information"
        exit 1
        ;;
esac

echo
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

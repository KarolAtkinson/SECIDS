#!/bin/bash
# Setup Auto-Update for GitHub Repository
# This script configures automatic Git synchronization

PROJECT_DIR="/home/kali/Documents/Code/SECIDS-CNN"
cd "$PROJECT_DIR" || exit 1

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         GitHub Auto-Update Setup                           ║${NC}"
echo -e "${BLUE}║         SECIDS-CNN Repository Sync                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Check if Git is configured
if ! git remote -v &>/dev/null; then
    echo -e "${RED}ERROR: No Git repository found!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Git repository detected${NC}"
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
echo -e "  Remote: ${CYAN}$REMOTE_URL${NC}"
echo

# Test the Git sync script
echo -e "${BLUE}Testing Git auto-sync script...${NC}"
python3 Auto_Update/git_auto_sync.py --status

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Git auto-sync script is working${NC}\n"
else
    echo -e "\n${RED}✗ Git auto-sync script failed${NC}\n"
    exit 1
fi

# Ask user for sync interval
echo -e "${YELLOW}Select auto-sync interval:${NC}"
echo "  1) Every 6 hours (recommended)"
echo "  2) Every 12 hours"
echo "  3) Every 24 hours (daily)"
echo "  4) Every hour (frequent)"
echo "  5) Manual only (no automatic sync)"
echo
read -p "Enter choice [1-5]: " choice

case $choice in
    1) INTERVAL=6 ;;
    2) INTERVAL=12 ;;
    3) INTERVAL=24 ;;
    4) INTERVAL=1 ;;
    5) 
        echo -e "\n${YELLOW}Skipping automatic sync setup${NC}"
        echo -e "You can manually sync anytime with:"
        echo -e "  ${CYAN}python3 Auto_Update/git_auto_sync.py${NC}\n"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Update task configuration
echo -e "\n${BLUE}Updating task scheduler configuration...${NC}"
python3 << EOF
import json
from pathlib import Path

config_file = Path('Auto_Update/schedulers/task_config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

# Update git_sync interval
if 'tasks' in config and 'git_sync' in config['tasks']:
    config['tasks']['git_sync']['interval_hours'] = $INTERVAL
    config['tasks']['git_sync']['enabled'] = True
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Git sync interval set to $INTERVAL hours")
else:
    print("✗ git_sync task not found in configuration")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to update configuration${NC}"
    exit 1
fi

# Setup cron job (alternative to task scheduler)
echo -e "\n${YELLOW}Do you want to setup a cron job for automatic sync?${NC}"
echo "  (This runs independently of the task scheduler)"
read -p "Setup cron job? [y/N]: " setup_cron

if [[ "$setup_cron" =~ ^[Yy]$ ]]; then
    # Calculate cron schedule
    case $INTERVAL in
        1) CRON_SCHEDULE="0 * * * *" ;;      # Every hour
        6) CRON_SCHEDULE="0 */6 * * *" ;;    # Every 6 hours
        12) CRON_SCHEDULE="0 */12 * * *" ;;  # Every 12 hours
        24) CRON_SCHEDULE="0 2 * * *" ;;     # Daily at 2 AM
    esac
    
    CRON_CMD="cd $PROJECT_DIR && python3 Auto_Update/git_auto_sync.py >> Auto_Update/logs/git_sync_cron.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "git_auto_sync.py"; then
        echo -e "${YELLOW}Removing existing cron job...${NC}"
        crontab -l 2>/dev/null | grep -v "git_auto_sync.py" | crontab -
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_CMD") | crontab -
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Cron job installed successfully${NC}"
        echo -e "  Schedule: ${CYAN}Every $INTERVAL hour(s)${NC}"
        echo -e "  Log file: ${CYAN}Auto_Update/logs/git_sync_cron.log${NC}"
    else
        echo -e "${RED}✗ Failed to install cron job${NC}"
    fi
fi

# Ask if user wants to run first sync now
echo -e "\n${YELLOW}Do you want to run the first sync now?${NC}"
echo "  (This will pull from and push to GitHub)"
read -p "Run sync now? [y/N]: " run_now

if [[ "$run_now" =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Running Git sync...${NC}\n"
    python3 Auto_Update/git_auto_sync.py
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}✓ Sync completed successfully${NC}"
    else
        echo -e "\n${YELLOW}⚠ Sync completed with errors (check log)${NC}"
    fi
fi

# Display summary
echo
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Setup Complete!                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "${GREEN}Auto-sync is now configured!${NC}"
echo
echo -e "${CYAN}Manual Commands:${NC}"
echo -e "  Status:     python3 Auto_Update/git_auto_sync.py --status"
echo -e "  Sync now:   python3 Auto_Update/git_auto_sync.py"
echo -e "  Pull only:  python3 Auto_Update/git_auto_sync.py --pull-only"
echo -e "  Push only:  python3 Auto_Update/git_auto_sync.py --push-only"
echo -e "  Dry run:    python3 Auto_Update/git_auto_sync.py --dry-run"
echo
echo -e "${CYAN}Task Scheduler:${NC}"
echo -e "  Start:      python3 Auto_Update/task_scheduler.py --daemon"
echo -e "  Run once:   python3 Auto_Update/task_scheduler.py --run git_sync"
echo -e "  Config:     Auto_Update/schedulers/task_config.json"
echo
echo -e "${CYAN}Logs:${NC}"
echo -e "  Sync log:   Auto_Update/logs/git_sync.log"
echo -e "  Cron log:   Auto_Update/logs/git_sync_cron.log"
echo
echo -e "${YELLOW}Note: Auto-sync runs every $INTERVAL hour(s)${NC}"
echo

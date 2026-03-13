# Auto-Update System

Automatic task scheduling and GitHub repository synchronization for SECIDS-CNN.

## Overview

The Auto-Update system provides:
- **Automatic Git Synchronization**: Regular push/pull with GitHub repository
- **Task Scheduling**: Automated execution of maintenance tasks
- **System Monitoring**: Track system health and status
- **Workflow Chart Automation**: Permanent refresh of `Reports/WORKFLOW_CHART.md`

## Quick Start

### Setup GitHub Auto-Update

```bash
bash Auto_Update/setup_git_autoupdate.sh
```

Or run non-interactive policy setup (recommended for server deployments):

```bash
python3 Auto_Update/ensure_git_policy.py --interval-hours 6
```

This enables `git_sync`, installs/updates a cron entry, and validates that the GitHub remote is private.

This interactive script will:
1. Verify Git configuration
2. Test the sync functionality
3. Set sync interval (every 1, 6, 12, or 24 hours)
4. Optional: Setup cron job for automatic execution
5. Optional: Run first sync immediately

### Manual Git Sync

```bash
# Full sync (pull then push)
python3 Auto_Update/git_auto_sync.py

# Check status only
python3 Auto_Update/git_auto_sync.py --status

# Pull changes only
python3 Auto_Update/git_auto_sync.py --pull-only

# Push changes only
python3 Auto_Update/git_auto_sync.py --push-only

# Dry run (show what would happen)
python3 Auto_Update/git_auto_sync.py --dry-run

# Custom commit message
python3 Auto_Update/git_auto_sync.py --message "Your custom message"
```

## Configuration

### Task Configuration

Edit `Auto_Update/schedulers/task_config.json`:

```json
{
  "tasks": {
    "git_sync": {
      "enabled": true,
      "interval_hours": 6,
      "script": "Auto_Update/git_auto_sync.py",
      "description": "Sync repository with GitHub"
    },
    "whitelist_update": {
      "enabled": true,
      "interval_hours": 168,
      "script": "Device_Profile/device_info/capture_device_info.py",
      "description": "Update device profile"
    },
    "workflow_chart_update": {
      "enabled": true,
      "interval_hours": 12,
      "script": "Auto_Update/monitors/update_workflow_chart.py",
      "description": "Regenerate workflow chart documentation"
    }
  }
}
```

### Task Scheduler Usage

```bash
# Run as daemon (background service)
python3 Auto_Update/task_scheduler.py --daemon

# Run specific task once
python3 Auto_Update/task_scheduler.py --run git_sync

# Regenerate workflow chart now
python3 Auto_Update/task_scheduler.py --run workflow_chart_update

# Run all tasks once
python3 Auto_Update/task_scheduler.py --run-all

# Check task status
python3 Auto_Update/task_scheduler.py --status
```

## Files and Directories

```
Auto_Update/
├── git_auto_sync.py           # Git synchronization script
├── setup_git_autoupdate.sh    # Interactive setup script
├── task_scheduler.py          # Task scheduler daemon
├── __init__.py                # Package initialization
├── logs/                      # Log files
│   ├── git_sync.log          # Git sync operation log
│   ├── git_sync_cron.log     # Cron job log (if enabled)
│   └── task_scheduler.log    # Task scheduler log
├── schedulers/                # Scheduler configuration
│   └── task_config.json      # Task definitions
└── monitors/                  # System monitoring
  ├── system_status.json    # System health status
  └── update_workflow_chart.py  # Workflow chart generator

```

## How It Works

### Git Auto-Sync

1. **Fetch**: Downloads latest changes from GitHub
2. **Pull**: Integrates remote changes with local repository (with rebase)
3. **Stage**: Adds all modified/new/deleted files
4. **Commit**: Creates commit with auto-generated or custom message
5. **Push**: Uploads commits to GitHub

Commit messages are auto-generated with format:
```
Auto-sync: 2026-02-23 15:30:00 (5 modified, 2 new)
```

### Task Scheduler

- Runs configured tasks at specified intervals
- Tracks last execution time for each task
- Logs all operations to `logs/task_scheduler.log`
- Can run as daemon or execute tasks on-demand
- Regenerates `Reports/WORKFLOW_CHART.md` on `workflow_chart_update` interval

### Workflow Chart Auto-Update

- **Output:** `Reports/WORKFLOW_CHART.md`
- **Generator:** `Auto_Update/monitors/update_workflow_chart.py`
- **Default interval:** every 12 hours
- **Privilege model:** chart file permissions are synced to match `Master-Manual.md`

## Sync Intervals

| Interval | Use Case |
|----------|----------|
| 1 hour | Development/testing, frequent changes |
| 6 hours | **Recommended** - Regular updates without spam |
| 12 hours | Twice daily sync |
| 24 hours | Daily backup/sync |

## Troubleshooting

### Git Authentication Issues

If push fails with authentication errors:

```bash
# Configure Git credentials
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Setup credential helper (cache password)
git config --global credential.helper cache
git config --global credential.helper 'cache --timeout=86400'  # 24 hours
```

### Sync Conflicts

If sync fails due to conflicts:

```bash
# Check what's wrong
python3 Auto_Update/git_auto_sync.py --status

# Manual resolution
git status
git pull --rebase origin main
# Resolve conflicts
git add -A
git rebase --continue
git push origin main
```

### View Logs

```bash
# Git sync log
tail -f Auto_Update/logs/git_sync.log

# Cron job log
tail -f Auto_Update/logs/git_sync_cron.log

# Task scheduler log
tail -f Auto_Update/logs/task_scheduler.log
```

### Disable Auto-Sync

**Option 1: Disable in configuration**
```bash
# Edit task_config.json, set enabled to false
nano Auto_Update/schedulers/task_config.json
```

**Option 2: Remove cron job**
```bash
crontab -e
# Delete the line containing git_auto_sync.py
```

## Security Considerations

- **Credentials**: Use SSH keys or credential helper for authentication
- **Private Data**: Use `.gitignore` to exclude sensitive files
- **Auto-commits**: Review changes before enabling auto-sync
- **Frequency**: Don't set interval < 1 hour to avoid rate limiting

## Recommended .gitignore Additions

```gitignore
# Logs (don't sync logs to repo)
Auto_Update/logs/*.log
Logs/*.log

# System-specific
*.pyc
__pycache__/
.venv*/
.env

# Large files
*.h5
*.pcap
Archives/*.csv

# Sensitive
Config/*.env
**/credentials.json
```

## Integration with Existing Workflows

The task scheduler integrates with:
- **Device Profile Updates**: Automatic whitelist/blacklist management
- **Dataset Refinement**: Periodic dataset processing
- **Model Validation**: Regular performance checks

All tasks run independently and log their results.

## Advanced Usage

### Custom Sync Schedule

For complex schedules, use cron directly:

```bash
crontab -e

# Sync every weekday at 9 AM
0 9 * * 1-5 cd /home/kali/Documents/Code/SECIDS-CNN && python3 Auto_Update/git_auto_sync.py

# Sync every 4 hours during work hours (9-17)
0 9-17/4 * * * cd /home/kali/Documents/Code/SECIDS-CNN && python3 Auto_Update/git_auto_sync.py
```

### Systemd Service

For system-level integration, create a systemd service:

```bash
sudo nano /etc/systemd/system/secids-autoupdate.service
```

```ini
[Unit]
Description=SECIDS Auto-Update Service
After=network.target

[Service]
Type=simple
User=kali
WorkingDirectory=/home/kali/Documents/Code/SECIDS-CNN
ExecStart=/usr/bin/python3 /home/kali/Documents/Code/SECIDS-CNN/Auto_Update/task_scheduler.py --daemon
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable secids-autoupdate.service
sudo systemctl start secids-autoupdate.service
```

## Support

For issues or questions:
1. Check logs in `Auto_Update/logs/`
2. Run with `--status` flag to diagnose
3. Use `--dry-run` to test without making changes
4. Review GitHub repository settings

---

**Last Updated**: 2026-02-23  
**Status**: Active  
**Repository**: https://github.com/KarolAtkinson/SECIDS.git

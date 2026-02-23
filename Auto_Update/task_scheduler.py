#!/usr/bin/env python3
"""
Auto-Update Task Scheduler
Monitors system and triggers sub-routines when needed
"""

import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class TaskScheduler:
    """Background task scheduler for automatic system maintenance"""
    
    def __init__(self, config_file=None):
        """
        Initialize task scheduler
        
        Args:
            config_file: Path to configuration file
        """
        self.base_dir = Path(__file__).parent
        self.project_root = self.base_dir.parent
        
        if config_file is None:
            config_file = self.base_dir / 'schedulers' / 'task_config.json'
        
        self.config_file = Path(config_file)
        self.log_dir = self.base_dir / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Task tracking
        self.last_run = defaultdict(lambda: datetime.min)
        self.task_results = {}
    
    def _load_config(self):
        """Load task configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                pass  # Skip on error
        # Default configuration
        default_config = {
            'tasks': {
                'dataset_cleanup': {
                    'enabled': True,
                    'interval_hours': 24,
                    'script': 'Launchers/project_cleanup.sh',
                    'description': 'Clean up and organize files'
                },
                'whitelist_update': {
                    'enabled': True,
                    'interval_hours': 168,  # Weekly
                    'script': 'Device_Profile/device_info/capture_device_info.py',
                    'description': 'Update device profile'
                },
                'dataset_refinement': {
                    'enabled': True,
                    'interval_hours': 72,  # Every 3 days
                    'script': 'Scripts/refine_datasets.py',
                    'description': 'Refine datasets with whitelist rules'
                },
                'model_validation': {
                    'enabled': True,
                    'interval_hours': 48,
                    'script': 'Scripts/test_enhanced_model.py',
                    'description': 'Validate model performance'
                },
                'blacklist_cleanup': {
                    'enabled': True,
                    'interval_hours': 168,  # Weekly
                    'description': 'Remove old blacklist entries'
                }
            },
            'thresholds': {
                'max_csv_files': 50,
                'max_refined_age_days': 30,
                'max_blacklist_age_days': 90
            }
        }
        
        # Save default config
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _should_run_task(self, task_name, task_config):
        """Check if task should run"""
        if not task_config.get('enabled', False):
            return False
        
        interval_hours = task_config.get('interval_hours', 24)
        last_run = self.last_run[task_name]
        time_since_last = datetime.now() - last_run
        
        return time_since_last >= timedelta(hours=interval_hours)
    
    def _run_script(self, script_path):
        """Execute a script"""
        full_path = self.project_root / script_path
        
        if not full_path.exists():
            return {'success': False, 'error': f'Script not found: {script_path}'}
        
        try:
            # Determine how to run the script
            if script_path.endswith('.py'):
                result = subprocess.run(
                    ['python3', str(full_path)],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
            elif script_path.endswith('.sh'):
                result = subprocess.run(
                    ['bash', str(full_path)],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=600
                )
            else:
                return {'success': False, 'error': 'Unknown script type'}
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout[:1000],  # Limit output
                'stderr': result.stderr[:1000]
            }
        
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Script timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_csv_files(self):
        """Check if CSV files need organization"""
        datasets_dir = self.project_root / 'SecIDS-CNN' / 'datasets'
        if not datasets_dir.exists():
            return False
        
        csv_files = list(datasets_dir.glob('*.csv'))
        max_files = self.config['thresholds']['max_csv_files']
        
        # Count non-refined files
        non_refined = [f for f in csv_files if '_refined' not in f.name and '_results' not in f.name]
        
        return len(non_refined) > max_files
    
    def run_task(self, task_name):
        """Run a specific task"""
        if task_name not in self.config['tasks']:
            return {'success': False, 'error': 'Task not found'}
        
        task_config = self.config['tasks'][task_name]
        
        self.log(f"Running task: {task_name}")
        self.log(f"Description: {task_config.get('description', 'N/A')}")
        
        # Special handling for different tasks
        if 'script' in task_config:
            result = self._run_script(task_config['script'])
        elif task_name == 'blacklist_cleanup':
            result = self._cleanup_blacklist()
        else:
            result = {'success': False, 'error': 'No handler for task'}
        
        # Record result
        self.last_run[task_name] = datetime.now()
        self.task_results[task_name] = result
        
        if result['success']:
            self.log(f"✓ Task completed: {task_name}")
        else:
            self.log(f"✗ Task failed: {task_name} - {result.get('error', 'Unknown error')}")
        
        return result
    
    def _cleanup_blacklist(self):
        """Clean up old blacklist entries"""
        try:
            blacklist_dir = self.project_root / 'Device_Profile' / 'Blacklist' / 'threat_profiles'
            if not blacklist_dir.exists():
                return {'success': True, 'message': 'No blacklist to clean'}
            
            max_age = timedelta(days=self.config['thresholds']['max_blacklist_age_days'])
            now = datetime.now()
            removed_count = 0
            
            for profile_file in blacklist_dir.glob('threat_*.json'):
                # Check file age
                mtime = datetime.fromtimestamp(profile_file.stat().st_mtime)
                if now - mtime > max_age:
                    profile_file.unlink()
                    removed_count += 1
            
            return {
                'success': True,
                'message': f'Removed {removed_count} old blacklist entries'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_and_run(self):
        """Check all tasks and run if needed"""
        results = {}
        
        for task_name, task_config in self.config['tasks'].items():
            if self._should_run_task(task_name, task_config):
                results[task_name] = self.run_task(task_name)
        
        # Check for special conditions
        if self._check_csv_files():
            self.log("⚠️  Too many CSV files detected, triggering cleanup")
            results['emergency_cleanup'] = self.run_task('dataset_cleanup')
        
        return results
    
    def log(self, message):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        print(log_message)
        
        # Write to log file
        log_file = self.log_dir / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(log_message + '\n')
    
    def get_status(self):
        """Get current status of all tasks"""
        status = {}
        
        for task_name, task_config in self.config['tasks'].items():
            last_run = self.last_run.get(task_name, datetime.min)
            next_run = last_run + timedelta(hours=task_config.get('interval_hours', 24))
            
            status[task_name] = {
                'enabled': task_config.get('enabled', False),
                'description': task_config.get('description', ''),
                'last_run': last_run.isoformat() if last_run != datetime.min else 'Never',
                'next_run': next_run.isoformat() if task_config.get('enabled') else 'Disabled',
                'last_result': self.task_results.get(task_name, {}).get('success', None)
            }
        
        return status
    
    def run_daemon(self, check_interval=3600):
        """Run scheduler as a daemon (check every hour by default)"""
        self.log("Task Scheduler daemon started")
        self.log(f"Check interval: {check_interval} seconds")
        
        try:
            while True:
                self.log("\n" + "="*60)
                self.log("Checking tasks...")
                
                results = self.check_and_run()
                
                if results:
                    self.log(f"Executed {len(results)} task(s)")
                else:
                    self.log("No tasks needed execution")
                
                self.log(f"Next check in {check_interval} seconds")
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            self.log("\nScheduler daemon stopped by user")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-Update Task Scheduler')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--status', action='store_true', help='Show task status')
    parser.add_argument('--run', type=str, help='Run specific task')
    parser.add_argument('--interval', type=int, default=3600, help='Check interval for daemon (seconds)')
    args = parser.parse_args()
    
    scheduler = TaskScheduler()
    
    if args.status:
        print("\nTask Scheduler Status:")
        print("="*60)
        status = scheduler.get_status()
        for task_name, task_status in status.items():
            print(f"\n{task_name}:")
            for key, value in task_status.items():
                print(f"  {key}: {value}")
    
    elif args.run:
        result = scheduler.run_task(args.run)
        print(f"\nTask Result: {result}")
    
    elif args.daemon:
        scheduler.run_daemon(check_interval=args.interval)
    
    else:
        print("Auto-Update Task Scheduler")
        print("="*60)
        print("Usage:")
        print("  --status         Show all tasks status")
        print("  --run TASK       Run specific task")
        print("  --daemon         Run as background daemon")
        print("  --interval N     Daemon check interval (seconds)")
        print("\nAvailable tasks:")
        for task_name, task_config in scheduler.config['tasks'].items():
            print(f"  - {task_name}: {task_config.get('description', '')}")

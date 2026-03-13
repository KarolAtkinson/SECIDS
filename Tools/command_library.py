#!/usr/bin/env python3
"""
SecIDS-CNN Command Library
==========================
Centralized command management system with shortcuts for all project operations.

Features:
- Pre-defined shortcuts for common operations
- Command history tracking
- Favorite commands
- Interactive command builder
- Batch execution
- Command validation
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse

PROJECT_ROOT = Path(__file__).resolve().parent


class CommandLibrary:
    """Manages command shortcuts and execution"""
    
    def __init__(self):
        # Use Config directory for storage
        config_dir = PROJECT_ROOT / 'Config'
        config_dir.mkdir(exist_ok=True)
        
        self.commands_file = config_dir / 'command_shortcuts.json'
        self.history_file = config_dir / 'command_history.json'
        self.favorites_file = config_dir / 'command_favorites.json'
        
        self.commands = self._load_commands()
        self.history = self._load_history()
        self.favorites = self._load_favorites()
    
    def _load_commands(self) -> Dict:
        """Load command definitions"""
        default_commands = {
            # Setup & Verification
            "verify": {
                "cmd": "python3 Tools/verify_setup.py",
                "description": "Verify system setup and dependencies",
                "category": "setup",
                "sudo": False
            },
            "install-deps": {
                "cmd": "pip install -r SecIDS-CNN/requirements.txt && pip install scapy",
                "description": "Install all required dependencies",
                "category": "setup",
                "sudo": False
            },
            "check-iface": {
                "cmd": "ip link show",
                "description": "List available network interfaces",
                "category": "setup",
                "sudo": False
            },
            "WSEC": {
                "cmd": "bash Launchers/WSEC",
                "description": "Start/open WebUI at dynamic login URL",
                "category": "setup",
                "sudo": False
            },
            
            # Pipeline Operations
            "pipeline-full": {
                "cmd": "python3 pipeline_orchestrator.py --mode full",
                "description": "Run complete pipeline (capture, train, detect)",
                "category": "pipeline",
                "sudo": True
            },
            "pipeline-capture": {
                "cmd": "python3 pipeline_orchestrator.py --mode capture --iface {iface} --duration {duration}",
                "description": "Capture and analyze traffic",
                "category": "pipeline",
                "sudo": True,
                "params": ["iface", "duration"]
            },
            "pipeline-train": {
                "cmd": "python3 pipeline_orchestrator.py --mode train",
                "description": "Train all models",
                "category": "pipeline",
                "sudo": False
            },
            "pipeline-detect-live": {
                "cmd": "python3 pipeline_orchestrator.py --mode detect-live --iface {iface} --duration {duration}",
                "description": "Live threat detection",
                "category": "pipeline",
                "sudo": True,
                "params": ["iface", "duration"]
            },
            "pipeline-detect-batch": {
                "cmd": "python3 pipeline_orchestrator.py --mode detect-batch --input {input_file}",
                "description": "Batch threat detection on CSV file",
                "category": "pipeline",
                "sudo": False,
                "params": ["input_file"]
            },
            
            # Live Detection
            "live-detect": {
                "cmd": "python3 SecIDS-CNN/run_model.py live --iface {iface}",
                "description": "Live detection with default settings",
                "category": "detection",
                "sudo": True,
                "params": ["iface"]
            },
            "live-detect-fast": {
                "cmd": "python3 SecIDS-CNN/run_model.py live --iface {iface} --window 6 --interval 4",
                "description": "Live detection with fast processing (6s window, 4s interval)",
                "category": "detection",
                "sudo": True,
                "params": ["iface"]
            },
            "live-detect-slow": {
                "cmd": "python3 SecIDS-CNN/run_model.py live --iface {iface} --window 20 --interval 10",
                "description": "Live detection with slower processing (20s window, 10s interval)",
                "category": "detection",
                "sudo": True,
                "params": ["iface"]
            },
            "live-detect-unified": {
                "cmd": "python3 SecIDS-CNN/run_model.py live --iface {iface} --backend unified",
                "description": "Live detection using unified model backend",
                "category": "detection",
                "sudo": True,
                "params": ["iface"]
            },
            
            # File-Based Detection
            "detect-file": {
                "cmd": "python3 SecIDS-CNN/run_model.py file {csv_file}",
                "description": "Detect threats in CSV file",
                "category": "detection",
                "sudo": False,
                "params": ["csv_file"]
            },
            "detect-multiple": {
                "cmd": "python3 SecIDS-CNN/run_model.py file {csv_files}",
                "description": "Detect threats in multiple CSV files",
                "category": "detection",
                "sudo": False,
                "params": ["csv_files"]
            },
            
            # Capture Operations
            "capture-quick": {
                "cmd": "dumpcap -i {iface} -a duration:120 -w Captures/capture_$(date +%s).pcap",
                "description": "Quick 120-second capture",
                "category": "capture",
                "sudo": True,
                "params": ["iface"]
            },
            "capture-custom": {
                "cmd": "dumpcap -i {iface} -a duration:{duration} -w Captures/capture_$(date +%s).pcap",
                "description": "Custom duration capture",
                "category": "capture",
                "sudo": True,
                "params": ["iface", "duration"]
            },
            "capture-continuous": {
                "cmd": "python3 Tools/continuous_live_capture.py --iface {iface}",
                "description": "Continuous capture with auto-processing",
                "category": "capture",
                "sudo": True,
                "params": ["iface"]
            },
            
            # Conversion & Processing
            "pcap-to-csv": {
                "cmd": "python3 Tools/pcap_to_secids_csv.py -i {pcap_file} -o {output_csv}",
                "description": "Convert PCAP to SecIDS CSV format",
                "category": "processing",
                "sudo": False,
                "params": ["pcap_file", "output_csv"]
            },
            "enhance-dataset": {
                "cmd": "python3 Tools/create_enhanced_dataset.py {input_csv} {output_csv}",
                "description": "Add enhanced features to dataset",
                "category": "processing",
                "sudo": False,
                "params": ["input_csv", "output_csv"]
            },
            
            # Training
            "train-secids": {
                "cmd": "python3 SecIDS-CNN/train_and_test.py",
                "description": "Train SecIDS-CNN model",
                "category": "training",
                "sudo": False
            },
            "train-unified": {
                "cmd": "python3 'Model_Tester/Code/train_unified_model.py'",
                "description": "Train unified threat model",
                "category": "training",
                "sudo": False
            },
            "train-master": {
                "cmd": "python3 'Model_Tester/Code/main.py'",
                "description": "Run complete Master ML/AI pipeline",
                "category": "training",
                "sudo": False
            },
            
            # Testing
            "test-unified": {
                "cmd": "python3 'Model_Tester/Code/test_unified_model.py'",
                "description": "Test unified model",
                "category": "testing",
                "sudo": False
            },
            "test-enhanced": {
                "cmd": "python3 test_enhanced_model.py",
                "description": "Test enhanced model features",
                "category": "testing",
                "sudo": False
            },
            
            # Analysis
            "analyze-threats": {
                "cmd": "python3 analyze_threat_origins.py",
                "description": "Analyze threat origins from detection results",
                "category": "analysis",
                "sudo": False
            },
            "analyze-results": {
                "cmd": "python3 Tools/live_capture_and_assess.py --iface {iface} --window {window}",
                "description": "Live capture and assessment",
                "category": "analysis",
                "sudo": True,
                "params": ["iface", "window"]
            },
            
            # Utilities
            "list-captures": {
                "cmd": "ls -lh Captures/",
                "description": "List captured PCAP files",
                "category": "utility",
                "sudo": False
            },
            "list-datasets": {
                "cmd": "ls -lh SecIDS-CNN/datasets/ 'Model_Tester/datasets/' 'Model_Tester/Threat_Detection_Model_1/'",
                "description": "List available datasets",
                "category": "utility",
                "sudo": False
            },
            "list-models": {
                "cmd": "ls -lh SecIDS-CNN/*.h5 'Model_Tester/models/'",
                "description": "List trained models",
                "category": "utility",
                "sudo": False
            },
            "clean-temp": {
                "cmd": "rm -f Captures/capture_temp_*.pcap && rm -f /tmp/secids_*",
                "description": "Clean temporary files",
                "category": "utility",
                "sudo": False
            },
            
            # Quick Tests
            "quick-test": {
                "cmd": "python3 SecIDS-CNN/run_model.py file SecIDS-CNN/datasets/Test1.csv",
                "description": "Quick test with Test1 dataset",
                "category": "testing",
                "sudo": False
            },
            "full-test": {
                "cmd": "python3 SecIDS-CNN/run_model.py file SecIDS-CNN/datasets/Test1.csv SecIDS-CNN/datasets/Test2.csv SecIDS-CNN/datasets/Test3.csv",
                "description": "Full test with all test datasets",
                "category": "testing",
                "sudo": False
            }
        }
        
        if self.commands_file.exists():
            with open(self.commands_file, 'r') as f:
                saved_commands = json.load(f)
                default_commands.update(saved_commands)
        
        return default_commands
    
    def _load_history(self) -> List[Dict]:
        """Load command history"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _load_favorites(self) -> List[str]:
        """Load favorite commands"""
        if self.favorites_file.exists():
            with open(self.favorites_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_commands(self):
        """Save command definitions"""
        with open(self.commands_file, 'w') as f:
            json.dump(self.commands, f, indent=2)
    
    def save_history(self):
        """Save command history"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history[-100:], f, indent=2)  # Keep last 100
    
    def save_favorites(self):
        """Save favorite commands"""
        with open(self.favorites_file, 'w') as f:
            json.dump(self.favorites, f, indent=2)
    
    def add_to_history(self, shortcut: str, cmd: str, success: bool):
        """Add command to history"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'shortcut': shortcut,
            'command': cmd,
            'success': success
        })
        self.save_history()
    
    def add_favorite(self, shortcut: str):
        """Add command to favorites"""
        if shortcut not in self.favorites and shortcut in self.commands:
            self.favorites.append(shortcut)
            self.save_favorites()
            return True
        return False
    
    def remove_favorite(self, shortcut: str):
        """Remove command from favorites"""
        if shortcut in self.favorites:
            self.favorites.remove(shortcut)
            self.save_favorites()
            return True
        return False
    
    def list_commands(self, category: Optional[str] = None):
        """List available commands"""
        print("\n" + "="*80)
        print("SECIDS-CNN COMMAND LIBRARY")
        print("="*80 + "\n")
        
        categories = {}
        for shortcut, cmd_info in self.commands.items():
            cat = cmd_info.get('category', 'other')
            if category and cat != category:
                continue
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((shortcut, cmd_info))
        
        for cat in sorted(categories.keys()):
            print(f"\n{'─'*80}")
            print(f"  {cat.upper()}")
            print(f"{'─'*80}")
            
            for shortcut, cmd_info in sorted(categories[cat], key=lambda x: x[0]):
                fav = " ⭐" if shortcut in self.favorites else ""
                sudo = " [SUDO]" if cmd_info.get('sudo', False) else ""
                params = f" (params: {', '.join(cmd_info.get('params', []))})" if cmd_info.get('params') else ""
                
                print(f"\n  {shortcut}{fav}{sudo}")
                print(f"    {cmd_info['description']}{params}")
                print(f"    $ {cmd_info['cmd']}")
        
        print("\n" + "="*80 + "\n")
    
    def execute_command(self, shortcut: str, params: Dict = None, dry_run: bool = False):
        """Execute a command by shortcut"""
        if shortcut not in self.commands:
            print(f"❌ Command '{shortcut}' not found")
            return False
        
        cmd_info = self.commands[shortcut]
        cmd = cmd_info['cmd']
        
        # Replace parameters
        if params:
            for key, value in params.items():
                cmd = cmd.replace(f'{{{key}}}', str(value))
        
        # Check for missing parameters
        if '{' in cmd and '}' in cmd:
            print(f"❌ Missing required parameters in command")
            print(f"   Command: {cmd}")
            return False
        
        # Add sudo if needed and not already present
        if cmd_info.get('sudo', False) and not cmd.startswith('sudo') and os.geteuid() != 0:
            cmd = f'sudo {cmd}'
        
        print(f"\n{'='*80}")
        print(f"Executing: {shortcut}")
        print(f"{'='*80}")
        print(f"Command: {cmd}")
        print(f"{'='*80}\n")
        
        if dry_run:
            print("DRY RUN - Command not executed")
            return True
        
        try:
            # Execute command
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=PROJECT_ROOT,
                text=True
            )
            
            success = result.returncode == 0
            self.add_to_history(shortcut, cmd, success)
            
            if success:
                print(f"\n✅ Command completed successfully")
            else:
                print(f"\n❌ Command failed with exit code {result.returncode}")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Error executing command: {e}")
            self.add_to_history(shortcut, cmd, False)
            return False
    
    def show_history(self, limit: int = 10):
        """Show command history"""
        print("\n" + "="*80)
        print("COMMAND HISTORY")
        print("="*80 + "\n")
        
        for entry in self.history[-limit:]:
            status = "✅" if entry['success'] else "❌"
            print(f"{status} [{entry['timestamp']}] {entry['shortcut']}")
            print(f"   {entry['command']}\n")
    
    def show_favorites(self):
        """Show favorite commands"""
        print("\n" + "="*80)
        print("FAVORITE COMMANDS")
        print("="*80 + "\n")
        
        if not self.favorites:
            print("No favorite commands yet. Use 'add-favorite <shortcut>' to add one.\n")
            return
        
        for shortcut in self.favorites:
            if shortcut in self.commands:
                cmd_info = self.commands[shortcut]
                print(f"⭐ {shortcut}")
                print(f"   {cmd_info['description']}")
                print(f"   $ {cmd_info['cmd']}\n")
    
    def add_custom_command(self, shortcut: str, cmd: str, description: str, 
                          category: str = 'custom', sudo: bool = False, params: List[str] = None):
        """Add a custom command"""
        self.commands[shortcut] = {
            'cmd': cmd,
            'description': description,
            'category': category,
            'sudo': sudo
        }
        if params:
            self.commands[shortcut]['params'] = params
        
        self.save_commands()
        print(f"✅ Added custom command: {shortcut}")


def main():
    parser = argparse.ArgumentParser(
        description='SecIDS-CNN Command Library - Shortcut Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all commands
  python3 command_library.py list
  
  # List commands by category
  python3 command_library.py list --category detection
  
  # Execute a command
  python3 command_library.py exec verify
  
  # Execute with parameters
  python3 command_library.py exec live-detect --param iface=eth0
  
  # Execute pipeline
  python3 command_library.py exec pipeline-capture --param iface=eth0 --param duration=120
  
  # Show history
  python3 command_library.py history
  
  # Show favorites
  python3 command_library.py favorites
  
  # Add to favorites
  python3 command_library.py add-favorite live-detect
  
  # Dry run (show command without executing)
  python3 command_library.py exec live-detect --param iface=eth0 --dry-run
        """
    )
    
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # List commands
    list_parser = subparsers.add_parser('list', help='List available commands')
    list_parser.add_argument('--category', help='Filter by category')
    
    # Execute command
    exec_parser = subparsers.add_parser('exec', help='Execute a command')
    exec_parser.add_argument('shortcut', help='Command shortcut')
    exec_parser.add_argument('--param', action='append', help='Parameter in key=value format')
    exec_parser.add_argument('--dry-run', action='store_true', help='Show command without executing')
    
    # Show history
    history_parser = subparsers.add_parser('history', help='Show command history')
    history_parser.add_argument('--limit', type=int, default=10, help='Number of entries to show')
    
    # Show favorites
    subparsers.add_parser('favorites', help='Show favorite commands')
    
    # Add favorite
    add_fav_parser = subparsers.add_parser('add-favorite', help='Add command to favorites')
    add_fav_parser.add_argument('shortcut', help='Command shortcut')
    
    # Remove favorite
    rem_fav_parser = subparsers.add_parser('remove-favorite', help='Remove command from favorites')
    rem_fav_parser.add_argument('shortcut', help='Command shortcut')
    
    # Add custom command
    add_parser = subparsers.add_parser('add', help='Add custom command')
    add_parser.add_argument('shortcut', help='Command shortcut')
    add_parser.add_argument('command', help='Command to execute')
    add_parser.add_argument('--description', required=True, help='Command description')
    add_parser.add_argument('--category', default='custom', help='Command category')
    add_parser.add_argument('--sudo', action='store_true', help='Requires sudo')
    add_parser.add_argument('--param', action='append', dest='params', help='Parameter names')
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        sys.exit(0)
    
    # Create library instance
    library = CommandLibrary()
    
    # Execute action
    if args.action == 'list':
        library.list_commands(args.category)
    
    elif args.action == 'exec':
        # Parse parameters
        params = {}
        if args.param:
            for param in args.param:
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        
        library.execute_command(args.shortcut, params, args.dry_run)
    
    elif args.action == 'history':
        library.show_history(args.limit)
    
    elif args.action == 'favorites':
        library.show_favorites()
    
    elif args.action == 'add-favorite':
        if library.add_favorite(args.shortcut):
            print(f"✅ Added '{args.shortcut}' to favorites")
        else:
            print(f"❌ Could not add '{args.shortcut}' to favorites")
    
    elif args.action == 'remove-favorite':
        if library.remove_favorite(args.shortcut):
            print(f"✅ Removed '{args.shortcut}' from favorites")
        else:
            print(f"❌ Could not remove '{args.shortcut}' from favorites")
    
    elif args.action == 'add':
        library.add_custom_command(
            args.shortcut,
            args.command,
            args.description,
            args.category,
            args.sudo,
            args.params
        )


if __name__ == '__main__':
    main()

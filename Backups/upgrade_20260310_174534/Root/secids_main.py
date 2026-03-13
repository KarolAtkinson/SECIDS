#!/usr/bin/env python3
"""
SecIDS-CNN Main Entry Point
Central launcher for all system components
"""

import sys
import os
from pathlib import Path
import argparse

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def show_banner():
    """Display SecIDS-CNN banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          SecIDS-CNN: Security Intrusion Detection System         ║
║        Convolutional Neural Network Threat Detection v2.0       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def launch_ui():
    """Launch the enhanced terminal UI"""
    ui_script = PROJECT_ROOT / 'UI' / 'terminal_ui_enhanced.py'
    os.execv(sys.executable, [sys.executable, str(ui_script)])


def launch_detection(args):
    """Launch the detection system"""
    detection_script = PROJECT_ROOT / 'SecIDS-CNN' / 'run_model.py'
    cmd = [sys.executable, str(detection_script)]
    
    if args.mode:
        cmd.append(args.mode)
        if args.mode == 'file':
            if args.files:
                cmd.extend(args.files)
            if args.all:
                cmd.append('--all')
        elif args.mode == 'live':
            if args.interface:
                cmd.extend(['--iface', args.interface])
            if args.window:
                cmd.extend(['--window', str(args.window)])
            if args.interval:
                cmd.extend(['--interval', str(args.interval)])
    
    os.execv(sys.executable, cmd)


def launch_model_tester():
    """Launch the model tester"""
    tester_script = PROJECT_ROOT / 'Model_Tester' / 'Code' / 'main.py'
    os.execv(sys.executable, [sys.executable, str(tester_script)])


def launch_auto_update():
    """Launch the auto-update scheduler"""
    scheduler_script = PROJECT_ROOT / 'Auto_Update' / 'task_scheduler.py'
    os.execv(sys.executable, [sys.executable, str(scheduler_script)])


def system_check():
    """Run system diagnostics"""
    sys.path.insert(0, str(PROJECT_ROOT / 'Tools'))
    from system_checker import SystemChecker
    
    checker = SystemChecker(verbose=True)
    all_passed = checker.check_all()
    
    if all_passed:
        print("\n✅ All system checks passed!")
    else:
        print("\n⚠️  Some system checks failed. Please review the output above.")
    
    sys.exit(0 if all_passed else 1)


def main():
    """Main entry point for SecIDS-CNN"""
    parser = argparse.ArgumentParser(
        description='SecIDS-CNN: Security Intrusion Detection System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch interactive UI (recommended)
  python secids_main.py ui
  
  # Run file-based detection
  python secids_main.py detect file --all
  
  # Run live detection
  python secids_main.py detect live --interface eth0
  
  # Run system check
  python secids_main.py check
  
  # Launch model tester
  python secids_main.py model-test
  
  # Launch auto-update scheduler
  python secids_main.py auto-update
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # UI command
    subparsers.add_parser('ui', help='Launch interactive terminal UI')
    
    # Detection command
    detect_parser = subparsers.add_parser('detect', help='Run threat detection')
    detect_subparsers = detect_parser.add_subparsers(dest='mode', help='Detection mode')
    
    # File-based detection
    file_parser = detect_subparsers.add_parser('file', help='File-based detection')
    file_parser.add_argument('files', nargs='*', help='CSV files to analyze')
    file_parser.add_argument('--all', action='store_true', help='Process all CSV files')
    
    # Live detection
    live_parser = detect_subparsers.add_parser('live', help='Live network detection')
    live_parser.add_argument('--interface', '-i', required=True, help='Network interface')
    live_parser.add_argument('--window', '-w', type=float, default=10.0, help='Window size (seconds)')
    live_parser.add_argument('--interval', '-t', type=float, default=4.0, help='Processing interval (seconds)')
    
    # System check command
    subparsers.add_parser('check', help='Run system diagnostics')
    
    # Model tester command
    subparsers.add_parser('model-test', help='Launch model tester')
    
    # Auto-update command
    subparsers.add_parser('auto-update', help='Launch auto-update scheduler')
    
    args = parser.parse_args()
    
    # Show banner
    show_banner()
    
    # Execute command
    if not args.command or args.command == 'ui':
        launch_ui()
    elif args.command == 'detect':
        launch_detection(args)
    elif args.command == 'check':
        system_check()
    elif args.command == 'model-test':
        launch_model_tester()
    elif args.command == 'auto-update':
        launch_auto_update()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

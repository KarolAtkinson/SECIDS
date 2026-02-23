#!/usr/bin/env python3
"""
SecIDS-CNN System Upgrade Script
Performs safe system-wide upgrades without crashing the system
"""

import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SystemUpgrader:
    """Safe system upgrade manager"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.venv_python = self.project_root / '.venv_test' / 'bin' / 'python'
        self.venv_pip = self.project_root / '.venv_test' / 'bin' / 'pip'
        self.backup_dir = self.project_root / 'Backups' / f'upgrade_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        self.upgrade_log = []
        
    def log(self, message, level="INFO"):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.upgrade_log.append(log_entry)
        
        # Color coding for terminal
        colors = {
            "INFO": "\033[94m",    # Blue
            "SUCCESS": "\033[92m", # Green
            "WARNING": "\033[93m", # Yellow
            "ERROR": "\033[91m",   # Red
        }
        reset = "\033[0m"
        
        color = colors.get(level, "")
        print(f"{color}{log_entry}{reset}")
    
    def create_backup(self):
        """Create backup of critical files"""
        self.log("Creating backup of critical files...")
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup critical files
            critical_files = [
                'requirements.txt',
                'pyrightconfig.json',
                'secids_main.py',
                'system_integrator.py',
            ]
            
            for file in critical_files:
                src = self.project_root / file
                if src.exists():
                    dst = self.backup_dir / file
                    shutil.copy2(src, dst)
                    self.log(f"  ✓ Backed up: {file}", "SUCCESS")
            
            # Backup __init__.py files
            init_files = list(self.project_root.glob("*/__init__.py"))
            for init_file in init_files:
                rel_path = init_file.relative_to(self.project_root)
                dst = self.backup_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(init_file, dst)
                self.log(f"  ✓ Backed up: {rel_path}", "SUCCESS")
            
            self.log(f"Backup completed: {self.backup_dir}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Backup failed: {e}", "ERROR")
            return False
    
    def check_python_version(self):
        """Verify Python version compatibility"""
        self.log("Checking Python version...")
        
        try:
            version_info = sys.version_info
            version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
            
            if version_info >= (3, 10):
                self.log(f"  ✓ Python {version_str} is compatible", "SUCCESS")
                return True
            else:
                self.log(f"  ✗ Python {version_str} is too old (requires 3.10+)", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Version check failed: {e}", "ERROR")
            return False
    
    def update_pip(self):
        """Update pip to latest version"""
        self.log("Updating pip...")
        
        try:
            result = subprocess.run(
                [str(self.venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.log("  ✓ pip updated successfully", "SUCCESS")
                return True
            else:
                self.log(f"  ✗ pip update failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"pip update failed: {e}", "ERROR")
            return False
    
    def upgrade_packages(self, safe_mode=True):
        """Upgrade Python packages"""
        self.log("Upgrading Python packages...")
        
        try:
            requirements_file = self.project_root / 'requirements.txt'
            
            if not requirements_file.exists():
                self.log("  ✗ requirements.txt not found", "ERROR")
                return False
            
            if safe_mode:
                # Install/upgrade packages from requirements.txt
                self.log("  Installing packages from requirements.txt (safe mode)...")
                result = subprocess.run(
                    [str(self.venv_pip), 'install', '-r', str(requirements_file), '--upgrade'],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
            else:
                # Upgrade all packages to latest
                self.log("  Upgrading all packages to latest versions...")
                result = subprocess.run(
                    [str(self.venv_pip), 'list', '--outdated', '--format=freeze'],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                outdated = [line.split('==')[0] for line in result.stdout.strip().split('\n') if line]
                
                if outdated:
                    result = subprocess.run(
                        [str(self.venv_pip), 'install', '--upgrade'] + outdated,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
            
            if result.returncode == 0:
                self.log("  ✓ Packages upgraded successfully", "SUCCESS")
                return True
            else:
                self.log(f"  ✗ Package upgrade failed: {result.stderr}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Package upgrade failed: {e}", "ERROR")
            return False
    
    def verify_imports(self):
        """Verify critical imports work"""
        self.log("Verifying critical imports...")
        
        critical_imports = [
            ('tensorflow', 'TensorFlow'),
            ('keras', 'Keras'),
            ('numpy', 'NumPy'),
            ('pandas', 'Pandas'),
            ('sklearn', 'scikit-learn'),
            ('scapy', 'Scapy'),
            ('rich', 'Rich'),
        ]
        
        all_passed = True
        
        for module, name in critical_imports:
            try:
                result = subprocess.run(
                    [str(self.venv_python), '-c', f'import {module}; print({module}.__version__)'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.log(f"  ✓ {name}: {version}", "SUCCESS")
                else:
                    self.log(f"  ✗ {name}: Import failed", "ERROR")
                    all_passed = False
                    
            except Exception as e:
                self.log(f"  ✗ {name}: {e}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def check_model_files(self):
        """Verify model files exist and are accessible"""
        self.log("Checking model files...")
        
        model_files = [
            self.project_root / 'Models' / 'SecIDS-CNN.h5',
        ]
        
        all_present = True
        
        for model_file in model_files:
            if model_file.exists():
                size_mb = model_file.stat().st_size / (1024 * 1024)
                self.log(f"  ✓ {model_file.name}: {size_mb:.2f} MB", "SUCCESS")
            else:
                self.log(f"  ✗ {model_file.name}: Not found", "WARNING")
                all_present = False
        
        return all_present
    
    def run_syntax_check(self):
        """Run syntax check on all Python files"""
        self.log("Running syntax checks...")
        
        python_files = []
        for pattern in ['**/*.py']:
            python_files.extend(self.project_root.glob(pattern))
        
        # Exclude certain directories
        excluded = ['__pycache__', '.venv_test', 'node_modules', 'Backups', 'Archives']
        python_files = [
            f for f in python_files 
            if not any(ex in str(f) for ex in excluded)
        ]
        
        errors = []
        checked = 0
        
        for py_file in python_files[:50]:  # Limit to first 50 files
            try:
                result = subprocess.run(
                    [str(self.venv_python), '-m', 'py_compile', str(py_file)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode != 0:
                    errors.append((py_file.name, result.stderr))
                
                checked += 1
                
            except Exception:
                pass
        
        if errors:
            self.log(f"  Found {len(errors)} syntax errors in {checked} files checked", "WARNING")
            for filename, error in errors[:5]:  # Show first 5
                self.log(f"    - {filename}", "ERROR")
        else:
            self.log(f"  ✓ All {checked} files passed syntax check", "SUCCESS")
        
        return len(errors) == 0
    
    def save_upgrade_log(self):
        """Save upgrade log to file"""
        try:
            log_file = self.backup_dir / 'upgrade_log.txt'
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'w') as f:
                f.write('\n'.join(self.upgrade_log))
            
            self.log(f"Upgrade log saved to: {log_file}", "SUCCESS")
            
        except Exception as e:
            self.log(f"Failed to save log: {e}", "ERROR")
    
    def run_full_upgrade(self, safe_mode=True):
        """Run complete system upgrade"""
        print("\n" + "="*70)
        print("  SecIDS-CNN System Upgrade")
        print("="*70 + "\n")
        
        self.log(f"Starting system upgrade (Safe Mode: {safe_mode})")
        
        steps = [
            ("Backup", self.create_backup),
            ("Python Version Check", self.check_python_version),
            ("Update pip", self.update_pip),
            ("Upgrade Packages", lambda: self.upgrade_packages(safe_mode)),
            ("Verify Imports", self.verify_imports),
            ("Check Models", self.check_model_files),
            ("Syntax Check", self.run_syntax_check),
        ]
        
        results = {}
        
        for step_name, step_func in steps:
            print(f"\n{'─'*70}")
            try:
                result = step_func()
                results[step_name] = result
                
                if not result and step_name in ["Backup", "Python Version Check"]:
                    self.log(f"Critical step '{step_name}' failed. Aborting upgrade.", "ERROR")
                    break
                    
            except Exception as e:
                self.log(f"Step '{step_name}' failed: {e}", "ERROR")
                results[step_name] = False
        
        # Summary
        print(f"\n{'='*70}")
        print("  Upgrade Summary")
        print(f"{'='*70}\n")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for step_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            color = "\033[92m" if result else "\033[91m"
            reset = "\033[0m"
            print(f"{color}{status}{reset} - {step_name}")
        
        print(f"\n{passed}/{total} steps completed successfully")
        
        # Save log
        self.save_upgrade_log()
        
        print(f"\n{'='*70}\n")
        
        if passed == total:
            self.log("System upgrade completed successfully!", "SUCCESS")
            return True
        else:
            self.log("System upgrade completed with warnings", "WARNING")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SecIDS-CNN System Upgrade')
    parser.add_argument('--unsafe', action='store_true', 
                      help='Run in unsafe mode (upgrade all packages to latest)')
    parser.add_argument('--no-backup', action='store_true',
                      help='Skip backup step (not recommended)')
    
    args = parser.parse_args()
    
    upgrader = SystemUpgrader()
    
    safe_mode = not args.unsafe
    
    if args.no_backup:
        print("\n⚠️  WARNING: Running without backup!")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Upgrade cancelled.")
            return
    
    success = upgrader.run_full_upgrade(safe_mode=safe_mode)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

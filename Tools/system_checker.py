#!/usr/bin/env python3
"""
System Checker - Comprehensive startup verification for SecIDS-CNN.

Verifies all system components and dependencies before starting operations.
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path


class SystemChecker:
    """Comprehensive system component verification."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = {}
        
    def check_all(self):
        """Run all system checks and return comprehensive report."""
        print("\n" + "="*80)
        print("SECIDS-CNN SYSTEM VERIFICATION")
        print("="*80 + "\n")
        
        checks = [
            ("Python Environment", self._check_python),
            ("Core Dependencies", self._check_dependencies),
            ("Model Files", self._check_models),
            ("Wireshark Tools", self._check_wireshark),
            ("Network Interfaces", self._check_interfaces),
            ("Countermeasures", self._check_countermeasures),
            ("Progress Utilities", self._check_progress),
            ("File Structure", self._check_file_structure),
            ("Permissions", self._check_permissions),
        ]
        
        passed = 0
        total = len(checks)
        
        for name, check_func in checks:
            status = check_func()
            self.results[name] = status
            if status:
                passed += 1
                print(f"✅ {name:<25} READY")
            else:
                print(f"❌ {name:<25} FAILED")
        
        print("\n" + "="*80)
        print(f"SYSTEM STATUS: {passed}/{total} checks passed")
        print("="*80 + "\n")
        
        return passed == total
    
    def _check_python(self):
        """Verify Python version."""
        try:
            version = sys.version_info
            if version.major == 3 and version.minor >= 8:
                if self.verbose:
                    print(f"   Python {version.major}.{version.minor}.{version.micro}")
                return True
            return False
        except Exception:
            return False
    
    def _check_dependencies(self):
        """Check critical Python packages."""
        required = ['tensorflow', 'numpy', 'pandas', 'sklearn', 'scapy']
        missing = []
        
        for package in required:
            try:
                if package == 'sklearn':
                    importlib.import_module('sklearn')
                else:
                    importlib.import_module(package)
            except ImportError:
                missing.append(package)
        
        if missing and self.verbose:
            print(f"   Missing: {', '.join(missing)}")
        
        return len(missing) == 0
    
    def _check_models(self):
        """Verify model files exist."""
        model_paths = [
            Path('../Models/SecIDS-CNN.h5'),  # From Tools dir
            Path('Models/SecIDS-CNN.h5'),  # From project root
            Path('SecIDS-CNN/SecIDS-CNN.h5'),  # From project root
            Path('../SecIDS-CNN/SecIDS-CNN.h5'),  # From Tools dir
        ]
        
        for path in model_paths:
            if path.exists():
                if self.verbose:
                    print(f"   Found: {path}")
                return True
        
        return False
    
    def _check_wireshark(self):
        """Check Wireshark/dumpcap availability."""
        tools = ['dumpcap', 'wireshark', 'tshark']
        available = []
        
        for tool in tools:
            try:
                result = subprocess.run(['which', tool], 
                                      capture_output=True, 
                                      text=True,
                                      timeout=2)
                if result.returncode == 0:
                    available.append(tool)
            except Exception as e:
                pass  # Skip on error
        if self.verbose and available:
            print(f"   Available: {', '.join(available)}")
        
        return len(available) > 0
    
    def _check_interfaces(self):
        """Check network interfaces."""
        try:
            result = subprocess.run(['ip', 'link', 'show'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=2)
            if result.returncode == 0:
                # Look for common interfaces
                interfaces = []
                for line in result.stdout.split('\n'):
                    if ': ' in line and '@' not in line:
                        parts = line.split(': ')
                        if len(parts) > 1:
                            iface = parts[1].split(':')[0]
                            if iface not in ['lo']:
                                interfaces.append(iface)
                
                if self.verbose and interfaces:
                    print(f"   Found: {', '.join(interfaces[:3])}")
                
                return len(interfaces) > 0
        except Exception as e:
            pass  # Skip on error
        return False
    
    def _check_countermeasures(self):
        """Check countermeasure system."""
        try:
            paths = [
                Path('../Countermeasures/ddos_countermeasure.py'),
                Path('Countermeasures/ddos_countermeasure.py'),
            ]
            for countermeasure_file in paths:
                if countermeasure_file.exists():
                    return True
            return False
        except Exception:
            return False
    
    def _check_progress(self):
        """Check progress utilities."""
        try:
            paths = [
                Path('progress_utils.py'),  # Same directory
                Path('Tools/progress_utils.py'),  # From project root
                Path('../Tools/progress_utils.py'),  # From SecIDS-CNN dir
            ]
            for progress_file in paths:
                if progress_file.exists():
                    return True
            return False
        except Exception:
            return False
    
    def _check_file_structure(self):
        """Verify critical directories exist."""
        required_dirs = ['SecIDS-CNN', 'Tools', 'Models', 'Captures', 'Logs']
        # Try both from project root and from Tools directory
        base_paths = [Path('.'), Path('..')]
        
        for base in base_paths:
            missing = []
            for dirname in required_dirs:
                if not (base / dirname).exists():
                    missing.append(dirname)
            
            if len(missing) == 0:
                return True
        
        return False
    
    def _check_permissions(self):
        """Check if running with necessary permissions."""
        try:
            # Check if we can access network interfaces (needs root/sudo)
            result = subprocess.run(['ip', 'link', 'show'], 
                                  capture_output=True,
                                  timeout=2)
            return result.returncode == 0
        except Exception:
            return False


def run_system_check():
    """Convenience function to run system check."""
    checker = SystemChecker(verbose=True)
    return checker.check_all()


if __name__ == '__main__':
    sys.exit(0 if run_system_check() else 1)

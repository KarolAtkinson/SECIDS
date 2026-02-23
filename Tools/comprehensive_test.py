#!/usr/bin/env python3
"""
Comprehensive System Test - Tests all SecIDS-CNN sub-routines
Tests all major components and paths for 5-minute verification
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'Tools'))
sys.path.insert(0, str(PROJECT_ROOT / 'SecIDS-CNN'))

class ComprehensiveTest:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
    def log(self, test_name, status, message=""):
        """Log test result"""
        elapsed = time.time() - self.start_time
        symbol = "✅" if status else "❌"
        self.results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'time': elapsed
        })
        print(f"[{elapsed:6.2f}s] {symbol} {test_name}")
        if message:
            print(f"          {message}")
    
    def test_system_checker(self):
        """Test 1: System Checker"""
        try:
            from system_checker import SystemChecker
            checker = SystemChecker(verbose=False)
            result = checker.check_all()
            self.log("System Checker", result, f"System checks: {len([r for r,v in checker.results.items() if v])}/9")
            return result
        except Exception as e:
            self.log("System Checker", False, str(e))
            return False
    
    def test_wireshark_manager(self):
        """Test 2: Wireshark Manager"""
        try:
            from wireshark_manager import WiresharkManager
            mgr = WiresharkManager(interface='eth0')
            self.log("Wireshark Manager Import", True, "Module loaded successfully")
            return True
        except Exception as e:
            self.log("Wireshark Manager Import", False, str(e))
            return False
    
    def test_progress_utils(self):
        """Test 3: Progress Utilities"""
        try:
            from progress_utils import ProgressBar, DataLoadingProgress
            pb = ProgressBar(total=10, description="Test")
            self.log("Progress Utilities", True, "Progress bars available")
            return True
        except Exception as e:
            self.log("Progress Utilities", False, str(e))
            return False
    
    def test_secids_model(self):
        """Test 4: SecIDS Model Loading"""
        try:
            from secids_cnn import SecIDSModel
            model = SecIDSModel()
            self.log("SecIDS Model Load", True, "Model loaded successfully")
            return True
        except Exception as e:
            self.log("SecIDS Model Load", False, str(e))
            return False
    
    def test_countermeasures(self):
        """Test 5: Countermeasure System"""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / 'Countermeasures'))
            from ddos_countermeasure import DDoSCountermeasure
            cm = DDoSCountermeasure()
            self.log("Countermeasure System", True, "Initialized successfully")
            return True
        except Exception as e:
            self.log("Countermeasure System", False, str(e))
            return False
    
    def test_whitelist_checker(self):
        """Test 6: Whitelist Checker"""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / 'Device_Profile' / 'device_info'))
            from whitelist_checker import WhitelistChecker
            wc = WhitelistChecker()
            # Test with Malwarebytes
            result = wc.is_trusted_port(443)
            self.log("Whitelist Checker", True, f"Port 443 trusted: {result}")
            return True
        except Exception as e:
            self.log("Whitelist Checker", False, str(e))
            return False
    
    def test_blacklist_manager(self):
        """Test 7: Blacklist Manager"""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / 'Device_Profile' / 'device_info'))
            from blacklist_manager import BlacklistManager
            bm = BlacklistManager()
            self.log("Blacklist Manager", True, "Initialized successfully")
            return True
        except Exception as e:
            self.log("Blacklist Manager", False, str(e))
            return False
    
    def test_vm_scanner(self):
        """Test 8: VM Scanner"""
        try:
            from vm_scanner import VMScanner
            scanner = VMScanner()
            self.log("VM Scanner", True, "Scanner initialized")
            return True
        except Exception as e:
            self.log("VM Scanner", False, str(e))
            return False
    
    def test_file_paths(self):
        """Test 9: Critical File Paths"""
        paths = {
            'Model': PROJECT_ROOT / 'Models' / 'SecIDS-CNN.h5',
            'Whitelist': PROJECT_ROOT / 'Device_Profile' / 'whitelists' / 'whitelist_20260129.json',
            'Blacklist Dir': PROJECT_ROOT / 'Device_Profile' / 'Blacklist',
            'Scans Dir': PROJECT_ROOT / 'Device_Profile' / 'scans',
            'Reports Dir': PROJECT_ROOT / 'Reports',
            'Tools Dir': PROJECT_ROOT / 'Tools',
            'Captures Dir': PROJECT_ROOT / 'Captures',
            'Logs Dir': PROJECT_ROOT / 'Logs'
        }
        
        all_exist = True
        missing = []
        for name, path in paths.items():
            if not path.exists():
                all_exist = False
                missing.append(name)
        
        if all_exist:
            self.log("File Paths Check", True, f"All {len(paths)} critical paths exist")
        else:
            self.log("File Paths Check", False, f"Missing: {', '.join(missing)}")
        return all_exist
    
    def test_data_processing(self):
        """Test 10: Data Processing Pipeline"""
        try:
            import pandas as pd
            import numpy as np
            from sklearn.preprocessing import StandardScaler
            
            # Create sample data
            data = pd.DataFrame({
                'feature1': np.random.rand(10),
                'feature2': np.random.rand(10)
            })
            
            scaler = StandardScaler()
            scaled = scaler.fit_transform(data)
            
            self.log("Data Processing", True, f"Processed {len(data)} samples")
            return True
        except Exception as e:
            self.log("Data Processing", False, str(e))
            return False
    
    def test_pcap_converter(self):
        """Test 11: PCAP to CSV Converter"""
        try:
            # Check if pcap_to_secids_csv.py exists
            converter_path = PROJECT_ROOT / 'Tools' / 'pcap_to_secids_csv.py'
            if converter_path.exists():
                self.log("PCAP Converter", True, "Converter script found")
                return True
            else:
                self.log("PCAP Converter", False, "Script not found")
                return False
        except Exception as e:
            self.log("PCAP Converter", False, str(e))
            return False
    
    def test_live_capture_module(self):
        """Test 12: Live Capture Module"""
        try:
            sys.path.insert(0, str(PROJECT_ROOT / 'Tools'))
            # Just import, don't actually capture
            import continuous_live_capture
            self.log("Live Capture Module", True, "Module import successful")
            return True
        except Exception as e:
            self.log("Live Capture Module", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SYSTEM TEST - ALL SUB-ROUTINES")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        tests = [
            self.test_system_checker,
            self.test_file_paths,
            self.test_wireshark_manager,
            self.test_progress_utils,
            self.test_secids_model,
            self.test_countermeasures,
            self.test_whitelist_checker,
            self.test_blacklist_manager,
            self.test_vm_scanner,
            self.test_data_processing,
            self.test_pcap_converter,
            self.test_live_capture_module
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        passed = sum(1 for r in self.results if r['status'])
        total = len(self.results)
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        print(f"Total Time: {elapsed:.2f}s")
        print("="*80 + "\n")
        
        return passed == total

def main():
    tester = ComprehensiveTest()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())

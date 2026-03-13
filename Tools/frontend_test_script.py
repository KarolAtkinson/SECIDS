#!/usr/bin/env python3
"""
Comprehensive Front-End Testing Script
Tests all UI functions systematically
"""

import subprocess
import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

class FrontEndTester:
    """Automated front-end testing for SecIDS-CNN"""
    
    def __init__(self):
        self.results = []
        self.failed_tests = []
        
    def log(self, message, status="INFO"):
        """Log test results"""
        timestamp = time.strftime("%H:%M:%S")
        status_colors = {
            "INFO": "\033[94m",
            "PASS": "\033[92m",
            "FAIL": "\033[91m",
            "WARN": "\033[93m"
        }
        reset = "\033[0m"
        color = status_colors.get(status, "")
        print(f"{color}[{timestamp}] [{status}] {message}{reset}")
        self.results.append({"time": timestamp, "status": status, "message": message})
        
    def test_ui_launch(self):
        """Test 1: UI Launch"""
        self.log("Testing UI launch...", "INFO")
        try:
            # Test if UI file exists
            ui_file = PROJECT_ROOT / "UI" / "terminal_ui.py"
            if not ui_file.exists():
                self.log("UI file not found!", "FAIL")
                return False
                
            # Test if UI can be imported
            sys.path.insert(0, str(PROJECT_ROOT))
            from UI.terminal_ui import SecIDSUI
            ui = SecIDSUI()
            self.log("✓ UI launches successfully", "PASS")
            return True
        except Exception as e:
            self.log(f"UI launch failed: {e}", "FAIL")
            self.failed_tests.append(("UI Launch", str(e)))
            return False
    
    def test_dataset_files(self):
        """Test 2: Dataset Files Check"""
        self.log("Checking dataset files...", "INFO")
        try:
            datasets_dir = PROJECT_ROOT / "SecIDS-CNN" / "datasets"
            if not datasets_dir.exists():
                self.log("Datasets directory not found!", "FAIL")
                return False
                
            csv_files = list(datasets_dir.glob("*.csv"))
            self.log(f"Found {len(csv_files)} CSV files", "INFO")
            
            # Check for MD_*.csv naming convention
            md_files = [f for f in csv_files if f.name.startswith("MD_")]
            non_md_files = [f for f in csv_files if not f.name.startswith("MD_") and f.name != "Test1.csv"]
            
            if non_md_files:
                self.log(f"Found {len(non_md_files)} files not following MD_*.csv convention:", "WARN")
                for f in non_md_files:
                    self.log(f"  - {f.name}", "WARN")
                self.log("These should be renamed to MD_*.csv format", "WARN")
            else:
                self.log("✓ All dataset files follow MD_*.csv convention", "PASS")
                
            return True
        except Exception as e:
            self.log(f"Dataset check failed: {e}", "FAIL")
            self.failed_tests.append(("Dataset Check", str(e)))
            return False
    
    def test_model_file(self):
        """Test 3: Model File Check"""
        self.log("Checking model file...", "INFO")
        try:
            model_paths = [
                PROJECT_ROOT / "Models" / "SecIDS-CNN.h5",
                PROJECT_ROOT / "SecIDS-CNN" / "SecIDS-CNN.h5"
            ]
            
            found = False
            for model_path in model_paths:
                if model_path.exists():
                    size_mb = model_path.stat().st_size / (1024 * 1024)
                    self.log(f"✓ Model found: {model_path.name} ({size_mb:.2f} MB)", "PASS")
                    found = True
                    break
                    
            if not found:
                self.log("Model file not found in expected locations!", "FAIL")
                return False
                
            return True
        except Exception as e:
            self.log(f"Model check failed: {e}", "FAIL")
            self.failed_tests.append(("Model Check", str(e)))
            return False
    
    def test_results_directory(self):
        """Test 4: Results Directory"""
        self.log("Checking Results directory...", "INFO")
        try:
            results_dir = PROJECT_ROOT / "Results"
            if not results_dir.exists():
                self.log("Results directory not found!", "WARN")
                self.log("Creating Results directory...", "INFO")
                results_dir.mkdir(exist_ok=True)
                self.log("✓ Results directory created", "PASS")
            else:
                self.log("✓ Results directory exists", "PASS")
                
            # Check for existing result files
            result_files = list(results_dir.glob("*"))
            if result_files:
                self.log(f"Found {len(result_files)} existing result files", "INFO")
                
            return True
        except Exception as e:
            self.log(f"Results directory check failed: {e}", "FAIL")
            self.failed_tests.append(("Results Directory", str(e)))
            return False
    
    def test_launchers(self):
        """Test 5: Launcher Scripts"""
        self.log("Checking launcher scripts...", "INFO")
        try:
            launchers_dir = PROJECT_ROOT / "Launchers"
            if not launchers_dir.exists():
                self.log("Launchers directory not found!", "FAIL")
                return False
                
            launchers = ["secids.sh", "secids-ui"]
            for launcher in launchers:
                launcher_path = launchers_dir / launcher
                if launcher_path.exists():
                    self.log(f"✓ {launcher} exists", "PASS")
                else:
                    self.log(f"✗ {launcher} missing!", "FAIL")
                    return False
                    
            return True
        except Exception as e:
            self.log(f"Launcher check failed: {e}", "FAIL")
            self.failed_tests.append(("Launchers", str(e)))
            return False
    
    def test_reports_directory(self):
        """Test 6: Reports Directory"""
        self.log("Checking Reports directory...", "INFO")
        try:
            reports_dir = PROJECT_ROOT / "Reports"
            if not reports_dir.exists():
                self.log("Reports directory not found!", "FAIL")
                return False
                
            report_files = list(reports_dir.glob("*.md"))
            self.log(f"✓ Found {len(report_files)} report files", "PASS")
            return True
        except Exception as e:
            self.log(f"Reports check failed: {e}", "FAIL")
            self.failed_tests.append(("Reports", str(e)))
            return False
    
    def test_config_directory(self):
        """Test 7: Config Directory and .env"""
        self.log("Checking Config directory...", "INFO")
        try:
            config_dir = PROJECT_ROOT / "Config"
            if not config_dir.exists():
                self.log("Config directory not found!", "FAIL")
                return False
                
            # Check for .env file
            env_file = config_dir / ".env"
            if env_file.exists():
                self.log("✓ .env file in correct location (Config/.env)", "PASS")
            else:
                self.log(".env file not found in Config/", "WARN")
                
            # Check for other config files
            config_files = list(config_dir.glob("*.json"))
            self.log(f"Found {len(config_files)} JSON config files", "INFO")
            
            return True
        except Exception as e:
            self.log(f"Config check failed: {e}", "FAIL")
            self.failed_tests.append(("Config", str(e)))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("  SecIDS-CNN Front-End Comprehensive Test Suite")
        print("="*70 + "\n")
        
        tests = [
            ("UI Launch", self.test_ui_launch),
            ("Dataset Files", self.test_dataset_files),
            ("Model File", self.test_model_file),
            ("Results Directory", self.test_results_directory),
            ("Launchers", self.test_launchers),
            ("Reports Directory", self.test_reports_directory),
            ("Config Directory", self.test_config_directory)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n{'─'*70}")
            print(f"Running: {test_name}")
            print(f"{'─'*70}")
            try:
                result = test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"Test crashed: {e}", "FAIL")
                failed += 1
                self.failed_tests.append((test_name, str(e)))
            time.sleep(0.5)
        
        # Summary
        print("\n" + "="*70)
        print("  Test Summary")
        print("="*70)
        print(f"\n  Total Tests: {len(tests)}")
        print(f"  \033[92mPassed: {passed}\033[0m")
        print(f"  \033[91mFailed: {failed}\033[0m")
        
        if self.failed_tests:
            print("\n  Failed Tests:")
            for test_name, error in self.failed_tests:
                print(f"    • {test_name}: {error}")
        
        print("\n" + "="*70 + "\n")
        
        return failed == 0

if __name__ == "__main__":
    tester = FrontEndTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

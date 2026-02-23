#!/usr/bin/env python3
"""
Final Comprehensive Test Suite
Tests all UI functions and verifies MD_*.csv naming convention
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("╔" + "="*78 + "╗")
print("║" + "  SecIDS-CNN Comprehensive Front-End Test Suite".center(78) + "║")
print("╚" + "="*78 + "╝\n")

tests_passed = 0
tests_failed = 0
test_results = []

def run_test(test_name, test_func):
    """Run a test and track results"""
    global tests_passed, tests_failed
    print(f"\n{'─'*80}")
    print(f"[TEST] {test_name}")
    print(f"{'─'*80}")
    try:
        result = test_func()
        if result:
            tests_passed += 1
            test_results.append(f"✅ {test_name}")
            print(f"✅ PASSED")
        else:
            tests_failed += 1
            test_results.append(f"❌ {test_name}")
            print(f"❌ FAILED")
        return result
    except Exception as e:
        tests_failed += 1
        test_results.append(f"❌ {test_name} - Exception: {str(e)[:50]}")
        print(f"❌ EXCEPTION: {e}")
        return False

# Test 1: System Check
def test_system_check():
    result = subprocess.run(
        ["bash", "-c", "source .venv_test/bin/activate && python3 Tools/system_checker.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30
    )
    success = "9/9 checks passed" in result.stdout
    if success:
        print("✓ All 9/9 system checks passed")
    else:
        print("✗ System check had issues")
        print(result.stdout[-300:])
    return success

# Test 2: Threat Detection
def test_threat_detection():
    result = subprocess.run(
        ["bash", "-c", "source .venv_test/bin/activate && python3 SecIDS-CNN/run_model.py file /home/kali/Documents/Code/SECIDS-CNN/SecIDS-CNN/datasets/MD_1.csv 2>&1 | tail -20"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120
    )
    success = "Total elapsed time" in result.stdout and "Results saved to" in result.stdout
    if success:
        print("✓ Threat detection completed successfully")
        # Extract key stats
        for line in result.stdout.split('\n'):
            if any(x in line for x in ['Total records', 'Threats detected', 'Processing time']):
                print(f"  {line.strip()}")
    else:
        print("✗ Threat detection failed")
        print(result.stdout[-500:])
    return success

# Test 3: Results Directory
def test_results_directory():
    results_dir = PROJECT_ROOT / "Results"
    if not results_dir.exists():
        print("✗ Results directory not found")
        return False
    
    csv_files = list(results_dir.glob("detection_results_*.csv"))
    md_files = list(results_dir.glob("threat_report_*.md"))
    json_files = list(results_dir.glob("threat_report_*.json"))
    
    print(f"✓ Found {len(csv_files)} detection result CSV files")
    print(f"✓ Found {len(md_files)} markdown reports")
    print(f"✓ Found {len(json_files)} JSON reports")
    
    return len(csv_files) > 0 and len(md_files) > 0 and len(json_files) > 0

# Test 4: CSV Naming Convention
def test_csv_naming():
    datasets_dir = PROJECT_ROOT / "SecIDS-CNN" / "datasets"
    csv_files = list(datasets_dir.glob("*.csv"))
    
    print(f"Found {len(csv_files)} CSV files:")
    
    correct = []
    incorrect = []
    
    for f in csv_files:
        if f.name.startswith("MD_") or f.name in ["Test1.csv", "Test2.csv"]:
            correct.append(f.name)
            print(f"  ✅ {f.name}")
        else:
            incorrect.append(f.name)
            print(f"  ⚠️  {f.name} - Should be MD_*.csv")
    
    if incorrect:
        print(f"\n⚠️  {len(incorrect)} files need renaming to MD_*.csv format")
    else:
        print(f"\n✓ All {len(correct)} files follow correct naming convention")
    
    return len(incorrect) == 0

# Test 5: Configuration Files
def test_config_files():
    config_dir = PROJECT_ROOT / "Config"
    env_file = config_dir / ".env"
    
    if not env_file.exists():
        print("✗ .env file not found in Config/")
        return False
    
    print(f"✓ .env file exists in Config/ ({env_file.stat().st_size} bytes)")
    
    json_files = list(config_dir.glob("*.json"))
    print(f"✓ Found {len(json_files)} JSON config files")
    
    return True

# Test 6: Launcher Scripts
def test_launchers():
    launchers = ["secids.sh", "secids-ui", "project_cleanup.sh"]
    launchers_dir = PROJECT_ROOT / "Launchers"
    
    all_found = True
    for launcher in launchers:
        path = launchers_dir / launcher
        if path.exists():
            print(f"  ✅ {launcher}")
        else:
            print(f"  ❌ {launcher} missing")
            all_found = False
    
    return all_found

# Test 7: Model Files
def test_models():
    model_locations = [
        PROJECT_ROOT / "Models" / "SecIDS-CNN.h5",
        PROJECT_ROOT / "SecIDS-CNN" / "SecIDS-CNN.h5"
    ]
    
    found = False
    for model_path in model_locations:
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {model_path.relative_to(PROJECT_ROOT)} ({size_mb:.2f} MB)")
            found = True
    
    return found

# Test 8: File Organization
def test_file_organization():
    result = subprocess.run(
        ["bash", "Launchers/project_cleanup.sh"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Check for key success indicators
    success_markers = ["✓ Project cleanup complete", ".env file present in Config/"]
    success = all(marker in result.stdout for marker in success_markers)
    
    if success:
        print("✓ File organization working correctly")
    else:
        print("✗ File organization issues")
        print(result.stdout[-300:])
    
    return success

# Test 9: UI Launch Test
def test_ui_launch():
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from UI.terminal_ui import SecIDSUI
        ui = SecIDSUI()
        print("✓ UI loads successfully")
        print(f"✓ UI config file: {ui.config_file}")
        return True
    except Exception as e:
        print(f"✗ UI failed to load: {e}")
        return False

# Test 10: Documentation Check
def test_documentation():
    docs = [
        "Master-Manual.md",
        "Reports/README.md",
        "Config/.env.README.txt"
    ]
    
    all_found = True
    for doc in docs:
        path = PROJECT_ROOT / doc
        if path.exists():
            print(f"  ✅ {doc}")
        else:
            print(f"  ⚠️  {doc} missing")
            all_found = False
    
    # Check Master-Manual mentions MD_1.csv
    manual_path = PROJECT_ROOT / "Master-Manual.md"
    if manual_path.exists():
        content = manual_path.read_text()
        if "MD_1.csv" in content:
            print("  ✅ Master-Manual.md updated with MD_1.csv")
        else:
            print("  ⚠️  Master-Manual.md needs MD_1.csv reference")
    
    return all_found

# Run all tests
print("\nRunning comprehensive test suite...\n")

run_test("1. System Check", test_system_check)
run_test("2. Threat Detection", test_threat_detection)
run_test("3. Results Directory", test_results_directory)
run_test("4. CSV Naming Convention", test_csv_naming)
run_test("5. Configuration Files", test_config_files)
run_test("6. Launcher Scripts", test_launchers)
run_test("7. Model Files", test_models)
run_test("8. File Organization", test_file_organization)
run_test("9. UI Launch", test_ui_launch)
run_test("10. Documentation", test_documentation)

# Final Summary
print("\n" + "="*80)
print("  FINAL TEST SUMMARY")
print("="*80)
print(f"\n  Total Tests: {tests_passed + tests_failed}")
print(f"  ✅ Passed: {tests_passed}")
print(f"  ❌ Failed: {tests_failed}")
print(f"  Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")

print("\n  Test Results:")
for result in test_results:
    print(f"    {result}")

print("\n" + "="*80)

if tests_failed == 0:
    print("\n  🎉 ALL TESTS PASSED! System is production ready.")
else:
    print(f"\n  ⚠️  {tests_failed} test(s) failed. Review output above.")

print("\n" + "="*80 + "\n")

sys.exit(0 if tests_failed == 0 else 1)

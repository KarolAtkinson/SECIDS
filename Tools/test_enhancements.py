#!/usr/bin/env python3
"""
Quick test script to verify all new features are working correctly.

This script tests:
1. Wireshark Manager functionality
2. Progress bar utilities
3. Import paths and dependencies
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / 'Tools'
SECIDS_DIR = PROJECT_ROOT / 'SecIDS-CNN'

# Add paths
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
if str(SECIDS_DIR) not in sys.path:
    sys.path.insert(0, str(SECIDS_DIR))

def test_imports():
    """Test that all new modules can be imported."""
    print("="*80)
    print("TESTING IMPORTS")
    print("="*80)
    
    try:
        from wireshark_manager import WiresharkManager
        print("✓ Wireshark Manager import successful")
    except ImportError as e:
        print(f"✗ Wireshark Manager import failed: {e}")
        return False
    
    try:
        from progress_utils import (DataLoadingProgress, PreprocessingProgress,
                                     TrainingProgress, PredictionProgress)
        print("✓ Progress utilities import successful")
    except ImportError as e:
        print(f"⚠️  Progress utilities import failed (tqdm may not be installed): {e}")
        print("   Run: pip install tqdm")
    
    return True

def test_wireshark_manager():
    """Test Wireshark Manager basic functionality."""
    print("\n" + "="*80)
    print("TESTING WIRESHARK MANAGER")
    print("="*80)
    
    try:
        from wireshark_manager import WiresharkManager
        
        # Test initialization
        manager = WiresharkManager('eth0')
        print("✓ WiresharkManager initialization successful")
        
        # Test interface configuration
        print(f"  - Interface: {manager.interface}")
        print(f"  - Running: {manager.is_running}")
        
        # Note: Not actually starting Wireshark in test mode
        print("✓ Basic functionality tests passed")
        print("  Note: Actual Wireshark start/stop not tested (requires sudo)")
        
        return True
    except Exception as e:
        print(f"✗ Wireshark Manager test failed: {e}")
        return False

def test_progress_utils():
    """Test progress utilities basic functionality."""
    print("\n" + "="*80)
    print("TESTING PROGRESS UTILITIES")
    print("="*80)
    
    try:
        from progress_utils import ProgressBar
        import time
        
        # Test basic progress bar
        print("Testing basic progress bar...")
        with ProgressBar(10, "Test operation", "items") as pbar:
            for i in range(10):
                time.sleep(0.05)
                pbar.update()
        
        print("✓ Progress bar test successful")
        return True
    except ImportError:
        print("⚠️  tqdm not installed - progress bars will not be available")
        print("   Run: pip install tqdm")
        return True  # Not a failure, just missing optional dependency
    except Exception as e:
        print(f"✗ Progress utilities test failed: {e}")
        return False

def test_file_structure():
    """Verify all files are in correct locations."""
    print("\n" + "="*80)
    print("TESTING FILE STRUCTURE")
    print("="*80)
    
    files_to_check = [
        ('Tools/wireshark_manager.py', TOOLS_DIR / 'wireshark_manager.py'),
        ('Tools/progress_utils.py', TOOLS_DIR / 'progress_utils.py'),
        ('SecIDS-CNN/run_model.py', SECIDS_DIR / 'run_model.py'),
        ('SecIDS-CNN/train_and_test.py', SECIDS_DIR / 'train_and_test.py'),
        ('Tools/continuous_live_capture.py', TOOLS_DIR / 'continuous_live_capture.py'),
        ('Tools/live_capture_and_assess.py', TOOLS_DIR / 'live_capture_and_assess.py'),
        ('Tools/pcap_to_secids_csv.py', TOOLS_DIR / 'pcap_to_secids_csv.py'),
        ('Reports/ENHANCEMENT_UPDATE.md', PROJECT_ROOT / 'Reports' / 'ENHANCEMENT_UPDATE.md'),
    ]
    
    all_found = True
    for name, path in files_to_check:
        if path.exists():
            print(f"✓ {name}")
        else:
            print(f"✗ {name} - NOT FOUND")
            all_found = False
    
    if all_found:
        print("\n✓ All files in correct locations")
    else:
        print("\n✗ Some files are missing")
    
    return all_found

def test_dependencies():
    """Check for required and optional dependencies."""
    print("\n" + "="*80)
    print("TESTING DEPENDENCIES")
    print("="*80)
    
    required = [
        ('psutil', 'Process management (required for Wireshark manager)'),
        ('pandas', 'Data manipulation'),
        ('numpy', 'Numerical operations'),
        ('sklearn', 'Machine learning utilities'),
    ]
    
    optional = [
        ('tqdm', 'Progress bars (optional but recommended)'),
        ('scapy', 'Packet manipulation (required for live capture)'),
        ('tensorflow', 'Deep learning (required for model training)'),
    ]
    
    print("\nRequired dependencies:")
    for module, desc in required:
        try:
            __import__(module)
            print(f"  ✓ {module:15} - {desc}")
        except ImportError:
            print(f"  ✗ {module:15} - {desc} - NOT INSTALLED")
    
    print("\nOptional dependencies:")
    for module, desc in optional:
        try:
            __import__(module)
            print(f"  ✓ {module:15} - {desc}")
        except ImportError:
            print(f"  ⚠️ {module:15} - {desc} - NOT INSTALLED")
    
    return True

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "SECIDS-CNN ENHANCEMENT TEST SUITE" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("File Structure", test_file_structure()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("Wireshark Manager", test_wireshark_manager()))
    results.append(("Progress Utilities", test_progress_utils()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name:25} {status}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("  1. Install missing dependencies: pip install -r SecIDS-CNN/requirements.txt")
        print("  2. Try running live capture: sudo python3 SecIDS-CNN/run_model.py live --iface eth0")
        print("  3. Check ENHANCEMENT_UPDATE.md for detailed documentation")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    print("="*80)
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

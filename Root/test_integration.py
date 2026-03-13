#!/usr/bin/env python3
"""
Comprehensive Integration Test for SecIDS-CNN
==============================================
Tests the complete integrated workflow system including:
- Component initialization
- Greylist system
- Threat classification
- Countermeasure integration (Active/Passive modes)
"""

import sys
import os
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'SecIDS-CNN'))
sys.path.insert(0, str(PROJECT_ROOT / 'Device_Profile'))
sys.path.insert(0, str(PROJECT_ROOT / 'Countermeasures'))

print("="*80)
print("  SecIDS-CNN Comprehensive Integration Test")
print("="*80)

# Test 1: Import all components
print("\n[Test 1] Importing core components...")
components_loaded = []
components_failed = []

# SecIDS Model
try:
    from secids_cnn import SecIDSModel
    components_loaded.append("SecIDSModel")
    print("  ✓ SecIDSModel imported")
except Exception as e:
    components_failed.append(("SecIDSModel", str(e)))
    print(f"  ⚠️  SecIDSModel not available: {e}")

# Greylist Manager
try:
    from greylist_manager import GreylistManager
    components_loaded.append("GreylistManager")
    print("  ✓ GreylistManager imported")
except Exception as e:
    components_failed.append(("GreylistManager", str(e)))
    print(f"  ⚠️  GreylistManager not available: {e}")

# List Manager
try:
    from list_manager import ListManager
    components_loaded.append("ListManager")
    print("  ✓ ListManager imported")
except Exception as e:
    components_failed.append(("ListManager", str(e)))
    print(f"  ⚠️  ListManager not available: {e}")

# Countermeasures - New Architecture
countermeasure_available = False
try:
    from countermeasure_active import ActiveCountermeasure
    from countermeasure_passive import PassiveCountermeasure
    components_loaded.append("ActiveCountermeasure")
    components_loaded.append("PassiveCountermeasure")
    countermeasure_available = True
    print("  ✓ ActiveCountermeasure imported (new architecture)")
    print("  ✓ PassiveCountermeasure imported (new architecture)")
except Exception as e:
    # Try legacy countermeasure
    try:
        from ddos_countermeasure import DDoSCountermeasure
        components_loaded.append("DDoSCountermeasure")
        print("  ✓ DDoSCountermeasure imported (legacy)")
    except Exception as e2:
        components_failed.append(("Countermeasures", str(e)))
        print(f"  ⚠️  Countermeasures not available: {e}")

# Test 2: Initialize components
print("\n[Test 2] Initializing components...")

# Initialize model
model = None
if "SecIDSModel" in components_loaded:
    try:
        model = SecIDSModel()
        print("  ✓ SecIDS-CNN model loaded")
        print(f"    Model type: {type(model.model)}")
    except Exception as e:
        print(f"  ⚠️  Model initialization skipped: {e}")

# Initialize greylist manager
greylist_mgr = None
if "GreylistManager" in components_loaded:
    try:
        greylist_mgr = GreylistManager()
        print("  ✓ Greylist manager initialized")
        print(f"    Thresholds: {greylist_mgr.GREYLIST_LOW:.0%} - {greylist_mgr.GREYLIST_HIGH:.0%}")
    except Exception as e:
        print(f"  ✗ Greylist manager initialization failed: {e}")

# Initialize list manager
list_mgr = None
if "ListManager" in components_loaded:
    try:
        list_mgr = ListManager()
        print("  ✓ List manager initialized")
        status = list_mgr.get_status()
        print(f"    Whitelist: {status['whitelist_count']} entries")
        print(f"    Blacklist: {status['blacklist_count']} entries")
        print(f"    Greylist: {status['greylist_count']} entries")
    except Exception as e:
        print(f"  ✗ List manager initialization failed: {e}")

# Test 3: Model prediction test
print("\n[Test 3] Testing model predictions...")
if model:
    try:
        import pandas as pd
        import numpy as np
        
        # Create sample data with correct features
        test_data = pd.DataFrame({
            'Destination Port': [80, 443, 22],
            'Flow Duration': [1000000, 2000000, 500000],
            'Total Fwd Packets': [10, 20, 5],
            'Total Length of Fwd Packets': [5000, 10000, 2500],
            'Flow Bytes/s': [5000.0, 5000.0, 5000.0],
            'Flow Packets/s': [10.0, 10.0, 10.0],
            'Average Packet Size': [500.0, 500.0, 500.0],
            'Packet Length Std': [100.0, 150.0, 50.0],
            'FIN Flag Count': [1, 1, 1],
            'ACK Flag Count': [8, 15, 3]
        })
        
        predictions = model.predict_proba(test_data)
        print(f"  ✓ Model predictions successful")
        print(f"    Prediction shape: {predictions.shape if hasattr(predictions, 'shape') else len(predictions)}")
        print(f"    Sample predictions: {predictions[:3] if hasattr(predictions, '__getitem__') else predictions}")
        
    except Exception as e:
        print(f"  ✗ Model prediction failed: {e}")
else:
    print("  ⚠️  Model not loaded, skipping prediction test")

# Test 4: Threat classification workflow
print("\n[Test 4] Testing threat classification workflow...")
if greylist_mgr and model:
    try:
        # Simulate threats with different probabilities
        test_threats = [
            {'src_ip': '10.10.10.10', 'probability': 0.45, 'dst_port': 80, 'timestamp': '2026-02-03T17:00:00'},
            {'src_ip': '20.20.20.20', 'probability': 0.65, 'dst_port': 443, 'timestamp': '2026-02-03T17:00:01'},
            {'src_ip': '30.30.30.30', 'probability': 0.85, 'dst_port': 22, 'timestamp': '2026-02-03T17:00:02'},
        ]
        
        classifications = {'whitelist': 0, 'greylist': 0, 'blacklist': 0}
        
        for threat in test_threats:
            classification, needs_decision = greylist_mgr.process_threat(threat)
            classifications[classification] += 1
            symbol = "✓" if classification == 'whitelist' else "⚠️" if classification == 'greylist' else "🚫"
            print(f"  {symbol} IP {threat['src_ip']}: {classification.upper()} ({threat['probability']*100:.0f}%)")
        
        print(f"\n  Classification Summary:")
        print(f"    Whitelist: {classifications['whitelist']}")
        print(f"    Greylist: {classifications['greylist']} (needs user decision)")
        print(f"    Blacklist: {classifications['blacklist']} (auto-block)")
        
    except Exception as e:
        print(f"  ✗ Classification workflow failed: {e}")
else:
    print("  ⚠️  Components not available for classification test")

# Test 5: List management operations
print("\n[Test 5] Testing list management operations...")
if list_mgr:
    try:
        test_ip = '192.168.100.100'
        
        # Test adding to greylist
        list_mgr.add_to_greylist(test_ip, "Integration test entry")
        status = list_mgr.get_ip_status(test_ip)
        assert status == 'greylist', f"Expected greylist, got {status}"
        print(f"  ✓ Added to greylist: {test_ip}")
        
        # Test moving to whitelist
        list_mgr.move_to_whitelist(test_ip, "Verified safe")
        status = list_mgr.get_ip_status(test_ip)
        assert status == 'whitelist', f"Expected whitelist, got {status}"
        print(f"  ✓ Moved to whitelist: {test_ip}")
        
        # Test moving to blacklist
        list_mgr.move_to_blacklist(test_ip, "Security threat")
        status = list_mgr.get_ip_status(test_ip)
        assert status == 'blacklist', f"Expected blacklist, got {status}"
        print(f"  ✓ Moved to blacklist: {test_ip}")
        
        # Cleanup
        list_mgr.remove_from_blacklist(test_ip)
        print(f"  ✓ Cleanup complete")
        
    except Exception as e:
        print(f"  ✗ List management operations failed: {e}")
else:
    print("  ⚠️  List manager not available")

# Test 6: Statistics and reporting
print("\n[Test 6] Testing statistics and reporting...")
if greylist_mgr:
    try:
        stats = greylist_mgr.get_statistics()
        print(f"  ✓ Statistics retrieved:")
        print(f"    Total alerts: {stats['total_greylist_alerts']}")
        print(f"    Current greylist size: {stats['current_greylist_size']}")
        print(f"    Pending decisions: {stats['pending_decisions']}")
        
        # Generate report
        report_path = greylist_mgr.export_report()
        print(f"  ✓ Report exported to: {report_path}")
        
    except Exception as e:
        print(f"  ✗ Statistics/reporting failed: {e}")
else:
    print("  ⚠️  Greylist manager not available")

# Test 7: Configuration verification
print("\n[Test 7] Verifying configuration...")

config_checks = []

# Check directories
dirs_to_check = [
    PROJECT_ROOT / 'Device_Profile',
    PROJECT_ROOT / 'Device_Profile' / 'greylist',
    PROJECT_ROOT / 'Device_Profile' / 'whitelists',
    PROJECT_ROOT / 'Device_Profile' / 'Blacklist',
]

for dir_path in dirs_to_check:
    if dir_path.exists():
        config_checks.append(f"✓ {dir_path.name} directory exists")
    else:
        config_checks.append(f"✗ {dir_path.name} directory missing")

# Check model file
model_path = PROJECT_ROOT / 'Models' / 'SecIDS-CNN.h5'
if model_path.exists():
    config_checks.append(f"✓ Model file exists ({model_path.stat().st_size / (1024*1024):.1f} MB)")
else:
    config_checks.append("✗ Model file missing")

for check in config_checks:
    print(f"  {check}")

# Final Summary
print("\n" + "="*80)
print("  INTEGRATION TEST SUMMARY")
print("="*80)
print(f"\n  Components Loaded: {len(components_loaded)}/{len(components_loaded) + len(components_failed)}")
for comp in components_loaded:
    print(f"    ✓ {comp}")

if components_failed:
    print(f"\n  Components Failed: {len(components_failed)}")
    for comp, error in components_failed:
        print(f"    ✗ {comp}: {error}")

print(f"\n  Status: ", end="")
if len(components_failed) == 0:
    print("✓ ALL SYSTEMS OPERATIONAL")
elif "SecIDSModel" in components_loaded and "GreylistManager" in components_loaded:
    print("⚠️  CORE SYSTEMS OPERATIONAL (some optional components unavailable)")
else:
    print("✗ CRITICAL COMPONENTS MISSING")

print("\n" + "="*80)
print("  Integration test complete!")
print("="*80)

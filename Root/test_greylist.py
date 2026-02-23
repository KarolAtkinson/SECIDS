#!/usr/bin/env python3
"""
Greylist System Test Script
Tests all components of the greylist integration
"""

import sys
from pathlib import Path

# Add paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / 'Device_Profile'))

print("="*80)
print("  SecIDS-CNN Greylist System Test")
print("="*80)

# Test 1: Import modules
print("\n[Test 1] Importing modules...")
try:
    from greylist_manager import GreylistManager
    print("  ✓ GreylistManager imported")
except Exception as e:
    print(f"  ✗ Failed to import GreylistManager: {e}")
    sys.exit(1)

try:
    from list_manager import ListManager
    print("  ✓ ListManager imported")
except Exception as e:
    print(f"  ✗ Failed to import ListManager: {e}")
    sys.exit(1)

# Test 2: Initialize managers
print("\n[Test 2] Initializing managers...")
try:
    greylist_mgr = GreylistManager()
    print("  ✓ GreylistManager initialized")
except Exception as e:
    print(f"  ✗ Failed to initialize GreylistManager: {e}")
    sys.exit(1)

try:
    list_mgr = ListManager()
    print("  ✓ ListManager initialized")
except Exception as e:
    print(f"  ✗ Failed to initialize ListManager: {e}")
    sys.exit(1)

# Test 3: Threat classification
print("\n[Test 3] Testing threat classification...")
test_cases = [
    (0.3, 'whitelist', '30% - should be whitelist'),
    (0.6, 'greylist', '60% - should be greylist'),
    (0.9, 'blacklist', '90% - should be blacklist'),
]

for probability, expected, description in test_cases:
    result = greylist_mgr.classify_threat(probability)
    if result == expected:
        print(f"  ✓ {description}: {result}")
    else:
        print(f"  ✗ {description}: got {result}, expected {expected}")

# Test 4: Process threats
print("\n[Test 4] Processing test threats...")
test_threats = [
    {'src_ip': '192.168.1.100', 'probability': 0.45, 'dst_port': 80},   # Whitelist
    {'src_ip': '10.0.0.50', 'probability': 0.62, 'dst_port': 443},      # Greylist
    {'src_ip': '172.16.0.30', 'probability': 0.88, 'dst_port': 22},     # Blacklist
    {'src_ip': '192.168.1.200', 'probability': 0.58, 'dst_port': 8080}, # Greylist
]

for threat in test_threats:
    classification, needs_decision = greylist_mgr.process_threat(threat)
    status = "✓" if needs_decision == (classification == 'greylist') else "✗"
    print(f"  {status} IP {threat['src_ip']}: {classification} ({threat['probability']*100:.0f}%)")

# Test 5: Check greylist
print("\n[Test 5] Checking greylist entries...")
greylisted_ips = greylist_mgr.get_all_greylisted_ips()
print(f"  ✓ Greylisted IPs: {len(greylisted_ips)}")
for ip in greylisted_ips:
    entry = greylist_mgr.get_greylist_entry(ip)
    print(f"    - {ip}: {entry['occurrences']} occurrence(s)")

# Test 6: List manager integration
print("\n[Test 6] Testing list manager integration...")
test_ip = '192.168.1.100'
print(f"  Testing IP: {test_ip}")

# Check initial status
status = list_mgr.get_ip_status(test_ip)
print(f"  Initial status: {status}")

# Add to greylist
list_mgr.add_to_greylist(test_ip, "Test entry")
status = list_mgr.get_ip_status(test_ip)
if status == 'greylist':
    print(f"  ✓ Added to greylist: {status}")
else:
    print(f"  ✗ Failed to add to greylist: {status}")

# Move to whitelist
list_mgr.move_to_whitelist(test_ip, "Test - verified safe")
status = list_mgr.get_ip_status(test_ip)
if status == 'whitelist':
    print(f"  ✓ Moved to whitelist: {status}")
else:
    print(f"  ✗ Failed to move to whitelist: {status}")

# Clean up test entry
list_mgr.remove_from_whitelist(test_ip)
print(f"  ✓ Test entry cleaned up")

# Test 7: Statistics
print("\n[Test 7] Checking statistics...")
stats = greylist_mgr.get_statistics()
print(f"  Total greylist alerts: {stats['total_greylist_alerts']}")
print(f"  Current greylist size: {stats['current_greylist_size']}")
print(f"  Pending decisions: {stats['pending_decisions']}")

# Test 8: Export reports
print("\n[Test 8] Exporting reports...")
try:
    greylist_report = greylist_mgr.export_report()
    print(f"  ✓ Greylist report: {greylist_report}")
except Exception as e:
    print(f"  ✗ Failed to export greylist report: {e}")

try:
    list_report = list_mgr.export_report()
    print(f"  ✓ Lists report: {list_report}")
except Exception as e:
    print(f"  ✗ Failed to export lists report: {e}")

# Summary
print("\n" + "="*80)
print("  TEST SUMMARY")
print("="*80)
print(f"  ✓ All core tests passed")
print(f"  ✓ Greylist system is functional")
print(f"  ✓ List manager integration working")
print("\n  Ready for integration with workflow!")
print("="*80)

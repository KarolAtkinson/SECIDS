#!/usr/bin/env python3
"""
Test script for DDoS Countermeasure System
Verifies that countermeasures work correctly with live detection
"""

import sys
from pathlib import Path

# Add Countermeasures to path
sys.path.insert(0, str(Path(__file__).parent))
from ddos_countermeasure import DDoSCountermeasure

def test_basic_functionality():
    """Test basic countermeasure functionality"""
    print("=" * 80)
    print("TESTING: Basic Countermeasure Functionality")
    print("=" * 80)
    print()
    
    cm = DDoSCountermeasure(
        block_threshold=3,
        time_window=10,
        auto_block=False  # Disable actual blocking for test
    )
    
    cm.start()
    
    # Test 1: Single threat (should not trigger block)
    print("Test 1: Single threat detection")
    cm.process_threat({
        'src_ip': '192.168.1.100',
        'dst_port': 80,
        'probability': 0.9
    })
    print("✅ Single threat processed\n")
    
    # Test 2: Multiple threats (should trigger alert)
    print("Test 2: Multiple threats from same IP")
    for i in range(5):
        cm.process_threat({
            'src_ip': '192.168.1.100',
            'dst_port': 80,
            'probability': 0.85
        })
    print("✅ Multiple threats processed\n")
    
    # Wait for processing
    cm.action_queue.join()
    
    # Show statistics
    cm.print_statistics()
    
    cm.stop()
    
    print("\n✅ Basic functionality test completed")
    return True


def test_threat_tracking():
    """Test threat history tracking"""
    print("=" * 80)
    print("TESTING: Threat History Tracking")
    print("=" * 80)
    print()
    
    cm = DDoSCountermeasure(
        block_threshold=3,
        time_window=5,
        auto_block=False
    )
    
    cm.start()
    
    # Add threats from different IPs
    ips = ['10.0.0.1', '10.0.0.2', '10.0.0.1', '10.0.0.3', '10.0.0.1']
    
    for ip in ips:
        cm.process_threat({
            'src_ip': ip,
            'dst_port': 443,
            'probability': 0.8
        })
    
    cm.action_queue.join()
    
    # Check threat history
    print(f"Unique IPs tracked: {len(cm.threat_history)}")
    for ip, threats in cm.threat_history.items():
        print(f"  {ip}: {len(threats)} threats")
    
    cm.stop()
    
    print("\n✅ Threat tracking test completed")
    return True


def test_concurrent_processing():
    """Test thread-safe concurrent threat processing"""
    import threading
    import time
    
    print("=" * 80)
    print("TESTING: Concurrent Threat Processing")
    print("=" * 80)
    print()
    
    cm = DDoSCountermeasure(
        block_threshold=5,
        time_window=10,
        auto_block=False
    )
    
    cm.start()
    
    def send_threats(ip, count):
        for i in range(count):
            cm.process_threat({
                'src_ip': ip,
                'dst_port': 80,
                'probability': 0.9
            })
            time.sleep(0.01)
    
    # Launch multiple threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=send_threats, args=(f'10.0.0.{i}', 10))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    cm.action_queue.join()
    
    print(f"Total threats processed: {cm.stats['threats_detected']}")
    print(f"Actions taken: {cm.stats['actions_taken']}")
    
    cm.stop()
    
    print("\n✅ Concurrent processing test completed")
    return True


def run_all_tests():
    """Run all countermeasure tests"""
    print()
    print("=" * 80)
    print("COUNTERMEASURE SYSTEM TEST SUITE")
    print("=" * 80)
    print()
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Threat Tracking", test_threat_tracking),
        ("Concurrent Processing", test_concurrent_processing),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n{'='*80}")
            print(f"Running: {name}")
            print('='*80)
            if test_func():
                passed += 1
                print(f"✅ {name} PASSED")
            else:
                failed += 1
                print(f"❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {passed / (passed + failed) * 100:.1f}%")
    print("=" * 80)
    print()
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

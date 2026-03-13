#!/usr/bin/env python3
"""
Comprehensive Test Suite for Countermeasure System
Tests all components: Core, Passive, Active
"""

import sys
import time
from pathlib import Path

# Add Countermeasures to path
sys.path.insert(0, str(Path(__file__).parent / 'Countermeasures'))

from countermeasure_core import CountermeasureCore
from countermeasure_passive import PassiveCountermeasure
from countermeasure_active import ActiveCountermeasure


def test_core():
    """Test CountermeasureCore base class"""
    print("\n" + "="*80)
    print("TEST 1: CountermeasureCore Base Class")
    print("="*80)
    
    try:
        core = CountermeasureCore(mode='test', auto_block=False)
        print(f"✓ Instance created")
        print(f"  Mode: {core.mode}")
        print(f"  Threshold: {core.block_threshold}")
        print(f"  Time window: {core.time_window}s")
        print(f"  Auto-block: {core.auto_block}")
        
        # Test statistics
        stats = core.get_statistics()
        print(f"✓ Statistics retrieved: {len(stats)} fields")
        
        # Test status
        status = core.get_status()
        print(f"✓ Status: {status}")
        
        core.stop()
        print(f"✓ Stopped cleanly")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_passive():
    """Test PassiveCountermeasure"""
    print("\n" + "="*80)
    print("TEST 2: PassiveCountermeasure (Automated Mode)")
    print("="*80)
    
    try:
        passive = PassiveCountermeasure(block_threshold=3, time_window=30)
        print(f"✓ Instance created and auto-started")
        print(f"  Mode: {passive.mode}")
        print(f"  Running: {passive.running}")
        print(f"  Threshold: {passive.block_threshold} threats / {passive.time_window}s")
        
        # Test simple stats
        stats = passive.get_simple_stats()
        print(f"✓ Simple stats retrieved:")
        print(f"  Runtime: {stats.get('runtime', 0):.1f}s")
        print(f"  Input traffic: {stats.get('input_traffic', 0)}")
        print(f"  Output traffic: {stats.get('output_traffic', 0)}")
        print(f"  Threats detected: {stats.get('threats_detected', 0)}")
        print(f"  Countermeasures: {stats.get('countermeasures_deployed', 0)}")
        
        # Test health status
        health = passive.get_health_status()
        print(f"✓ Health status: {health}")
        
        # Test pause/resume
        passive.pause()
        print(f"✓ Paused successfully")
        
        time.sleep(0.5)
        
        passive.resume()
        print(f"✓ Resumed successfully")
        
        # Stop
        passive.stop()
        print(f"✓ Stopped cleanly")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_active():
    """Test ActiveCountermeasure"""
    print("\n" + "="*80)
    print("TEST 3: ActiveCountermeasure (Manual Mode)")
    print("="*80)
    
    try:
        active = ActiveCountermeasure(
            block_threshold=5,
            time_window=60,
            interactive=False
        )
        print(f"✓ Instance created (manual start)")
        print(f"  Mode: {active.mode}")
        print(f"  Running: {active.running}")
        print(f"  Threshold: {active.block_threshold} threats / {active.time_window}s")
        print(f"  Interactive: {active.interactive}")
        
        # Start monitoring
        active.start()
        print(f"✓ Started monitoring")
        print(f"  Running: {active.running}")
        
        # Test detailed stats
        stats = active.get_detailed_stats()
        print(f"✓ Detailed stats retrieved:")
        print(f"  Threats detected: {stats.get('threats_detected', 0)}")
        print(f"  IPs blocked: {stats.get('ips_blocked', 0)}")
        print(f"  Ports blocked: {stats.get('ports_blocked', 0)}")
        print(f"  Manual actions: {len(stats.get('manual_actions', []))}")
        
        # Test manual blocking (simulate threat processing)
        print(f"\n  Testing threat processing...")
        threat = {
            'src_ip': '192.168.1.100',
            'dst_port': 80,
            'protocol': 'TCP',
            'type': 'DDoS'
        }
        active.process_threat(threat)
        print(f"✓ Threat processed (won't block - below threshold)")
        
        # Stop
        active.stop()
        print(f"✓ Stopped cleanly")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_manual():
    """Test workflow manual display"""
    print("\n" + "="*80)
    print("TEST 4: Workflow Manual")
    print("="*80)
    
    try:
        from countermeasure_active import show_workflow_manual
        print("✓ show_workflow_manual() imported")
        print("\nDisplaying workflow manual:")
        print("-" * 80)
        show_workflow_manual()
        print("-" * 80)
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_imports():
    """Test UI imports"""
    print("\n" + "="*80)
    print("TEST 5: UI Imports")
    print("="*80)
    
    try:
        from passive_ui import PassiveUI
        print(f"✓ PassiveUI imported")
        
        from active_ui import ActiveUI
        print(f"✓ ActiveUI imported")
        
        # Create instances (don't run them)
        passive_ui = PassiveUI()
        print(f"✓ PassiveUI instance created")
        
        active_ui = ActiveUI()
        print(f"✓ ActiveUI instance created")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("COUNTERMEASURE SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    results = {
        'Core Base Class': test_core(),
        'Passive Mode': test_passive(),
        'Active Mode': test_active(),
        'Workflow Manual': test_workflow_manual(),
        'UI Imports': test_ui_imports()
    }
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("="*80)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit(main())

#!/usr/bin/env python3
"""Verify all fixed Python files compile correctly"""

import py_compile
import sys

files = [
    'Root/integrated_workflow.py',
    'SecIDS-CNN/run_model.py',
    'SecIDS-CNN/train_and_test.py',
    'SecIDS-CNN/unified_wrapper.py',
    'SecIDS-CNN/secids_cnn.py',
    'Tools/pcap_to_secids_csv.py',
    'Tools/system_checker.py',
    'Tools/create_enhanced_dataset.py',
    'Tools/live_capture_and_assess.py',
    'Tools/vm_scanner.py',
    'Tools/continuous_live_capture.py',
    'Tools/threat_reviewer.py',
    'Tools/wireshark_manager.py',
    'Device_Profile/device_info/blacklist_manager.py',
    'Scripts/stress_test.py',
    'Scripts/organize_files.py',
    'Scripts/analyze_threat_origins.py',
    'Scripts/production_debug_scan.py',
    'Scripts/redundancy_detector.py',
    'Scripts/system_upgrade.py',
    'Scripts/optimize_system.py',
    'Countermeasures/ddos_countermeasure.py',
    'UI/terminal_ui_enhanced.py',
    'Auto_Update/task_scheduler.py'
]

errors = 0
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f'✓ {f}')
    except Exception as e:
        print(f'✗ {f}: {e}')
        errors += 1

print(f'\n{"="*70}')
print(f'Result: {len(files)-errors}/{len(files)} files compiled successfully')
if errors == 0:
    print('✓ All fixed files are error-free!')
else:
    print(f'✗ {errors} file(s) have errors')
print(f'{"="*70}')

sys.exit(errors)

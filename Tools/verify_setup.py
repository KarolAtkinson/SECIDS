#!/usr/bin/env python3
"""
Network interface discovery and verification utility for SecIDS-CNN.

Helps identify available network interfaces and test packet capture capabilities.
"""

import subprocess
import sys
import os
from pathlib import Path

def get_network_interfaces():
    """Get list of active network interfaces."""
    try:
        # Try using ip command (Linux)
        result = subprocess.run(['ip', 'link', 'show'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            interfaces = []
            for line in result.stdout.split('\n'):
                if ':' in line and not line.startswith(' '):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        iface = parts[1].strip()
                        interfaces.append(iface)
            return interfaces
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Fallback to ifconfig (BSD/macOS)
        result = subprocess.run(['ifconfig'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            interfaces = []
            for line in result.stdout.split('\n'):
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    iface = line.split(':')[0].strip()
                    if iface:
                        interfaces.append(iface)
            return list(set(interfaces))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return []

def test_interface_capture(iface):
    """Test if we can capture on this interface."""
    try:
        # Try dumpcap first (lighter weight)
        result = subprocess.run(['dumpcap', '-i', iface, '-a', 'duration:1', '-w', '/dev/null'],
                              capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            return 'dumpcap', True
        
        # Try tshark
        result = subprocess.run(['tshark', '-i', iface, '-a', 'duration:1', '-w', '/dev/null'],
                              capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            return 'tshark', True
        
    except Exception as e:
        if 'Permission denied' in str(e) or 'permission' in str(e).lower():
            return None, False
    
    return None, False

def check_scapy():
    """Check if Scapy is installed."""
    try:
        import scapy
        return True, scapy.__version__
    except ImportError:
        return False, None

def check_model_file():
    """Check if SecIDS-CNN model file exists."""
    model_path = Path(__file__).parent.parent / 'SecIDS-CNN' / 'SecIDS-CNN.h5'
    return model_path.exists(), str(model_path)

def check_requirements():
    """Check Python dependencies."""
    deps = {
        'pandas': None,
        'numpy': None,
        'tensorflow': None,
        'sklearn': None,
        'scapy': None,
    }
    
    for pkg in deps:
        try:
            if pkg == 'sklearn':
                __import__('sklearn')
            else:
                __import__(pkg)
            deps[pkg] = True
        except ImportError:
            deps[pkg] = False
    
    return deps

def main():
    print("="*80)
    print("SecIDS-CNN - Network Interface Discovery & Verification")
    print("="*80)
    print()
    
    # Check Python version
    print("Python Version:")
    print(f"  {sys.version.split()[0]}")
    print()
    
    # Check dependencies
    print("Python Dependencies:")
    deps = check_requirements()
    for pkg, status in deps.items():
        status_icon = "✓" if status else "✗"
        print(f"  {status_icon} {pkg}")
    
    missing = [p for p, s in deps.items() if not s]
    if missing:
        print(f"\n  Install missing: pip install {' '.join(missing)}")
    print()
    
    # Check model file
    print("SecIDS-CNN Model:")
    model_exists, model_path = check_model_file()
    status_icon = "✓" if model_exists else "✗"
    print(f"  {status_icon} {model_path}")
    print()
    
    # Check network interfaces
    print("Available Network Interfaces:")
    interfaces = get_network_interfaces()
    
    if not interfaces:
        print("  ✗ No interfaces found. Check system configuration.")
        sys.exit(1)
    
    print(f"  Found {len(interfaces)} interface(s):")
    for iface in sorted(interfaces):
        tool, can_capture = test_interface_capture(iface)
        if can_capture:
            status_icon = "✓"
            status = "Ready for capture"
        else:
            status_icon = "✗"
            status = "Permission denied (use sudo)"
        
        print(f"    {status_icon} {iface:10s} - {status}")
    print()
    
    # Recommendations
    print("Quick Start:")
    print()
    if interfaces:
        primary_iface = None
        for iface in ['eth0', 'en0', 'wlan0', 'en1', 'wifi0']:
            if iface in interfaces:
                primary_iface = iface
                break
        
        if not primary_iface:
            primary_iface = sorted(interfaces)[0]
        
        print(f"  Run continuous detection on {primary_iface}:")
        print(f"    sudo python3 SecIDS-CNN/run_model.py live --iface {primary_iface}")
        print()
        print("  Or with custom parameters:")
        print(f"    sudo python3 SecIDS-CNN/run_model.py live --iface {primary_iface} --window 3 --interval 1")
        print()
    
    print("For file-based analysis:")
    print("  python3 SecIDS-CNN/run_model.py file <csv_file>")
    print()
    print("="*80)

if __name__ == '__main__':
    main()

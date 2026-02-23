#!/usr/bin/env python3
"""
Whitelist/Blacklist Updater - Update lists based on VM scan results.

Updates whitelist and blacklist files based on VM scanner recommendations.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def update_lists_from_scan(scan_file):
    """Update whitelist/blacklist from scan results."""
    
    # Load scan results
    with open(scan_file, 'r') as f:
        scan_data = json.load(f)
    
    print(f"\n📊 Loaded scan from: {scan_data['scan_timestamp']}")
    print(f"   Whitelist candidates: {len(scan_data['whitelist_recommendations'])}")
    print(f"   Blacklist candidates: {len(scan_data['blacklist_recommendations'])}")
    
    # Paths
    device_profile_dir = Path(__file__).parent.parent / 'Device_Profile'
    whitelist_dir = device_profile_dir / 'whitelists'
    blacklist_dir = device_profile_dir / 'Blacklist'
    
    whitelist_dir.mkdir(parents=True, exist_ok=True)
    blacklist_dir.mkdir(parents=True, exist_ok=True)
    
    # Create whitelist file
    whitelist_file = whitelist_dir / f'whitelist_{datetime.now().strftime("%Y%m%d")}.json'
    whitelist_data = {
        'updated': datetime.now().isoformat(),
        'source': 'vm_scanner',
        'tools': [],
        'processes': []
    }
    
    for item in scan_data['whitelist_recommendations']:
        if item['type'] == 'tool':
            whitelist_data['tools'].append({
                'name': item['name'],
                'path': item['path'],
                'reason': item['reason']
            })
        elif item['type'] == 'process':
            whitelist_data['processes'].append({
                'name': item['name'],
                'command': item['command'][:200],  # Truncate long commands
                'reason': item['reason']
            })
    
    with open(whitelist_file, 'w') as f:
        json.dump(whitelist_data, f, indent=2)
    
    print(f"\n✅ Whitelist created: {whitelist_file}")
    print(f"   Tools: {len(whitelist_data['tools'])}")
    print(f"   Processes: {len(whitelist_data['processes'])}")
    
    # Create blacklist file
    blacklist_file = blacklist_dir / f'blacklist_{datetime.now().strftime("%Y%m%d")}.json'
    blacklist_data = {
        'updated': datetime.now().isoformat(),
        'source': 'vm_scanner',
        'flagged_items': []
    }
    
    for item in scan_data['blacklist_recommendations']:
        blacklist_data['flagged_items'].append({
            'type': item['type'],
            'name': item['name'],
            'pid': item.get('pid', 'N/A'),
            'command': item['command'][:200],  # Truncate long commands
            'reason': item['reason'],
            'status': 'flagged'  # User should review
        })
    
    with open(blacklist_file, 'w') as f:
        json.dump(blacklist_data, f, indent=2)
    
    print(f"\n⚠️  Blacklist created: {blacklist_file}")
    print(f"   Flagged items: {len(blacklist_data['flagged_items'])}")
    print(f"   Note: These are flagged for review, not auto-blocked")
    
    return whitelist_file, blacklist_file


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 update_lists.py <scan_file>")
        print("\nSearching for most recent scan...")
        
        scans_dir = Path(__file__).parent.parent / 'Device_Profile' / 'scans'
        scan_files = sorted(scans_dir.glob('vm_scan_*.json'), reverse=True)
        
        if scan_files:
            scan_file = scan_files[0]
            print(f"Found: {scan_file}")
        else:
            print("No scan files found. Run vm_scanner.py first.")
            return 1
    else:
        scan_file = Path(sys.argv[1])
    
    if not scan_file.exists():
        print(f"Error: Scan file not found: {scan_file}")
        return 1
    
    print("\n" + "="*80)
    print("WHITELIST/BLACKLIST UPDATER")
    print("="*80)
    
    whitelist_file, blacklist_file = update_lists_from_scan(scan_file)
    
    print("\n" + "="*80)
    print("UPDATE COMPLETE")
    print("="*80)
    print(f"\nWhitelist: {whitelist_file}")
    print(f"Blacklist: {blacklist_file}")
    print("\n💡 Review blacklisted items manually before taking action.")
    print("="*80 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

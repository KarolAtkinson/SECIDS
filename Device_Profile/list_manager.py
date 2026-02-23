#!/usr/bin/env python3
"""
List Manager Integration for SecIDS-CNN
========================================
Integrates greylist with existing whitelist and blacklist systems.
Manages transitions between lists and ensures consistency.

List Structure:
- Whitelist: Device_Profile/whitelists/
- Blacklist: Device_Profile/Blacklist/
- Greylist: Device_Profile/greylist/
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict


class ListManager:
    """
    Unified manager for whitelist, blacklist, and greylist
    Handles transitions and maintains consistency
    """
    
    def __init__(self, device_profile_dir: Path = None):
        """
        Initialize list manager
        
        Args:
            device_profile_dir: Path to Device_Profile directory
        """
        if device_profile_dir is None:
            self.device_profile_dir = Path(__file__).parent
        else:
            self.device_profile_dir = Path(device_profile_dir)
        
        # List directories
        self.whitelist_dir = self.device_profile_dir / 'whitelists'
        self.blacklist_dir = self.device_profile_dir / 'Blacklist'
        self.greylist_dir = self.device_profile_dir / 'greylist'
        
        # Ensure directories exist
        self.whitelist_dir.mkdir(exist_ok=True)
        self.blacklist_dir.mkdir(exist_ok=True)
        self.greylist_dir.mkdir(exist_ok=True)
        
        # List files
        self.whitelist_file = self.whitelist_dir / 'ip_whitelist.json'
        self.blacklist_file = self.blacklist_dir / 'ip_blacklist.json'
        self.greylist_file = self.greylist_dir / 'greylist.json'
        
        # In-memory lists
        self.whitelist = self.load_list(self.whitelist_file)
        self.blacklist = self.load_list(self.blacklist_file)
        self.greylist = self.load_list(self.greylist_file)
        
        print(f"✓ List Manager initialized")
        print(f"  Whitelist: {len(self.whitelist)} entries")
        print(f"  Blacklist: {len(self.blacklist)} entries")
        print(f"  Greylist: {len(self.greylist)} entries")
    
    def load_list(self, file_path: Path) -> Dict:
        """Load a list from file"""
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Convert list to dict if necessary
                    if isinstance(data, list):
                        return {item: {'added': datetime.now().isoformat()} for item in data}
                    return data
            except Exception as e:
                print(f"⚠️  Could not load {file_path.name}: {e}")
                return {}
        return {}
    
    def save_list(self, data: Dict, file_path: Path):
        """Save a list to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save {file_path.name}: {e}")
    
    def is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        return ip in self.whitelist
    
    def is_blacklisted(self, ip: str) -> bool:
        """Check if IP is blacklisted"""
        return ip in self.blacklist
    
    def is_greylisted(self, ip: str) -> bool:
        """Check if IP is greylisted"""
        return ip in self.greylist
    
    def get_ip_status(self, ip: str) -> str:
        """
        Get the current status of an IP
        
        Returns:
            'whitelist', 'blacklist', 'greylist', or 'unknown'
        """
        if self.is_whitelisted(ip):
            return 'whitelist'
        elif self.is_blacklisted(ip):
            return 'blacklist'
        elif self.is_greylisted(ip):
            return 'greylist'
        else:
            return 'unknown'
    
    def add_to_whitelist(self, ip: str, reason: str = None, metadata: Dict = None):
        """
        Add IP to whitelist and remove from other lists
        
        Args:
            ip: IP address
            reason: Reason for whitelisting
            metadata: Additional metadata
        """
        # Remove from other lists first
        self.remove_from_blacklist(ip)
        self.remove_from_greylist(ip)
        
        # Add to whitelist
        self.whitelist[ip] = {
            'added': datetime.now().isoformat(),
            'reason': reason or 'User verified',
            'metadata': metadata or {}
        }
        
        self.save_list(self.whitelist, self.whitelist_file)
        print(f"✓ Added {ip} to whitelist")
    
    def add_to_blacklist(self, ip: str, reason: str = None, metadata: Dict = None):
        """
        Add IP to blacklist and remove from other lists
        
        Args:
            ip: IP address
            reason: Reason for blacklisting
            metadata: Additional metadata
        """
        # Remove from other lists first
        self.remove_from_whitelist(ip)
        self.remove_from_greylist(ip)
        
        # Add to blacklist
        self.blacklist[ip] = {
            'added': datetime.now().isoformat(),
            'reason': reason or 'Threat detected',
            'metadata': metadata or {}
        }
        
        self.save_list(self.blacklist, self.blacklist_file)
        print(f"✓ Added {ip} to blacklist")
    
    def add_to_greylist(self, ip: str, reason: str = None, metadata: Dict = None):
        """
        Add IP to greylist and remove from other lists
        
        Args:
            ip: IP address
            reason: Reason for greylisting
            metadata: Additional metadata
        """
        # Remove from other lists first
        self.remove_from_whitelist(ip)
        self.remove_from_blacklist(ip)
        
        # Add to greylist
        self.greylist[ip] = {
            'added': datetime.now().isoformat(),
            'reason': reason or 'Potential threat - monitoring',
            'metadata': metadata or {}
        }
        
        self.save_list(self.greylist, self.greylist_file)
        print(f"✓ Added {ip} to greylist")
    
    def remove_from_whitelist(self, ip: str):
        """Remove IP from whitelist"""
        if ip in self.whitelist:
            del self.whitelist[ip]
            self.save_list(self.whitelist, self.whitelist_file)
    
    def remove_from_blacklist(self, ip: str):
        """Remove IP from blacklist"""
        if ip in self.blacklist:
            del self.blacklist[ip]
            self.save_list(self.blacklist, self.blacklist_file)
    
    def remove_from_greylist(self, ip: str):
        """Remove IP from greylist"""
        if ip in self.greylist:
            del self.greylist[ip]
            self.save_list(self.greylist, self.greylist_file)
    
    def move_to_whitelist(self, ip: str, reason: str = None, metadata: Dict = None):
        """
        Move IP from current list to whitelist
        
        Args:
            ip: IP address
            reason: Reason for moving
            metadata: Additional metadata
        """
        current_status = self.get_ip_status(ip)
        
        if current_status == 'whitelist':
            print(f"⚠️  {ip} already on whitelist")
            return
        
        # Get existing metadata if available
        existing_metadata = {}
        if current_status == 'greylist' and ip in self.greylist:
            existing_metadata = self.greylist[ip].get('metadata', {})
        elif current_status == 'blacklist' and ip in self.blacklist:
            existing_metadata = self.blacklist[ip].get('metadata', {})
        
        # Merge metadata
        if metadata:
            existing_metadata.update(metadata)
        
        # Add history
        existing_metadata['previous_status'] = current_status
        existing_metadata['moved_at'] = datetime.now().isoformat()
        
        self.add_to_whitelist(ip, reason, existing_metadata)
        print(f"→ Moved {ip} from {current_status} to whitelist")
    
    def move_to_blacklist(self, ip: str, reason: str = None, metadata: Dict = None):
        """
        Move IP from current list to blacklist
        
        Args:
            ip: IP address
            reason: Reason for moving
            metadata: Additional metadata
        """
        current_status = self.get_ip_status(ip)
        
        if current_status == 'blacklist':
            print(f"⚠️  {ip} already on blacklist")
            return
        
        # Get existing metadata if available
        existing_metadata = {}
        if current_status == 'greylist' and ip in self.greylist:
            existing_metadata = self.greylist[ip].get('metadata', {})
        elif current_status == 'whitelist' and ip in self.whitelist:
            existing_metadata = self.whitelist[ip].get('metadata', {})
        
        # Merge metadata
        if metadata:
            existing_metadata.update(metadata)
        
        # Add history
        existing_metadata['previous_status'] = current_status
        existing_metadata['moved_at'] = datetime.now().isoformat()
        
        self.add_to_blacklist(ip, reason, existing_metadata)
        print(f"→ Moved {ip} from {current_status} to blacklist")
    
    def move_to_greylist(self, ip: str, reason: str = None, metadata: Dict = None):
        """
        Move IP from current list to greylist
        
        Args:
            ip: IP address
            reason: Reason for moving
            metadata: Additional metadata
        """
        current_status = self.get_ip_status(ip)
        
        if current_status == 'greylist':
            print(f"⚠️  {ip} already on greylist")
            return
        
        # Get existing metadata if available
        existing_metadata = {}
        if current_status == 'whitelist' and ip in self.whitelist:
            existing_metadata = self.whitelist[ip].get('metadata', {})
        elif current_status == 'blacklist' and ip in self.blacklist:
            existing_metadata = self.blacklist[ip].get('metadata', {})
        
        # Merge metadata
        if metadata:
            existing_metadata.update(metadata)
        
        # Add history
        existing_metadata['previous_status'] = current_status
        existing_metadata['moved_at'] = datetime.now().isoformat()
        
        self.add_to_greylist(ip, reason, existing_metadata)
        print(f"→ Moved {ip} from {current_status} to greylist")
    
    def get_all_lists(self) -> Dict[str, List[str]]:
        """Get all lists"""
        return {
            'whitelist': list(self.whitelist.keys()),
            'blacklist': list(self.blacklist.keys()),
            'greylist': list(self.greylist.keys())
        }
    
    def get_status(self) -> Dict:
        """Get current status and statistics for all lists"""
        return {
            'whitelist_count': len(self.whitelist),
            'blacklist_count': len(self.blacklist),
            'greylist_count': len(self.greylist),
            'total_tracked': len(self.whitelist) + len(self.blacklist) + len(self.greylist),
            'whitelist_ips': list(self.whitelist.keys()),
            'blacklist_ips': list(self.blacklist.keys()),
            'greylist_ips': list(self.greylist.keys())
        }
    
    def export_report(self, output_file: Path = None) -> Path:
        """Export comprehensive list report"""
        if output_file is None:
            output_file = self.device_profile_dir / f'lists_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'whitelist_count': len(self.whitelist),
                'blacklist_count': len(self.blacklist),
                'greylist_count': len(self.greylist),
                'total_tracked': len(self.whitelist) + len(self.blacklist) + len(self.greylist)
            },
            'whitelist': self.whitelist,
            'blacklist': self.blacklist,
            'greylist': self.greylist
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Lists report exported to: {output_file}")
        return output_file


# Example usage
if __name__ == '__main__':
    print("="*80)
    print("  List Manager - Test Mode")
    print("="*80)
    
    # Initialize manager
    mgr = ListManager()
    
    # Test IP
    test_ip = '192.168.1.100'
    
    # Check status
    print(f"\nInitial status of {test_ip}: {mgr.get_ip_status(test_ip)}")
    
    # Add to greylist
    mgr.add_to_greylist(test_ip, "Detected suspicious activity")
    print(f"Status after greylist: {mgr.get_ip_status(test_ip)}")
    
    # Move to blacklist
    mgr.move_to_blacklist(test_ip, "Confirmed threat")
    print(f"Status after blacklist: {mgr.get_ip_status(test_ip)}")
    
    # Move to whitelist
    mgr.move_to_whitelist(test_ip, "False positive - verified safe")
    print(f"Status after whitelist: {mgr.get_ip_status(test_ip)}")
    
    # Show all lists
    print("\nAll lists:")
    lists = mgr.get_all_lists()
    for list_name, ips in lists.items():
        print(f"  {list_name}: {len(ips)} IPs")
    
    # Export report
    mgr.export_report()

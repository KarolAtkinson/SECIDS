#!/usr/bin/env python3
"""
Whitelist Checker
Validates traffic against local device profile and known organizations
"""

import json
import ipaddress
from pathlib import Path
from typing import Dict, List, Set, Optional

class WhitelistChecker:
    """Check if traffic is from trusted sources"""
    
    def __init__(self, device_profile_path=None, organizations_path=None):
        """
        Initialize whitelist checker
        
        Args:
            device_profile_path: Path to local device profile JSON
            organizations_path: Path to known organizations JSON
        """
        self.base_dir = Path(__file__).parent.parent
        
        if device_profile_path is None:
            device_profile_path = self.base_dir / 'device_info' / 'local_device.json'
        if organizations_path is None:
            organizations_path = self.base_dir / 'whitelists' / 'known_organizations.json'
        
        # Load configurations
        self.device_profile = self._load_json(device_profile_path)
        self.organizations = self._load_json(organizations_path)
        
        # Build lookup sets for fast checking
        self.local_ips = set(self.device_profile.get('local_ips', []))
        self.local_gateway = self.device_profile.get('default_gateway')
        self.local_dns = set(self.device_profile.get('dns_servers', []))
        
        # Build trusted IP ranges
        self.trusted_ip_ranges = []
        self.trusted_domains = set()
        self.trusted_dns_servers = set(self.organizations.get('common_dns_servers', []))
        
        for org_name, org_data in self.organizations.get('organizations', {}).items():
            if org_data.get('trusted', False):
                # Add domains
                self.trusted_domains.update(org_data.get('domains', []))
                
                # Add IP ranges
                for ip_range in org_data.get('ip_ranges', []):
                    try:
                        self.trusted_ip_ranges.append(ipaddress.ip_network(ip_range, strict=False))
                    except ValueError:
                        continue
    
    def _load_json(self, path):
        """Load JSON file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {path}: {e}")
            return {}
    
    def is_local_traffic(self, src_ip, dst_ip):
        """Check if traffic is local (same device or local network)"""
        # Check if source or destination is local IP
        if src_ip in self.local_ips or dst_ip in self.local_ips:
            return True
        
        # Check if communicating with gateway
        if src_ip == self.local_gateway or dst_ip == self.local_gateway:
            return True
        
        # Check if communicating with local DNS
        if src_ip in self.local_dns or dst_ip in self.local_dns:
            return True
        
        return False
    
    def is_trusted_ip(self, ip_address):
        """Check if IP is from a trusted organization"""
        # Check DNS servers
        if ip_address in self.trusted_dns_servers:
            return True
        
        # Check IP ranges
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            for ip_range in self.trusted_ip_ranges:
                if ip_obj in ip_range:
                    return True
        except ValueError:
            return False
        
        return False
    
    def is_trusted_port(self, port):
        """Check if port is commonly used for legitimate traffic"""
        # Common legitimate ports
        trusted_ports = {
            20, 21,    # FTP
            22,        # SSH
            25,        # SMTP
            53,        # DNS
            80,        # HTTP
            110,       # POP3
            123,       # NTP
            143,       # IMAP
            443,       # HTTPS
            465,       # SMTPS
            587,       # SMTP submission
            993,       # IMAPS
            995,       # POP3S
            3389,      # RDP
            5353,      # mDNS
            8080,      # HTTP alt
            8443       # HTTPS alt
        }
        
        return port in trusted_ports
    
    def check_flow(self, src_ip='unknown', dst_ip='unknown', dst_port=0, probability=0.0):
        """
        Check if a flow should be whitelisted
        
        Returns:
            dict: {
                'whitelisted': bool,
                'reason': str,
                'confidence': float
            }
        """
        reasons = []
        
        # Check local traffic
        if src_ip != 'unknown' and dst_ip != 'unknown':
            if self.is_local_traffic(src_ip, dst_ip):
                return {
                    'whitelisted': True,
                    'reason': 'Local device traffic',
                    'confidence': 1.0
                }
        
        # Check trusted IPs
        if src_ip != 'unknown' and self.is_trusted_ip(src_ip):
            reasons.append('Trusted source IP (known organization)')
        
        if dst_ip != 'unknown' and self.is_trusted_ip(dst_ip):
            reasons.append('Trusted destination IP (known organization)')
        
        # Check trusted port
        if self.is_trusted_port(dst_port):
            reasons.append(f'Standard service port ({dst_port})')
        
        # Decision logic
        if reasons:
            # If low threat probability and trusted characteristics, whitelist
            if probability < 0.7 and len(reasons) >= 2:
                return {
                    'whitelisted': True,
                    'reason': '; '.join(reasons),
                    'confidence': 0.8
                }
            
            # If medium threat but strong trust indicators, whitelist
            if probability < 0.9 and any('Trusted' in r for r in reasons):
                return {
                    'whitelisted': True,
                    'reason': '; '.join(reasons),
                    'confidence': 0.6
                }
        
        # Not whitelisted
        return {
            'whitelisted': False,
            'reason': 'No whitelist criteria matched',
            'confidence': 0.0
        }
    
    def get_statistics(self):
        """Get whitelist statistics"""
        return {
            'local_ips': len(self.local_ips),
            'trusted_organizations': len(self.organizations.get('organizations', {})),
            'trusted_ip_ranges': len(self.trusted_ip_ranges),
            'trusted_domains': len(self.trusted_domains),
            'trusted_dns_servers': len(self.trusted_dns_servers)
        }


if __name__ == '__main__':
    # Test whitelist checker
    checker = WhitelistChecker()
    
    print("Whitelist Checker Statistics:")
    stats = checker.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nTest Cases:")
    
    # Test local traffic
    result = checker.check_flow(src_ip='192.168.112.143', dst_ip='192.168.112.2', dst_port=53)
    print(f"1. Local DNS: {result}")
    
    # Test Google DNS
    result = checker.check_flow(src_ip='192.168.112.143', dst_ip='8.8.8.8', dst_port=53, probability=0.9)
    print(f"2. Google DNS: {result}")
    
    # Test HTTPS to Google
    result = checker.check_flow(src_ip='192.168.112.143', dst_ip='142.250.1.1', dst_port=443, probability=0.95)
    print(f"3. HTTPS to Google: {result}")
    
    # Test suspicious traffic
    result = checker.check_flow(src_ip='10.0.0.1', dst_ip='192.168.1.100', dst_port=12345, probability=0.99)
    print(f"4. Suspicious: {result}")

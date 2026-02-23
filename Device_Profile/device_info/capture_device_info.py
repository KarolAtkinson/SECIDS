#!/usr/bin/env python3
"""
Device Information Capture
Collects local device information for whitelisting legitimate traffic
"""

import json
import socket
import subprocess
import netifaces
from datetime import datetime
from pathlib import Path

def get_local_ips():
    """Get all local IP addresses"""
    ips = set()
    
    # Add localhost variants
    ips.add('127.0.0.1')
    ips.add('::1')
    ips.add('localhost')
    
    # Get all network interface IPs
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        
        # IPv4 addresses
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                ips.add(addr['addr'])
        
        # IPv6 addresses
        if netifaces.AF_INET6 in addrs:
            for addr in addrs[netifaces.AF_INET6]:
                # Remove zone identifier if present
                ipv6 = addr['addr'].split('%')[0]
                ips.add(ipv6)
    
    return sorted(list(ips))

def get_mac_addresses():
    """Get all MAC addresses"""
    macs = []
    
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        
        if netifaces.AF_LINK in addrs:
            for addr in addrs[netifaces.AF_LINK]:
                if 'addr' in addr and addr['addr'] != '00:00:00:00:00:00':
                    macs.append({
                        'interface': interface,
                        'mac': addr['addr']
                    })
    
    return macs

def get_hostname():
    """Get system hostname"""
    return socket.gethostname()

def get_default_gateway():
    """Get default gateway"""
    gateways = netifaces.gateways()
    if 'default' in gateways and netifaces.AF_INET in gateways['default']:
        return gateways['default'][netifaces.AF_INET][0]
    return None

def get_dns_servers():
    """Get DNS servers from resolv.conf"""
    dns_servers = []
    try:
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if line.startswith('nameserver'):
                    dns_servers.append(line.split()[1])
    except Exception as e:
        print(f"Could not read DNS servers: {e}")
    
    return dns_servers

def capture_device_profile():
    """Capture complete device profile"""
    profile = {
        'timestamp': datetime.now().isoformat(),
        'hostname': get_hostname(),
        'local_ips': get_local_ips(),
        'mac_addresses': get_mac_addresses(),
        'default_gateway': get_default_gateway(),
        'dns_servers': get_dns_servers(),
        'description': 'Local device profile for traffic whitelisting'
    }
    
    return profile

def save_device_profile(output_path=None):
    """Save device profile to JSON file"""
    if output_path is None:
        output_path = Path(__file__).parent / 'local_device.json'
    
    profile = capture_device_profile()
    
    with open(output_path, 'w') as f:
        json.dump(profile, f, indent=2)
    
    print(f"Device profile saved to: {output_path}")
    print(f"\nDevice Information:")
    print(f"  Hostname: {profile['hostname']}")
    print(f"  Local IPs: {len(profile['local_ips'])} addresses")
    for ip in profile['local_ips']:
        print(f"    - {ip}")
    print(f"  MAC Addresses: {len(profile['mac_addresses'])} interfaces")
    for mac in profile['mac_addresses']:
        print(f"    - {mac['interface']}: {mac['mac']}")
    print(f"  Default Gateway: {profile['default_gateway']}")
    print(f"  DNS Servers: {', '.join(profile['dns_servers'])}")
    
    return profile

if __name__ == '__main__':
    try:
        save_device_profile()
    except Exception as e:
        print(f"Error capturing device profile: {e}")
        import traceback
        traceback.print_exc()

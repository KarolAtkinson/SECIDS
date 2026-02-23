#!/usr/bin/env python3
"""
VM System Scanner - Comprehensive system and network tool discovery.

Scans the VM for:
- Running processes
- Installed network tools
- System services
- Listening ports
- Security tools

Generates whitelist/blacklist recommendations based on findings.
"""

import subprocess
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class VMScanner:
    """Comprehensive VM system scanner."""
    
    def __init__(self):
        self.results = {
            'scan_timestamp': datetime.now().isoformat(),
            'processes': [],
            'network_tools': [],
            'services': [],
            'listening_ports': [],
            'installed_packages': [],
            'whitelist_recommendations': [],
            'blacklist_recommendations': []
        }
        
        # Known security/network tools to whitelist
        self.known_good_tools = {
            'wireshark', 'tshark', 'dumpcap', 'tcpdump', 'nmap',
            'python3', 'python', 'bash', 'sh', 'systemd', 'ssh',
            'sshd', 'networkmanager', 'dhclient', 'dnsmasq',
            'avahi-daemon', 'cups', 'cron', 'rsyslog',
            'malwarebytes', 'mbam', 'mbamservice', 'mbamtray'  # Malwarebytes security scanner
        }
        
        # Suspicious patterns to flag
        self.suspicious_patterns = {
            'nc', 'netcat', 'reverse', 'shell', 'backdoor',
            'meterpreter', 'payload', 'exploit', 'rootkit'
        }
    
    def scan_all(self):
        """Run all scans."""
        print("\n" + "="*80)
        print("VM SYSTEM SCAN - SecIDS-CNN")
        print("="*80 + "\n")
        
        self.scan_processes()
        self.scan_network_tools()
        self.scan_services()
        self.scan_listening_ports()
        self.scan_installed_packages()
        self.generate_recommendations()
        
        return self.results
    
    def scan_processes(self):
        """Scan running processes."""
        print("🔍 Scanning running processes...")
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        self.results['processes'].append({
                            'user': parts[0],
                            'pid': parts[1],
                            'cpu': parts[2],
                            'mem': parts[3],
                            'command': parts[10]
                        })
                
                print(f"   Found {len(self.results['processes'])} running processes")
        except Exception as e:
            print(f"   ⚠️  Error scanning processes: {e}")
    
    def scan_network_tools(self):
        """Scan for installed network tools."""
        print("🔍 Scanning network tools...")
        
        tools_to_check = [
            'wireshark', 'tshark', 'dumpcap', 'tcpdump', 'nmap',
            'netstat', 'ss', 'ip', 'ifconfig', 'iptables',
            'nft', 'ufw', 'firewalld', 'nc', 'netcat',
            'curl', 'wget', 'dig', 'nslookup', 'host'
        ]
        
        found_tools = []
        for tool in tools_to_check:
            try:
                result = subprocess.run(
                    ['which', tool],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    path = result.stdout.strip()
                    found_tools.append({
                        'name': tool,
                        'path': path
                    })
            except Exception as e:
                pass  # Skip on error
        self.results['network_tools'] = found_tools
        print(f"   Found {len(found_tools)} network tools")
    
    def scan_services(self):
        """Scan system services."""
        print("🔍 Scanning system services...")
        try:
            result = subprocess.run(
                ['systemctl', 'list-units', '--type=service', '--no-pager'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '.service' in line and 'loaded' in line:
                        parts = line.split()
                        if parts:
                            service_name = parts[0]
                            status = 'active' if 'active' in line else 'inactive'
                            self.results['services'].append({
                                'name': service_name,
                                'status': status
                            })
                
                active_count = sum(1 for s in self.results['services'] if s['status'] == 'active')
                print(f"   Found {len(self.results['services'])} services ({active_count} active)")
        except Exception as e:
            print(f"   ⚠️  Error scanning services: {e}")
    
    def scan_listening_ports(self):
        """Scan listening network ports."""
        print("🔍 Scanning listening ports...")
        try:
            result = subprocess.run(
                ['ss', '-tulnp'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if 'LISTEN' in line or 'UNCONN' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            self.results['listening_ports'].append({
                                'protocol': parts[0],
                                'local_address': parts[4],
                                'state': parts[1] if len(parts) > 1 else 'UNKNOWN'
                            })
                
                print(f"   Found {len(self.results['listening_ports'])} listening ports")
        except Exception as e:
            print(f"   ⚠️  Error scanning ports: {e}")
    
    def scan_installed_packages(self):
        """Scan installed packages (Debian/Ubuntu)."""
        print("🔍 Scanning installed packages...")
        try:
            # Try dpkg for Debian/Ubuntu/Kali
            result = subprocess.run(
                ['dpkg', '-l'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('ii'):  # Installed packages
                        parts = line.split()
                        if len(parts) >= 3:
                            self.results['installed_packages'].append({
                                'name': parts[1],
                                'version': parts[2]
                            })
                
                print(f"   Found {len(self.results['installed_packages'])} installed packages")
        except Exception as e:
            print(f"   ⚠️  Error scanning packages: {e}")
    
    def generate_recommendations(self):
        """Generate whitelist/blacklist recommendations."""
        print("\n🤖 Generating recommendations...")
        
        # Check processes for whitelisting/blacklisting
        for proc in self.results['processes']:
            cmd = proc['command'].lower()
            proc_name = cmd.split()[0] if cmd.split() else ''
            
            # Check if it's a known good tool
            is_known_good = any(tool in proc_name for tool in self.known_good_tools)
            
            # Check for suspicious patterns
            is_suspicious = any(pattern in cmd for pattern in self.suspicious_patterns)
            
            if is_suspicious:
                self.results['blacklist_recommendations'].append({
                    'type': 'process',
                    'name': proc_name,
                    'pid': proc['pid'],
                    'command': proc['command'],
                    'reason': 'Suspicious pattern detected'
                })
            elif is_known_good and 'python' in proc_name and 'secids' in cmd:
                self.results['whitelist_recommendations'].append({
                    'type': 'process',
                    'name': proc_name,
                    'pid': proc['pid'],
                    'command': proc['command'],
                    'reason': 'SecIDS-CNN related process'
                })
            elif is_known_good:
                self.results['whitelist_recommendations'].append({
                    'type': 'process',
                    'name': proc_name,
                    'pid': proc['pid'],
                    'command': proc['command'][:100],  # Truncate long commands
                    'reason': 'Known security/network tool'
                })
        
        # Whitelist network tools
        for tool in self.results['network_tools']:
            if tool['name'] in self.known_good_tools:
                self.results['whitelist_recommendations'].append({
                    'type': 'tool',
                    'name': tool['name'],
                    'path': tool['path'],
                    'reason': 'Required network/security tool'
                })
        
        print(f"   ✅ Whitelist recommendations: {len(self.results['whitelist_recommendations'])}")
        print(f"   ⚠️  Blacklist recommendations: {len(self.results['blacklist_recommendations'])}")
    
    def save_results(self, output_dir=None):
        """Save scan results to JSON."""
        if output_dir is None:
            output_dir = Path.cwd() / 'Device_Profile' / 'scans'
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'vm_scan_{timestamp}.json'
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Scan results saved to: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print scan summary."""
        print("\n" + "="*80)
        print("SCAN SUMMARY")
        print("="*80)
        print(f"Processes:              {len(self.results['processes'])}")
        print(f"Network Tools:          {len(self.results['network_tools'])}")
        print(f"Services:               {len(self.results['services'])}")
        print(f"Listening Ports:        {len(self.results['listening_ports'])}")
        print(f"Installed Packages:     {len(self.results['installed_packages'])}")
        print(f"\nWhitelist Candidates:   {len(self.results['whitelist_recommendations'])}")
        print(f"Blacklist Candidates:   {len(self.results['blacklist_recommendations'])}")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    scanner = VMScanner()
    results = scanner.scan_all()
    scanner.print_summary()
    output_file = scanner.save_results()
    
    # Ask if user wants to see detailed results
    print("\n📊 Would you like to see detailed results? (y/n): ", end='')
    try:
        response = input().strip().lower()
        if response == 'y':
            print(f"\n{json.dumps(results, indent=2)}")
    except Exception as e:
            pass  # Skip on error
    return 0


if __name__ == '__main__':
    sys.exit(main())

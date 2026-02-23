#!/usr/bin/env python3
"""
DDoS Countermeasure System
Real-time attack mitigation during live packet capture
Now with whitelist/blacklist/greylist integration
"""

import os
import sys
import time
import subprocess
import threading
import queue
from datetime import datetime
from collections import defaultdict, deque
from pathlib import Path


# Import list manager for whitelist/blacklist/greylist checking
try:
    device_profile_path = Path(__file__).parent.parent / 'Device_Profile'
    sys.path.insert(0, str(device_profile_path))
    from list_manager import ListManager
    LIST_MANAGER_AVAILABLE = True
except ImportError:
    LIST_MANAGER_AVAILABLE = False


class DDoSCountermeasure:
    """
    Real-time DDoS attack countermeasure system
    Runs in parallel with threat detection and takes immediate action
    """
    
    def __init__(self, 
                 block_threshold=5,
                 time_window=120,
                 auto_block=True,
                 log_file=None):
        """
        Initialize countermeasure system
        
        Args:
            block_threshold: Number of threats before blocking (default: 5)
            time_window: Time window in seconds for threat counting (default: 60)
            auto_block: Automatically block threats (default: True)
            log_file: Path to log file
        """
        self.block_threshold = block_threshold
        self.time_window = time_window
        self.auto_block = auto_block
        
        # Initialize list manager for whitelist/blacklist/greylist integration
        if LIST_MANAGER_AVAILABLE:
            try:
                self.list_manager = ListManager()
                self.log("List Manager integration enabled", "INFO")
            except Exception as e:
                self.log(f"Could not initialize List Manager: {e}", "WARNING")
                self.list_manager = None
        else:
            self.list_manager = None
        
        # Threat tracking
        self.threat_history = defaultdict(lambda: deque(maxlen=100))
        self.blocked_ips = set()
        self.blocked_ports = set()
        
        # Action queue for thread-safe operations
        self.action_queue = queue.Queue()
        
        # Statistics
        self.stats = {
            'threats_detected': 0,
            'threats_whitelisted': 0,
            'threats_greylisted': 0,
            'ips_blocked': 0,
            'ports_blocked': 0,
            'actions_taken': 0,
            'start_time': datetime.now()
        }
        
        # Logging
        if log_file is None:
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"countermeasures_{timestamp}.log"
        
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Worker thread
        self.running = False
        self.worker_thread = None
        
        self.log(f"Countermeasure system initialized")
        self.log(f"Block threshold: {block_threshold} threats in {time_window}s")
        self.log(f"Auto-block: {auto_block}")
    
    def log(self, message, level="INFO"):
        """Write to log file and print"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            pass  # Skip on error
    def start(self):
        """Start the countermeasure worker thread"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        self.log("Countermeasure worker thread started")
    
    def stop(self):
        """Stop the countermeasure worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.log("Countermeasure worker thread stopped")
    
    def _worker(self):
        """Worker thread that processes countermeasure actions"""
        while self.running:
            try:
                # Process actions from queue with timeout
                try:
                    action = self.action_queue.get(timeout=1)
                    self._execute_action(action)
                    self.action_queue.task_done()
                except queue.Empty:
                    continue
            except Exception as e:
                self.log(f"Worker error: {e}", "ERROR")
    
    def _execute_action(self, action):
        """Execute a countermeasure action"""
        action_type = action.get('type')
        
        if action_type == 'block_ip':
            self._block_ip(action['ip'], action.get('reason', 'DDoS attack'))
        elif action_type == 'block_port':
            self._block_port(action['port'], action.get('reason', 'DDoS attack'))
        elif action_type == 'rate_limit_ip':
            self._rate_limit_ip(action['ip'], action.get('limit', 10))
        elif action_type == 'alert':
            self.log(f"⚠️  ALERT: {action['message']}", "ALERT")
        
        self.stats['actions_taken'] += 1
    
    def _block_ip(self, ip, reason):
        """Block an IP address using iptables"""
        if ip in self.blocked_ips:
            return
        
        try:
            # Add iptables rule to drop packets from this IP
            cmd = ['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.blocked_ips.add(ip)
                self.stats['ips_blocked'] += 1
                self.log(f"🚫 BLOCKED IP: {ip} - Reason: {reason}", "ACTION")
            else:
                self.log(f"Failed to block IP {ip}: {result.stderr}", "ERROR")
        except subprocess.TimeoutExpired:
            self.log(f"Timeout blocking IP {ip}", "ERROR")
        except Exception as e:
            self.log(f"Error blocking IP {ip}: {e}", "ERROR")
    
    def _block_port(self, port, reason):
        """Block traffic to a specific port using iptables"""
        if port in self.blocked_ports:
            return
        
        try:
            # Add iptables rule to drop packets to this port
            cmd = ['sudo', 'iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', str(port), '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.blocked_ports.add(port)
                self.stats['ports_blocked'] += 1
                self.log(f"🚫 BLOCKED PORT: {port} - Reason: {reason}", "ACTION")
            else:
                self.log(f"Failed to block port {port}: {result.stderr}", "ERROR")
        except subprocess.TimeoutExpired:
            self.log(f"Timeout blocking port {port}", "ERROR")
        except Exception as e:
            self.log(f"Error blocking port {port}: {e}", "ERROR")
    
    def _rate_limit_ip(self, ip, limit):
        """Apply rate limiting to an IP address"""
        try:
            # Use iptables with hashlimit module for rate limiting
            cmd = [
                'sudo', 'iptables', '-A', 'INPUT',
                '-s', ip,
                '-m', 'hashlimit',
                '--hashlimit-above', f'{limit}/sec',
                '--hashlimit-mode', 'srcip',
                '--hashlimit-name', 'ddos_protection',
                '-j', 'DROP'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.log(f"⚡ RATE LIMITED IP: {ip} to {limit} conn/sec", "ACTION")
            else:
                self.log(f"Failed to rate limit IP {ip}: {result.stderr}", "ERROR")
        except Exception as e:
            self.log(f"Error rate limiting IP {ip}: {e}", "ERROR")
    
    def process_threat(self, threat_data):
        """
        Process a detected threat and decide on countermeasures
        
        Args:
            threat_data: Dictionary containing threat information
                - src_ip: Source IP address
                - dst_ip: Destination IP address
                - dst_port: Destination port
                - protocol: Protocol (TCP/UDP)
                - probability: Threat probability (0-1)
                - flow_packets: Number of packets in flow
                - flow_bytes: Number of bytes in flow
        """
        self.stats['threats_detected'] += 1
        
        src_ip = threat_data.get('src_ip', 'unknown')
        dst_port = threat_data.get('dst_port', 0)
        probability = threat_data.get('probability', 0)
        timestamp = time.time()
        
        # Check whitelist/blacklist/greylist status
        if self.list_manager:
            ip_status = self.list_manager.get_ip_status(src_ip)
            
            if ip_status == 'whitelist':
                self.log(f"✓ Skipping countermeasure for whitelisted IP: {src_ip}", "INFO")
                self.stats['threats_whitelisted'] += 1
                return
            
            elif ip_status == 'greylist':
                self.log(f"⚠️  Skipping countermeasure for greylisted IP: {src_ip} - awaiting user decision", "WARNING")
                self.stats['threats_greylisted'] += 1
                return
            
            # If blacklisted or unknown, proceed with countermeasures
        
        # Record threat
        self.threat_history[src_ip].append({
            'timestamp': timestamp,
            'port': dst_port,
            'probability': probability,
            'data': threat_data
        })
        
        # Count recent threats from this IP
        recent_threats = [
            t for t in self.threat_history[src_ip]
            if timestamp - t['timestamp'] <= self.time_window
        ]
        
        threat_count = len(recent_threats)
        
        # Determine if countermeasures are needed
        if threat_count >= self.block_threshold:
            # Multiple threats detected - take action
            
            if self.auto_block:
                # Block the source IP
                self.action_queue.put({
                    'type': 'block_ip',
                    'ip': src_ip,
                    'reason': f'{threat_count} DDoS threats detected in {self.time_window}s'
                })
                
                # Also consider blocking the destination port if under heavy attack
                port_threats = sum(1 for t in recent_threats if t['port'] == dst_port)
                if port_threats >= self.block_threshold:
                    self.action_queue.put({
                        'type': 'block_port',
                        'port': dst_port,
                        'reason': f'{port_threats} DDoS threats to port {dst_port}'
                    })
            else:
                # Just alert without blocking
                self.action_queue.put({
                    'type': 'alert',
                    'message': f'High threat volume from {src_ip}: {threat_count} threats in {self.time_window}s'
                })
        
        elif threat_count >= self.block_threshold // 2 and probability > 0.8:
            # Medium threat level - apply rate limiting
            if self.auto_block and src_ip not in self.blocked_ips:
                self.action_queue.put({
                    'type': 'rate_limit_ip',
                    'ip': src_ip,
                    'limit': 10  # 10 connections per second
                })
    
    def unblock_ip(self, ip):
        """Remove IP block"""
        if ip not in self.blocked_ips:
            return
        
        try:
            cmd = ['sudo', 'iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.blocked_ips.remove(ip)
                self.log(f"✅ UNBLOCKED IP: {ip}", "ACTION")
            else:
                self.log(f"Failed to unblock IP {ip}: {result.stderr}", "ERROR")
        except Exception as e:
            self.log(f"Error unblocking IP {ip}: {e}", "ERROR")
    
    def unblock_port(self, port):
        """Remove port block"""
        if port not in self.blocked_ports:
            return
        
        try:
            cmd = ['sudo', 'iptables', '-D', 'INPUT', '-p', 'tcp', '--dport', str(port), '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.blocked_ports.remove(port)
                self.log(f"✅ UNBLOCKED PORT: {port}", "ACTION")
            else:
                self.log(f"Failed to unblock port {port}: {result.stderr}", "ERROR")
        except Exception as e:
            self.log(f"Error unblocking port {port}: {e}", "ERROR")
    
    def clear_all_blocks(self):
        """Remove all blocks"""
        self.log("Clearing all blocks...")
        
        for ip in list(self.blocked_ips):
            self.unblock_ip(ip)
        
        for port in list(self.blocked_ports):
            self.unblock_port(port)
        
        self.log("All blocks cleared")
    
    def get_statistics(self):
        """Get countermeasure statistics"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'runtime_seconds': runtime,
            'threats_detected': self.stats['threats_detected'],
            'ips_blocked': self.stats['ips_blocked'],
            'ports_blocked': self.stats['ports_blocked'],
            'actions_taken': self.stats['actions_taken'],
            'currently_blocked_ips': len(self.blocked_ips),
            'currently_blocked_ports': len(self.blocked_ports),
            'threats_per_minute': (self.stats['threats_detected'] / runtime * 60) if runtime > 0 else 0
        }
    
    def print_statistics(self):
        """Print statistics"""
        stats = self.get_statistics()
        
        print()
        print("=" * 80)
        print("COUNTERMEASURE STATISTICS")
        print("=" * 80)
        print(f"Runtime: {stats['runtime_seconds']:.1f} seconds")
        print(f"Threats detected: {stats['threats_detected']}")
        print(f"IPs blocked: {stats['ips_blocked']}")
        print(f"Ports blocked: {stats['ports_blocked']}")
        print(f"Total actions taken: {stats['actions_taken']}")
        print(f"Currently blocked IPs: {stats['currently_blocked_ips']}")
        print(f"Currently blocked ports: {stats['currently_blocked_ports']}")
        print(f"Threat rate: {stats['threats_per_minute']:.1f} threats/minute")
        print("=" * 80)
        print()


def test_countermeasure():
    """Test the countermeasure system"""
    print("Testing DDoS Countermeasure System")
    print("=" * 80)
    
    cm = DDoSCountermeasure(
        block_threshold=3,
        time_window=10,
        auto_block=False  # Disable auto-block for testing
    )
    
    cm.start()
    
    # Simulate threat detections
    test_threats = [
        {'src_ip': '192.168.1.100', 'dst_port': 80, 'probability': 0.9},
        {'src_ip': '192.168.1.100', 'dst_port': 80, 'probability': 0.85},
        {'src_ip': '192.168.1.101', 'dst_port': 443, 'probability': 0.75},
        {'src_ip': '192.168.1.100', 'dst_port': 80, 'probability': 0.95},
    ]
    
    for i, threat in enumerate(test_threats, 1):
        print(f"\nProcessing threat {i}: {threat}")
        cm.process_threat(threat)
        time.sleep(1)
    
    # Wait for actions to complete
    cm.action_queue.join()
    
    cm.print_statistics()
    cm.stop()
    
    print("\n✅ Test completed")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_countermeasure()
    else:
        print("DDoS Countermeasure System")
        print("This module is designed to be imported and used with live detection")
        print("\nRun with --test to test the system")

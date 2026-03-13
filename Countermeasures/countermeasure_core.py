#!/usr/bin/env python3
"""
DDoS Countermeasure Core System
================================
Base functionality for Active and Passive modes.
Streamlined for essential operations only (Master-Manual documented features).

Core Features:
- IP/Port blocking via iptables
- Whitelist/Blacklist/Greylist integration
- Thread-safe operation
- Statistics tracking
- Configurable thresholds
"""

import sys
import time
import subprocess
import threading
import queue
from datetime import datetime
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, Optional, Set


# Import list manager for whitelist/blacklist/greylist
try:
    device_profile_path = Path(__file__).parent.parent / 'Device_Profile'
    sys.path.insert(0, str(device_profile_path))
    from list_manager import ListManager
    LIST_MANAGER_AVAILABLE = True
except ImportError:
    LIST_MANAGER_AVAILABLE = False


class CountermeasureCore:
    """
    Core countermeasure functionality
    Base class for Active and Passive modes
    """
    
    def __init__(self,
                 mode: str = "passive",
                 block_threshold: int = 5,
                 time_window: int = 60,
                 auto_block: bool = True,
                 log_file: Optional[Path] = None):
        """
        Initialize core countermeasure system
        
        Args:
            mode: Operating mode ('active' or 'passive')
            block_threshold: Threats before blocking (default: 5)
            time_window: Time window in seconds (default: 60)
            auto_block: Auto-block threats (default: True)
            log_file: Path to log  file
        """
        self.mode = mode
        self.block_threshold = block_threshold
        self.time_window = time_window
        self.auto_block = auto_block
        
        # Initialize list manager
        self.list_manager = None
        if LIST_MANAGER_AVAILABLE:
            try:
                self.list_manager = ListManager()
            except Exception as e:
                self._log(f"List Manager init failed: {e}", "WARNING")
        
        # Threat tracking
        self.threat_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.blocked_ips: Set[str] = set()
        self.blocked_ports: Set[int] = set()
        
        # Action queue (thread-safe)
        self.action_queue: queue.Queue = queue.Queue()
        
        # Statistics
        self.stats = {
            'threats_detected': 0,
            'threats_whitelisted': 0,
            'threats_greylisted': 0,
            'ips_blocked': 0,
            'ports_blocked': 0,
            'actions_taken': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Logging
        if log_file is None:
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"countermeasure_{mode}_{timestamp}.log"
        
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Worker thread
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        
        # Check sudo privileges if auto-blocking is enabled
        self.sudo_available = self._check_sudo_privileges()
        if auto_block and not self.sudo_available:
            self._log("WARNING: Auto-blocking enabled but sudo privileges not available", "WARNING")
            self._log("Run with sudo or configure passwordless sudo (see setup_passwordless_sudo.sh)", "WARNING")
        
        self._log(f"Countermeasure system initialized [{mode.upper()} MODE]")
        self._log(f"Threshold: {block_threshold} threats in {time_window}s")
        self._log(f"Auto-block: {auto_block}")
        self._log(f"Sudo available: {self.sudo_available}")
    
    def _check_sudo_privileges(self) -> bool:
        """Check if sudo privileges are available for iptables"""
        try:
            # Try to run iptables with sudo (list rules, doesn't modify anything)
            result = subprocess.run(
                ['sudo', '-n', 'iptables', '-L'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def _log(self, message: str, level: str = "INFO"):
        """Write to log file and optionally print"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Print to console (can be overridden by subclasses)
        if self.mode == "active":
            print(log_entry)
        
        # Write to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except (OSError, IOError) as exc:
            print(f"[{timestamp}] [WARNING] Log file write failed: {exc}")
    
    def start(self):
        """Start the countermeasure worker thread"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        self._log("Worker thread started")
    
    def stop(self):
        """Stop the countermeasure worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self._log("Worker thread stopped")
    
    def _worker(self):
        """Worker thread that processes countermeasure actions"""
        while self.running:
            try:
                action = self.action_queue.get(timeout=1)
                self._execute_action(action)
                self.action_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self._log(f"Worker error: {e}", "ERROR")
                self.stats['errors'] += 1
    
    def _execute_action(self, action: Dict):
        """Execute a countermeasure action"""
        action_type = action.get('type')
        
        if action_type == 'block_ip':
            self._block_ip(action['ip'], action.get('reason', 'DDoS detected'))
        elif action_type == 'block_port':
            self._block_port(action['port'], action.get('reason', 'Port under attack'))
        elif action_type == 'alert':
            self._log(f"ALERT: {action['message']}", "ALERT")
        
        self.stats['actions_taken'] += 1
    
    def _block_ip(self, ip: str, reason: str):
        """Block an IP address using iptables"""
        if ip in self.blocked_ips:
            return
        
        # Check sudo availability
        if not self.sudo_available:
            self._log(f"SKIPPED blocking IP {ip}: sudo not available", "WARNING")
            self.stats['errors'] += 1
            return
        
        try:
            cmd = ['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.blocked_ips.add(ip)
                self.stats['ips_blocked'] += 1
                self._log(f"BLOCKED IP: {ip} - {reason}", "ACTION")
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self._log(f"Failed to block IP {ip}: {error_msg}", "ERROR")
                self.stats['errors'] += 1
        except subprocess.TimeoutExpired:
            self._log(f"Timeout blocking IP {ip} (sudo password required?)", "ERROR")
            self.stats['errors'] += 1
        except Exception as e:
            self._log(f"Error blocking IP {ip}: {e}", "ERROR")
            self.stats['errors'] += 1
    
    def _block_port(self, port: int, reason: str):
        """Block traffic to a specific port using iptables"""
        if port in self.blocked_ports:
            return
        
        # Check sudo availability
        if not self.sudo_available:
            self._log(f"SKIPPED blocking port {port}: sudo not available", "WARNING")
            self.stats['errors'] += 1
            return
        
        try:
            cmd = ['sudo', 'iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', str(port), '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.blocked_ports.add(port)
                self.stats['ports_blocked'] += 1
                self._log(f"BLOCKED PORT: {port} - {reason}", "ACTION")
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self._log(f"Failed to block port {port}: {error_msg}", "ERROR")
                self.stats['errors'] += 1
        except subprocess.TimeoutExpired:
            self._log(f"Timeout blocking port {port} (sudo password required?)", "ERROR")
            self.stats['errors'] += 1
        except Exception as e:
            self._log(f"Error blocking port {port}: {e}", "ERROR")
            self.stats['errors'] += 1
    
    def process_threat(self, threat_data: Dict):
        """
        Process a detected threat and decide on countermeasures
        
        Args:
            threat_data: Dictionary with threat information
                - src_ip: Source IP address
                - dst_port: Destination port
                - probability: Threat probability (0-1)
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
                self.stats['threats_whitelisted'] += 1
                return
            elif ip_status == 'greylist':
                self.stats['threats_greylisted'] += 1
                return
        
        # Record threat
        self.threat_history[src_ip].append({
            'timestamp': timestamp,
            'port': dst_port,
            'probability': probability
        })
        
        # Count recent threats
        recent_threats = [
            t for t in self.threat_history[src_ip]
            if timestamp - t['timestamp'] <= self.time_window
        ]
        
        threat_count = len(recent_threats)
        
        # Determine action
        if threat_count >= self.block_threshold and self.auto_block:
            # Block the source IP
            self.action_queue.put({
                'type': 'block_ip',
                'ip': src_ip,
                'reason': f'{threat_count} threats in {self.time_window}s'
            })
            
            # Block port if under heavy attack
            port_threats = sum(1 for t in recent_threats if t['port'] == dst_port)
            if port_threats >= self.block_threshold:
                self.action_queue.put({
                    'type': 'block_port',
                    'port': dst_port,
                    'reason': f'{port_threats} threats to port {dst_port}'
                })
        elif threat_count >= self.block_threshold // 2:
            # Alert only (not enough for blocking)
            self.action_queue.put({
                'type': 'alert',
                'message': f'Elevated threat from {src_ip}: {threat_count} threats'
            })
    
    def unblock_ip(self, ip: str):
        """Remove IP block"""
        if ip not in self.blocked_ips:
            return
        
        try:
            cmd = ['sudo', 'iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.blocked_ips.remove(ip)
                self._log(f"UNBLOCKED IP: {ip}", "ACTION")
        except Exception as e:
            self._log(f"Error unblocking IP {ip}: {e}", "ERROR")
            self.stats['errors'] += 1
    
    def unblock_port(self, port: int):
        """Remove port block"""
        if port not in self.blocked_ports:
            return
        
        try:
            cmd = ['sudo', 'iptables', '-D', 'INPUT', '-p', 'tcp', '--dport', str(port), '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.blocked_ports.remove(port)
                self._log(f"UNBLOCKED PORT: {port}", "ACTION")
        except Exception as e:
            self._log(f"Error unblocking port {port}: {e}", "ERROR")
            self.stats['errors'] += 1
    
    def clear_all_blocks(self):
        """Remove all blocks"""
        self._log("Clearing all blocks...")
        
        for ip in list(self.blocked_ips):
            self.unblock_ip(ip)
        
        for port in list(self.blocked_ports):
            self.unblock_port(port)
        
        self._log("All blocks cleared")
    
    def get_statistics(self) -> Dict:
        """Get countermeasure statistics"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'runtime_seconds': runtime,
            'threats_detected': self.stats['threats_detected'],
            'threats_whitelisted': self.stats['threats_whitelisted'],
            'threats_greylisted': self.stats['threats_greylisted'],
            'ips_blocked': self.stats['ips_blocked'],
            'ports_blocked': self.stats['ports_blocked'],
            'currently_blocked_ips': len(self.blocked_ips),
            'currently_blocked_ports': len(self.blocked_ports),
            'actions_taken': self.stats['actions_taken'],
            'errors': self.stats['errors'],
            'threats_per_minute': (self.stats['threats_detected'] / runtime * 60) if runtime > 0 else 0
        }
    
    def get_status(self) -> Dict:
        """Get current operational status"""
        return {
            'mode': self.mode,
            'running': self.running,
            'auto_block': self.auto_block,
            'block_threshold': self.block_threshold,
            'time_window': self.time_window,
            'list_manager_active': self.list_manager is not None,
            'whitelist_size': len(self.list_manager.whitelist) if self.list_manager else 0,
            'blacklist_size': len(self.list_manager.blacklist) if self.list_manager else 0,
            'greylist_size': len(self.list_manager.greylist) if self.list_manager else 0
        }

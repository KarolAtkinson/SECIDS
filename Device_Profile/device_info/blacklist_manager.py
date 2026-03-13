#!/usr/bin/env python3
"""
Blacklist Manager
Tracks confirmed threats and malicious sources
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class BlacklistManager:
    """Manages blacklisted threats and attack sources"""
    
    def __init__(self, blacklist_dir=None):
        """
        Initialize blacklist manager
        
        Args:
            blacklist_dir: Path to blacklist directory
        """
        if blacklist_dir is None:
            blacklist_dir = Path(__file__).parent.parent / 'Blacklist'
        
        self.blacklist_dir = Path(blacklist_dir)
        self.threat_profiles_dir = self.blacklist_dir / 'threat_profiles'
        self.blocked_ips_file = self.blacklist_dir / 'blocked_ips' / 'blocked_ips.json'
        self.attack_patterns_file = self.blacklist_dir / 'attack_patterns' / 'patterns.json'
        
        # Ensure directories exist
        self.threat_profiles_dir.mkdir(parents=True, exist_ok=True)
        self.blocked_ips_file.parent.mkdir(parents=True, exist_ok=True)
        self.attack_patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self.blocked_ips = self._load_blocked_ips()
        self.attack_patterns = self._load_attack_patterns()
    
    def _load_blocked_ips(self):
        """Load blocked IPs from file"""
        if self.blocked_ips_file.exists():
            try:
                with open(self.blocked_ips_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load blocked IPs: {e}")
                return {}
        return {}
    
    def _save_blocked_ips(self):
        """Save blocked IPs to file"""
        with open(self.blocked_ips_file, 'w') as f:
            json.dump(self.blocked_ips, f, indent=2, default=str)
    
    def _load_attack_patterns(self):
        """Load attack patterns from file"""
        if self.attack_patterns_file.exists():
            try:
                with open(self.attack_patterns_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load attack patterns: {e}")
                return []
        return []
    
    def _save_attack_patterns(self):
        """Save attack patterns to file"""
        with open(self.attack_patterns_file, 'w') as f:
            json.dump(self.attack_patterns, f, indent=2, default=str)
    
    def _generate_threat_id(self, src_ip, dst_port, timestamp):
        """Generate unique threat ID"""
        data = f"{src_ip}_{dst_port}_{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def add_threat(self, threat_data):
        """
        Add confirmed threat to blacklist with comprehensive data collection
        
        Args:
            threat_data: Dict containing all available threat information
                - src_ip: Source IP address
                - dst_ip: Destination IP
                - dst_port: Destination port
                - src_port: Source port
                - protocol: Protocol (TCP/UDP/ICMP)
                - probability: Threat probability
                - flow_packets: Number of packets
                - flow_bytes: Number of bytes
                - attack_type: Type of attack (optional)
                - flow_features: Complete flow feature set from model
                - additional_info: Any additional data
        
        Returns:
            str: Threat ID
        """
        timestamp = datetime.now().isoformat()
        src_ip = threat_data.get('src_ip', 'unknown')
        dst_port = threat_data.get('dst_port', 0)
        
        # Generate unique ID
        threat_id = self._generate_threat_id(src_ip, dst_port, timestamp)
        
        # Collect ALL available passive information (no active probing)
        threat_profile = {
            'threat_id': threat_id,
            'timestamp': timestamp,
            'detection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # Network Layer Info
            'network': {
                'src_ip': src_ip,
                'dst_ip': threat_data.get('dst_ip', 'unknown'),
                'src_port': threat_data.get('src_port', 0),
                'dst_port': dst_port,
                'protocol': threat_data.get('protocol', 'unknown'),
            },
            
            # Flow Statistics (comprehensive)
            'flow_stats': {
                'total_packets': threat_data.get('flow_packets', 0),
                'total_bytes': threat_data.get('flow_bytes', 0),
                'fwd_packets': threat_data.get('fwd_packets', 0),
                'bwd_packets': threat_data.get('bwd_packets', 0),
                'fwd_bytes': threat_data.get('fwd_bytes', 0),
                'bwd_bytes': threat_data.get('bwd_bytes', 0),
                'flow_duration': threat_data.get('flow_duration', 0),
                'flow_rate': threat_data.get('flow_rate', 0),
                'packet_rate': threat_data.get('packet_rate', 0),
                'byte_rate': threat_data.get('byte_rate', 0),
            },
            
            # Packet Analysis
            'packet_analysis': {
                'min_packet_length': threat_data.get('min_packet_length', 0),
                'max_packet_length': threat_data.get('max_packet_length', 0),
                'mean_packet_length': threat_data.get('mean_packet_length', 0),
                'std_packet_length': threat_data.get('std_packet_length', 0),
                'packet_length_variance': threat_data.get('packet_length_variance', 0),
            },
            
            # Timing Analysis
            'timing': {
                'flow_iat_mean': threat_data.get('flow_iat_mean', 0),
                'flow_iat_std': threat_data.get('flow_iat_std', 0),
                'flow_iat_max': threat_data.get('flow_iat_max', 0),
                'flow_iat_min': threat_data.get('flow_iat_min', 0),
                'fwd_iat_mean': threat_data.get('fwd_iat_mean', 0),
                'bwd_iat_mean': threat_data.get('bwd_iat_mean', 0),
            },
            
            # Flag Analysis (TCP)
            'tcp_flags': {
                'fin_count': threat_data.get('fin_flag_count', 0),
                'syn_count': threat_data.get('syn_flag_count', 0),
                'rst_count': threat_data.get('rst_flag_count', 0),
                'psh_count': threat_data.get('psh_flag_count', 0),
                'ack_count': threat_data.get('ack_flag_count', 0),
                'urg_count': threat_data.get('urg_flag_count', 0),
            },
            
            # Threat Assessment
            'threat_assessment': {
                'probability': threat_data.get('probability', 0.0),
                'confidence': threat_data.get('confidence', 0.0),
                'attack_type': threat_data.get('attack_type', 'unclassified'),
                'severity': self._calculate_severity(threat_data),
                'risk_score': self._calculate_risk_score(threat_data),
            },
            
            # Behavioral Patterns
            'behavior': {
                'burst_rate': threat_data.get('burst_rate', 0),
                'idle_time': threat_data.get('idle_time', 0),
                'active_time': threat_data.get('active_time', 0),
                'connection_pattern': threat_data.get('connection_pattern', 'unknown'),
            },
            
            # All Flow Features (for manual review)
            'flow_features': threat_data.get('flow_features', {}),
            
            # Additional Context
            'context': {
                'interface': threat_data.get('interface', 'unknown'),
                'capture_window': threat_data.get('capture_window', 0),
                'additional_info': threat_data.get('additional_info', {}),
            },
            
            # Tracking
            'tracking': {
                'first_seen': timestamp,
                'last_seen': timestamp,
                'occurrence_count': 1,
                'verified': False,
                'false_positive': None,  # None=unreviewed, True=FP, False=confirmed
                'notes': '',
            }
        }
        
        # Save threat profile
        profile_file = self.threat_profiles_dir / f"threat_{threat_id}.json"
        with open(profile_file, 'w') as f:
            json.dump(threat_profile, f, indent=2, default=str)
        
        # Update blocked IPs
        if src_ip != 'unknown':
            if src_ip in self.blocked_ips:
                # Update existing entry
                self.blocked_ips[src_ip]['last_seen'] = timestamp
                self.blocked_ips[src_ip]['threat_count'] += 1
                self.blocked_ips[src_ip]['threat_ids'].append(threat_id)
            else:
                # Add new entry
                self.blocked_ips[src_ip] = {
                    'first_seen': timestamp,
                    'last_seen': timestamp,
                    'threat_count': 1,
                    'threat_ids': [threat_id],
                    'blocked': True,
                    'severity': threat_profile.get('threat_assessment', {}).get('severity', 'MEDIUM')
                }
            self._save_blocked_ips()
        
        # Update attack patterns
        pattern = {
            'threat_id': threat_id,
            'timestamp': timestamp,
            'dst_port': dst_port,
            'protocol': threat_data.get('protocol', 'unknown'),
            'packets': threat_data.get('flow_packets', 0),
            'bytes': threat_data.get('flow_bytes', 0),
            'probability': threat_data.get('probability', 0.0)
        }
        self.attack_patterns.append(pattern)
        
        # Keep only last 1000 patterns
        if len(self.attack_patterns) > 1000:
            self.attack_patterns = self.attack_patterns[-1000:]
        self._save_attack_patterns()
        
        return threat_id
    
    def _calculate_severity(self, threat_data):
        """Calculate threat severity level based on multiple factors"""
        probability = threat_data.get('probability', 0.0)
        packets = threat_data.get('flow_packets', 0)
        bytes_val = threat_data.get('flow_bytes', 0)
        
        # Calculate severity score (0-100)
        score = 0
        
        # Probability weight (0-40 points)
        score += probability * 40
        
        # Volume weight (0-30 points)
        if packets > 1000:
            score += 30
        elif packets > 100:
            score += 20
        elif packets > 10:
            score += 10
        
        # Bytes weight (0-30 points)
        if bytes_val > 1000000:  # >1MB
            score += 30
        elif bytes_val > 100000:  # >100KB
            score += 20
        elif bytes_val > 10000:  # >10KB
            score += 10
        
        # Convert to severity level
        if score >= 80:
            return 'CRITICAL'
        elif score >= 60:
            return 'HIGH'
        elif score >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_risk_score(self, threat_data):
        """Calculate comprehensive risk score (0-100)"""
        score = 0.0
        
        # Threat probability (40%)
        score += threat_data.get('probability', 0.0) * 40
        
        # Traffic volume (20%)
        packets = threat_data.get('flow_packets', 0)
        if packets > 0:
            volume_score = min(packets / 1000, 1.0) * 20
            score += volume_score
        
        # Connection pattern (20%)
        # High packet rate or burst patterns increase risk
        packet_rate = threat_data.get('packet_rate', 0)
        if packet_rate > 100:
            score += 20
        elif packet_rate > 50:
            score += 15
        elif packet_rate > 10:
            score += 10
        
        # Protocol and port (20%)
        dst_port = threat_data.get('dst_port', 0)
        # Common attack ports increase risk
        high_risk_ports = [22, 23, 3389, 445, 135, 139]
        if dst_port in high_risk_ports:
            score += 20
        elif dst_port < 1024:  # Privileged ports
            score += 10
        
        return min(score, 100.0)
    
    def is_blacklisted(self, ip_address):
        """Check if IP is blacklisted"""
        return ip_address in self.blocked_ips and self.blocked_ips[ip_address].get('blocked', False)
    
    def get_threat_profile(self, threat_id):
        """Get threat profile by ID"""
        profile_file = self.threat_profiles_dir / f"threat_{threat_id}.json"
        if profile_file.exists():
            with open(profile_file, 'r') as f:
                return json.load(f)
        return None
    
    def get_ip_threats(self, ip_address):
        """Get all threats from a specific IP"""
        if ip_address not in self.blocked_ips:
            return []
        
        threat_ids = self.blocked_ips[ip_address].get('threat_ids', [])
        threats = []
        for threat_id in threat_ids:
            profile = self.get_threat_profile(threat_id)
            if profile:
                threats.append(profile)
        return threats
    
    def get_statistics(self):
        """Get comprehensive blacklist statistics"""
        total_ips = len(self.blocked_ips)
        total_threats = sum(len(data['threat_ids']) for data in self.blocked_ips.values())
        
        # Count by severity
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        unverified_count = 0
        false_positive_count = 0
        confirmed_count = 0
        
        # Analyze all threat profiles
        for threat_file in self.threat_profiles_dir.glob('threat_*.json'):
            try:
                with open(threat_file, 'r') as f:
                    profile = json.load(f)
                    severity = profile.get('threat_assessment', {}).get('severity', 'LOW')
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                    
                    # Check verification status
                    tracking = profile.get('tracking', {})
                    if tracking.get('false_positive') is None:
                        unverified_count += 1
                    elif tracking.get('false_positive') is True:
                        false_positive_count += 1
                    else:
                        confirmed_count += 1
            except Exception:
                continue
        
        return {
            'total_blocked_ips': total_ips,
            'total_threats': total_threats,
            'total_patterns': len(self.attack_patterns),
            'severity_breakdown': severity_counts,
            'verification_status': {
                'unverified': unverified_count,
                'false_positives': false_positive_count,
                'confirmed_threats': confirmed_count
            }
        }
    
    def mark_as_false_positive(self, threat_id, notes=''):
        """Mark a threat as false positive for review"""
        profile = self.get_threat_profile(threat_id)
        if profile:
            profile['tracking']['false_positive'] = True
            profile['tracking']['verified'] = True
            profile['tracking']['notes'] = notes
            profile_file = self.threat_profiles_dir / f"threat_{threat_id}.json"
            with open(profile_file, 'w') as f:
                json.dump(profile, f, indent=2, default=str)
            return True
        return False
    
    def mark_as_confirmed_threat(self, threat_id, notes=''):
        """Mark a threat as confirmed after review"""
        profile = self.get_threat_profile(threat_id)
        if profile:
            profile['tracking']['false_positive'] = False
            profile['tracking']['verified'] = True
            profile['tracking']['notes'] = notes
            profile_file = self.threat_profiles_dir / f"threat_{threat_id}.json"
            with open(profile_file, 'w') as f:
                json.dump(profile, f, indent=2, default=str)
            return True
        return False
    
    def get_unverified_threats(self):
        """Get all threats that haven't been manually reviewed"""
        unverified = []
        for threat_file in self.threat_profiles_dir.glob('threat_*.json'):
            try:
                with open(threat_file, 'r') as f:
                    profile = json.load(f)
                    if profile.get('tracking', {}).get('false_positive') is None:
                        unverified.append(profile)
            except Exception:
                continue
        return unverified
    
    def unblock_ip(self, ip_address):
        """Remove IP from blacklist"""
        if ip_address in self.blocked_ips:
            self.blocked_ips[ip_address]['blocked'] = False
            self._save_blocked_ips()
            return True
        return False
    
    def export_blacklist(self, output_file):
        """Export blacklist to JSON file"""
        export_data = {
            'export_date': datetime.now().isoformat(),
            'blocked_ips': self.blocked_ips,
            'attack_patterns': self.attack_patterns,
            'statistics': self.get_statistics()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)


if __name__ == '__main__':
    # Test blacklist manager
    manager = BlacklistManager()
    
    print("Blacklist Manager Test")
    print("="*60)
    
    # Add test threat
    test_threat = {
        'src_ip': '10.0.0.100',
        'dst_ip': '192.168.112.143',
        'dst_port': 80,
        'protocol': 'TCP',
        'probability': 0.95,
        'flow_packets': 1500,
        'flow_bytes': 500000,
        'attack_type': 'DDoS',
        'additional_info': {'test': True}
    }
    
    threat_id = manager.add_threat(test_threat)
    print(f"✓ Added threat: {threat_id}")
    
    # Check if blacklisted
    is_blocked = manager.is_blacklisted('10.0.0.100')
    print(f"✓ IP 10.0.0.100 blacklisted: {is_blocked}")
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"\nBlacklist Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

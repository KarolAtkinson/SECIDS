#!/usr/bin/env python3
"""
Greylist Manager for SecIDS-CNN
================================
Manages the greylist - a middle ground between whitelist and blacklist
for potential threats that require user verification before action.

Greylist Criteria:
- Threat probability: 0.5 - 0.75 (50-75% confidence)
- Suspicious but not definitive
- Requires human judgment for final decision

Actions:
- Alert user of potential threat
- Request decision: Blacklist, Whitelist, or Keep on Greylist
- Track greylist history and decisions
"""

import json
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time


# Import list manager for whitelist/blacklist integration
try:
    from list_manager import ListManager
    LIST_MANAGER_AVAILABLE = True
except ImportError:
    LIST_MANAGER_AVAILABLE = False
    print("⚠️  List Manager not available - greylist will work standalone")


class GreylistManager:
    """
    Manages IP addresses in the greylist - potential threats requiring user verification
    """
    
    # Threat probability thresholds
    WHITELIST_THRESHOLD = 0.5      # Below this = benign (whitelist candidate)
    GREYLIST_LOW = 0.5             # Greylist range start
    GREYLIST_HIGH = 0.75           # Greylist range end
    BLACKLIST_THRESHOLD = 0.75     # Above this = definite threat (auto-blacklist)
    
    def __init__(self, greylist_dir: Path = None):
        """
        Initialize greylist manager
        
        Args:
            greylist_dir: Directory for greylist files
        """
        if greylist_dir is None:
            self.greylist_dir = Path(__file__).parent / 'greylist'
        else:
            self.greylist_dir = Path(greylist_dir)
        
        self.greylist_dir.mkdir(exist_ok=True)
        
        # Greylist file paths
        self.greylist_file = self.greylist_dir / 'greylist.json'
        self.history_file = self.greylist_dir / 'greylist_history.json'
        
        # In-memory greylist
        self.greylist: Dict[str, Dict] = {}
        self.history: List[Dict] = []
        
        # Initialize list manager for whitelist/blacklist integration
        if LIST_MANAGER_AVAILABLE:
            try:
                self.list_manager = ListManager()
                print("  ✓ List Manager integration enabled")
            except Exception as e:
                print(f"  ⚠️  Could not initialize List Manager: {e}")
                self.list_manager = None
        else:
            self.list_manager = None
        
        # User decision queue
        self.decision_queue = queue.Queue()
        self.pending_decisions: Dict[str, Dict] = {}
        
        # Statistics
        self.stats = {
            'total_greylist_alerts': 0,
            'moved_to_blacklist': 0,
            'moved_to_whitelist': 0,
            'kept_on_greylist': 0,
            'auto_expired': 0
        }
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Load existing greylist
        self.load_greylist()
        self.load_history()
        
        print(f"✓ Greylist Manager initialized")
        print(f"  Greylist directory: {self.greylist_dir}")
        print(f"  Current greylist size: {len(self.greylist)}")
    
    def load_greylist(self):
        """Load greylist from file"""
        if self.greylist_file.exists():
            try:
                with open(self.greylist_file, 'r') as f:
                    self.greylist = json.load(f)
                print(f"  ✓ Loaded {len(self.greylist)} entries from greylist")
            except Exception as e:
                print(f"  ⚠️  Could not load greylist: {e}")
                self.greylist = {}
        else:
            self.greylist = {}
    
    def load_history(self):
        """Load decision history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
                print(f"  ✓ Loaded {len(self.history)} historical decisions")
            except Exception as e:
                print(f"  ⚠️  Could not load history: {e}")
                self.history = []
        else:
            self.history = []
    
    def save_greylist(self):
        """Save greylist to file"""
        try:
            with open(self.greylist_file, 'w') as f:
                json.dump(self.greylist, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save greylist: {e}")
    
    def save_history(self):
        """Save decision history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save history: {e}")
    
    def classify_threat(self, probability: float) -> str:
        """
        Classify threat based on probability
        
        Args:
            probability: Threat probability (0.0 - 1.0)
        
        Returns:
            Classification: 'whitelist', 'greylist', or 'blacklist'
        """
        if probability < self.WHITELIST_THRESHOLD:
            return 'whitelist'
        elif self.GREYLIST_LOW <= probability <= self.GREYLIST_HIGH:
            return 'greylist'
        else:
            return 'blacklist'
    
    def is_greylisted(self, ip: str) -> bool:
        """Check if IP is on greylist"""
        with self.lock:
            return ip in self.greylist
    
    def add_to_greylist(self, ip: str, threat_data: Dict) -> bool:
        """
        Add IP to greylist
        
        Args:
            ip: IP address
            threat_data: Threat information (probability, port, etc.)
        
        Returns:
            True if added, False if already exists
        """
        with self.lock:
            if ip in self.greylist:
                # Update existing entry
                self.greylist[ip]['occurrences'] += 1
                self.greylist[ip]['last_seen'] = datetime.now().isoformat()
                self.greylist[ip]['threat_data'].append(threat_data)
                return False
            else:
                # Add new entry
                self.greylist[ip] = {
                    'ip': ip,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat(),
                    'occurrences': 1,
                    'threat_data': [threat_data],
                    'status': 'pending_decision'
                }
                self.save_greylist()
                self.stats['total_greylist_alerts'] += 1
                return True
    
    def remove_from_greylist(self, ip: str):
        """Remove IP from greylist"""
        with self.lock:
            if ip in self.greylist:
                del self.greylist[ip]
                self.save_greylist()
    
    def get_greylist_entry(self, ip: str) -> Optional[Dict]:
        """Get greylist entry for IP"""
        with self.lock:
            return self.greylist.get(ip)
    
    def get_all_greylisted_ips(self) -> List[str]:
        """Get all IPs on greylist"""
        with self.lock:
            return list(self.greylist.keys())
    
    def record_decision(self, ip: str, decision: str, reason: str = None):
        """
        Record a user decision about a greylisted IP
        
        Args:
            ip: IP address
            decision: 'blacklist', 'whitelist', or 'keep_greylist'
            reason: Optional reason for decision
        """
        entry = self.get_greylist_entry(ip)
        if not entry:
            return
        
        decision_record = {
            'timestamp': datetime.now().isoformat(),
            'ip': ip,
            'decision': decision,
            'reason': reason,
            'threat_data': entry['threat_data'][-1] if entry['threat_data'] else None,
            'occurrences': entry['occurrences']
        }
        
        with self.lock:
            self.history.append(decision_record)
            self.save_history()
            
            # Update statistics
            if decision == 'blacklist':
                self.stats['moved_to_blacklist'] += 1
            elif decision == 'whitelist':
                self.stats['moved_to_whitelist'] += 1
            elif decision == 'keep_greylist':
                self.stats['kept_on_greylist'] += 1
    
    def process_threat(self, threat_data: Dict) -> Tuple[str, bool]:
        """
        Process a detected threat and determine action
        
        Args:
            threat_data: Threat information with probability
        
        Returns:
            Tuple of (classification, requires_user_decision)
        """
        probability = threat_data.get('probability', 0.0)
        ip = threat_data.get('src_ip', 'unknown')
        
        classification = self.classify_threat(probability)
        
        if classification == 'greylist':
            # Add to greylist
            is_new = self.add_to_greylist(ip, threat_data)
            
            if is_new or ip not in self.pending_decisions:
                # Queue for user decision
                self.decision_queue.put({
                    'ip': ip,
                    'threat_data': threat_data,
                    'classification': classification,
                    'timestamp': datetime.now().isoformat()
                })
                self.pending_decisions[ip] = threat_data
            
            return classification, True  # Requires user decision
        
        return classification, False  # Auto-handle (whitelist or blacklist)
    
    def get_pending_decision(self, timeout: float = None) -> Optional[Dict]:
        """
        Get next pending decision from queue
        
        Args:
            timeout: Timeout in seconds (None = non-blocking)
        
        Returns:
            Decision data or None if queue empty
        """
        try:
            if timeout is None:
                return self.decision_queue.get_nowait()
            else:
                return self.decision_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def has_pending_decisions(self) -> bool:
        """Check if there are pending decisions"""
        return not self.decision_queue.empty()
    
    def get_pending_count(self) -> int:
        """Get number of pending decisions"""
        return self.decision_queue.qsize()
    
    def apply_decision(self, ip: str, decision: str, reason: str = None) -> Dict:
        """
        Apply user decision to greylisted IP
        
        Args:
            ip: IP address
            decision: 'blacklist', 'whitelist', or 'keep_greylist'
            reason: Optional reason
        
        Returns:
            Action dictionary with details
        """
        # Record the decision
        self.record_decision(ip, decision, reason)
        
        action = {
            'ip': ip,
            'decision': decision,
            'timestamp': datetime.now().isoformat(),
            'reason': reason
        }
        
        if decision == 'blacklist':
            # Move to blacklist
            self.remove_from_greylist(ip)
            
            # Use list manager if available
            if self.list_manager:
                threat_data = self.get_greylist_entry(ip) or {}
                self.list_manager.move_to_blacklist(
                    ip, 
                    reason or "User confirmed threat from greylist",
                    metadata={'greylist_data': threat_data}
                )
            
            action['action'] = 'block'
            action['message'] = f"IP {ip} moved to blacklist - countermeasures will be deployed"
        
        elif decision == 'whitelist':
            # Move to whitelist
            self.remove_from_greylist(ip)
            
            # Use list manager if available
            if self.list_manager:
                threat_data = self.get_greylist_entry(ip) or {}
                self.list_manager.move_to_whitelist(
                    ip, 
                    reason or "User verified as safe from greylist",
                    metadata={'greylist_data': threat_data}
                )
            
            action['action'] = 'allow'
            action['message'] = f"IP {ip} moved to whitelist - will be trusted"
        
        elif decision == 'keep_greylist':
            # Keep on greylist
            action['action'] = 'monitor'
            action['message'] = f"IP {ip} kept on greylist - continue monitoring"
        
        # Remove from pending
        if ip in self.pending_decisions:
            del self.pending_decisions[ip]
        
        return action
    
    def cleanup_expired(self, max_age_hours: int = 24):
        """
        Clean up old greylist entries
        
        Args:
            max_age_hours: Maximum age in hours before auto-expiry
        """
        current_time = datetime.now()
        expired = []
        
        with self.lock:
            for ip, entry in list(self.greylist.items()):
                last_seen = datetime.fromisoformat(entry['last_seen'])
                age_hours = (current_time - last_seen).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    expired.append(ip)
                    del self.greylist[ip]
            
            if expired:
                self.save_greylist()
                self.stats['auto_expired'] += len(expired)
                print(f"✓ Cleaned up {len(expired)} expired greylist entries")
        
        return expired
    
    def get_statistics(self) -> Dict:
        """Get greylist statistics"""
        with self.lock:
            return {
                **self.stats,
                'current_greylist_size': len(self.greylist),
                'pending_decisions': self.get_pending_count(),
                'total_history': len(self.history)
            }
    
    def print_statistics(self):
        """Print greylist statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print("  GREYLIST STATISTICS")
        print("="*80)
        print(f"  Current greylist size: {stats['current_greylist_size']}")
        print(f"  Pending decisions: {stats['pending_decisions']}")
        print(f"  Total alerts: {stats['total_greylist_alerts']}")
        print(f"  Moved to blacklist: {stats['moved_to_blacklist']}")
        print(f"  Moved to whitelist: {stats['moved_to_whitelist']}")
        print(f"  Kept on greylist: {stats['kept_on_greylist']}")
        print(f"  Auto-expired: {stats['auto_expired']}")
        print(f"  Total decisions: {stats['total_history']}")
        print("="*80 + "\n")
    
    def export_report(self, output_file: Path = None) -> Path:
        """
        Export greylist report
        
        Args:
            output_file: Output file path
        
        Returns:
            Path to report file
        """
        if output_file is None:
            output_file = self.greylist_dir / f'greylist_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'current_greylist': self.greylist,
            'recent_history': self.history[-50:] if len(self.history) > 50 else self.history
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Greylist report exported to: {output_file}")
        return output_file


def prompt_user_decision(greylist_mgr: GreylistManager, pending_item: Dict) -> Dict:
    """
    Prompt user for decision on greylisted item
    
    Args:
        greylist_mgr: GreylistManager instance
        pending_item: Pending decision item
    
    Returns:
        Action dictionary
    """
    ip = pending_item['ip']
    threat_data = pending_item['threat_data']
    
    print("\n" + "⚠️ "*40)
    print("  GREYLIST ALERT - USER DECISION REQUIRED")
    print("⚠️ "*40)
    print(f"\n  Potential threat detected from: {ip}")
    print(f"  Threat probability: {threat_data['probability']*100:.1f}%")
    print(f"  Destination port: {threat_data.get('dst_port', 'unknown')}")
    print(f"  Flow packets: {threat_data.get('flow_packets', 'unknown')}")
    print(f"  Flow bytes: {threat_data.get('flow_bytes', 'unknown')}")
    
    # Check greylist history
    entry = greylist_mgr.get_greylist_entry(ip)
    if entry and entry['occurrences'] > 1:
        print(f"\n  ⚠️  This IP has been seen {entry['occurrences']} times")
        print(f"  First seen: {entry['first_seen']}")
        print(f"  Last seen: {entry['last_seen']}")
    
    print("\n  This threat is in the GREYLIST range (50-75% confidence)")
    print("  Automatic countermeasures are NOT deployed for greylisted threats.")
    
    print("\n  What action should be taken?")
    print("    [1] Move to BLACKLIST and deploy countermeasures (block IP)")
    print("    [2] Move to WHITELIST (trust this IP)")
    print("    [3] Keep on GREYLIST (continue monitoring)")
    print("    [4] Skip this decision (will be asked again)")
    
    while True:
        try:
            choice = input("\n  Enter choice [1-4]: ").strip()
            
            if choice == '1':
                reason = input("  Reason for blacklisting (optional): ").strip() or "User confirmed threat"
                return greylist_mgr.apply_decision(ip, 'blacklist', reason)
            
            elif choice == '2':
                reason = input("  Reason for whitelisting (optional): ").strip() or "User verified as safe"
                return greylist_mgr.apply_decision(ip, 'whitelist', reason)
            
            elif choice == '3':
                reason = input("  Reason for monitoring (optional): ").strip() or "Requires more observation"
                return greylist_mgr.apply_decision(ip, 'keep_greylist', reason)
            
            elif choice == '4':
                print("  Decision skipped - will be asked again later")
                return {
                    'ip': ip,
                    'decision': 'skipped',
                    'action': 'none',
                    'message': 'User skipped decision'
                }
            
            else:
                print("  ⚠️  Invalid choice. Please enter 1, 2, 3, or 4.")
        
        except KeyboardInterrupt:
            print("\n  Decision cancelled")
            return {
                'ip': ip,
                'decision': 'cancelled',
                'action': 'none',
                'message': 'User cancelled decision'
            }
        except Exception as e:
            print(f"  ⚠️  Error: {e}")


# Example usage
if __name__ == '__main__':
    print("="*80)
    print("  Greylist Manager - Test Mode")
    print("="*80)
    
    # Initialize manager
    mgr = GreylistManager()
    
    # Simulate some threats
    test_threats = [
        {'src_ip': '192.168.1.100', 'probability': 0.45, 'dst_port': 80},   # Whitelist
        {'src_ip': '10.0.0.50', 'probability': 0.62, 'dst_port': 443},      # Greylist
        {'src_ip': '172.16.0.30', 'probability': 0.88, 'dst_port': 22},     # Blacklist
        {'src_ip': '192.168.1.200', 'probability': 0.58, 'dst_port': 8080}, # Greylist
    ]
    
    print("\nProcessing test threats...")
    for threat in test_threats:
        classification, needs_decision = mgr.process_threat(threat)
        print(f"  IP {threat['src_ip']}: {classification} (probability: {threat['probability']*100:.1f}%)")
        if needs_decision:
            print(f"    → Requires user decision")
    
    # Show statistics
    mgr.print_statistics()
    
    # Process pending decisions
    if mgr.has_pending_decisions():
        print(f"\n{mgr.get_pending_count()} pending decision(s)...")
        
        while mgr.has_pending_decisions():
            pending = mgr.get_pending_decision()
            if pending:
                action = prompt_user_decision(mgr, pending)
                print(f"\n  ✓ {action['message']}")
    
    # Final statistics
    mgr.print_statistics()
    
    # Export report
    mgr.export_report()

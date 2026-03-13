#!/usr/bin/env python3
"""
Threat Review Tool - Review and verify detected threats
Helps identify false positives vs. actual threats
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / 'Device_Profile' / 'device_info'))
from blacklist_manager import BlacklistManager


class ThreatReviewer:
    """Review and analyze detected threats"""
    
    def __init__(self):
        self.blacklist_mgr = BlacklistManager()
        
    def list_unverified_threats(self):
        """List all unverified threats requiring review"""
        unverified = self.blacklist_mgr.get_unverified_threats()
        
        print("\n" + "="*80)
        print(f"UNVERIFIED THREATS REQUIRING REVIEW: {len(unverified)}")
        print("="*80 + "\n")
        
        if not unverified:
            print("✅ No unverified threats. All detections have been reviewed.")
            return
        
        for i, threat in enumerate(unverified, 1):
            self._print_threat_summary(threat, i)
    
    def _print_threat_summary(self, threat, num=None):
        """Print a threat summary"""
        prefix = f"{num}. " if num else ""
        
        print(f"{prefix}Threat ID: {threat.get('threat_id', 'Unknown')}")
        print(f"   Time: {threat.get('detection_time', threat.get('timestamp', 'Unknown'))}")
        
        network = threat.get('network', {})
        print(f"   Source: {network.get('src_ip', 'Unknown')}:{network.get('src_port', 'N/A')}")
        print(f"   Destination: {network.get('dst_ip', 'Unknown')}:{network.get('dst_port', 'N/A')}")
        print(f"   Protocol: {network.get('protocol', 'Unknown')}")
        
        assessment = threat.get('threat_assessment', {})
        prob = assessment.get('probability', 0)
        if prob > 1:  # If stored as percentage
            prob = prob / 100
        print(f"   Probability: {prob*100:.1f}%")
        print(f"   Severity: {assessment.get('severity', 'Unknown')}")
        print(f"   Risk Score: {assessment.get('risk_score', 0):.1f}/100")
        
        flow_stats = threat.get('flow_stats', {})
        print(f"   Traffic: {flow_stats.get('total_packets', 0)} packets, "
              f"{flow_stats.get('total_bytes', 0)} bytes")
        print()
    
    def show_threat_details(self, threat_id):
        """Show complete threat details"""
        threat = self.blacklist_mgr.get_threat_profile(threat_id)
        
        if not threat:
            print(f"❌ Threat {threat_id} not found")
            return
        
        print("\n" + "="*80)
        print(f"DETAILED THREAT ANALYSIS: {threat_id}")
        print("="*80 + "\n")
        
        # Basic Info
        print("📋 BASIC INFORMATION")
        print("-" * 80)
        print(f"Threat ID: {threat['threat_id']}")
        print(f"Detection Time: {threat['detection_time']}")
        print(f"Timestamp: {threat['timestamp']}")
        
        # Network Layer
        print("\n🌐 NETWORK LAYER")
        print("-" * 80)
        network = threat.get('network', {})
        for key, value in network.items():
            print(f"{key:20s}: {value}")
        
        # Flow Statistics
        print("\n📊 FLOW STATISTICS")
        print("-" * 80)
        flow_stats = threat.get('flow_stats', {})
        for key, value in flow_stats.items():
            print(f"{key:20s}: {value}")
        
        # Packet Analysis
        print("\n📦 PACKET ANALYSIS")
        print("-" * 80)
        packet_analysis = threat.get('packet_analysis', {})
        for key, value in packet_analysis.items():
            print(f"{key:25s}: {value}")
        
        # Timing Analysis
        print("\n⏱️  TIMING ANALYSIS")
        print("-" * 80)
        timing = threat.get('timing', {})
        for key, value in timing.items():
            print(f"{key:20s}: {value}")
        
        # TCP Flags
        print("\n🚩 TCP FLAGS")
        print("-" * 80)
        tcp_flags = threat.get('tcp_flags', {})
        for key, value in tcp_flags.items():
            print(f"{key:20s}: {value}")
        
        # Threat Assessment
        print("\n⚠️  THREAT ASSESSMENT")
        print("-" * 80)
        assessment = threat.get('threat_assessment', {})
        for key, value in assessment.items():
            print(f"{key:20s}: {value}")
        
        # Behavioral Patterns
        print("\n🔍 BEHAVIORAL PATTERNS")
        print("-" * 80)
        behavior = threat.get('behavior', {})
        for key, value in behavior.items():
            print(f"{key:20s}: {value}")
        
        # Context
        print("\n📍 CONTEXT")
        print("-" * 80)
        context = threat.get('context', {})
        for key, value in context.items():
            if key != 'additional_info':
                print(f"{key:20s}: {value}")
        
        # Tracking
        print("\n🔖 TRACKING")
        print("-" * 80)
        tracking = threat.get('tracking', {})
        for key, value in tracking.items():
            print(f"{key:20s}: {value}")
        
        print("\n" + "="*80)
    
    def analyze_patterns(self):
        """Analyze patterns across all threats"""
        stats = self.blacklist_mgr.get_statistics()
        
        print("\n" + "="*80)
        print("THREAT PATTERN ANALYSIS")
        print("="*80 + "\n")
        
        print("📊 OVERALL STATISTICS")
        print("-" * 80)
        print(f"Total Blocked IPs: {stats['total_blocked_ips']}")
        print(f"Total Threats: {stats['total_threats']}")
        print(f"Attack Patterns: {stats['total_patterns']}")
        
        print("\n⚠️  SEVERITY BREAKDOWN")
        print("-" * 80)
        for severity, count in stats['severity_breakdown'].items():
            bar = '█' * min(count, 50)
            print(f"{severity:10s}: {bar} ({count})")
        
        print("\n✅ VERIFICATION STATUS")
        print("-" * 80)
        ver_status = stats['verification_status']
        print(f"Unverified:        {ver_status['unverified']}")
        print(f"False Positives:   {ver_status['false_positives']}")
        print(f"Confirmed Threats: {ver_status['confirmed_threats']}")
        
        # Port analysis
        print("\n🔌 TOP TARGETED PORTS")
        print("-" * 80)
        port_counts = defaultdict(int)
        
        threat_profiles_dir = Path(__file__).parent.parent / 'Device_Profile' / 'Blacklist' / 'threat_profiles'
        for threat_file in threat_profiles_dir.glob('threat_*.json'):
            try:
                with open(threat_file, 'r') as f:
                    profile = json.load(f)
                    port = profile.get('network', {}).get('dst_port', 0)
                    if port > 0:
                        port_counts[port] += 1
            except (json.JSONDecodeError, OSError):
                # Cannot read threat file
                continue
        # Sort by count
        top_ports = sorted(port_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for port, count in top_ports:
            print(f"Port {port:5d}: {count} threats")
        
        print("\n" + "="*80)
    
    def mark_threat(self, threat_id, is_false_positive, notes=''):
        """Mark a threat as FP or confirmed"""
        if is_false_positive:
            success = self.blacklist_mgr.mark_as_false_positive(threat_id, notes)
            if success:
                print(f"✅ Threat {threat_id} marked as FALSE POSITIVE")
            else:
                print(f"❌ Failed to mark threat {threat_id}")
        else:
            success = self.blacklist_mgr.mark_as_confirmed_threat(threat_id, notes)
            if success:
                print(f"✅ Threat {threat_id} marked as CONFIRMED THREAT")
            else:
                print(f"❌ Failed to mark threat {threat_id}")
    
    def interactive_review(self):
        """Interactive threat review session"""
        unverified = self.blacklist_mgr.get_unverified_threats()
        
        if not unverified:
            print("\n✅ No unverified threats to review!")
            return
        
        print("\n" + "="*80)
        print(f"INTERACTIVE THREAT REVIEW - {len(unverified)} threats")
        print("="*80)
        
        for i, threat in enumerate(unverified, 1):
            self.show_threat_details(threat['threat_id'])
            
            print(f"\nReview {i}/{len(unverified)}")
            print("Options:")
            print("  [f] Mark as False Positive")
            print("  [c] Mark as Confirmed Threat")
            print("  [s] Skip (review later)")
            print("  [q] Quit review")
            
            choice = input("\nYour choice: ").strip().lower()
            
            if choice == 'f':
                notes = input("Notes (optional): ").strip()
                self.mark_threat(threat['threat_id'], True, notes)
            elif choice == 'c':
                notes = input("Notes (optional): ").strip()
                self.mark_threat(threat['threat_id'], False, notes)
            elif choice == 'q':
                print("\nExiting review session...")
                break
            elif choice == 's':
                print("\nSkipping...")
            else:
                print("\nInvalid choice, skipping...")
            
            print()


def main():
    """Main entry point"""
    reviewer = ThreatReviewer()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python threat_reviewer.py list           - List unverified threats")
        print("  python threat_reviewer.py show <id>      - Show threat details")
        print("  python threat_reviewer.py patterns       - Analyze patterns")
        print("  python threat_reviewer.py review         - Interactive review")
        print("  python threat_reviewer.py mark <id> <fp|confirmed> [notes]")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        reviewer.list_unverified_threats()
    
    elif command == 'show' and len(sys.argv) >= 3:
        reviewer.show_threat_details(sys.argv[2])
    
    elif command == 'patterns':
        reviewer.analyze_patterns()
    
    elif command == 'review':
        reviewer.interactive_review()
    
    elif command == 'mark' and len(sys.argv) >= 4:
        threat_id = sys.argv[2]
        is_fp = sys.argv[3].lower() in ['fp', 'false', 'falsepositive']
        notes = ' '.join(sys.argv[4:]) if len(sys.argv) > 4 else ''
        reviewer.mark_threat(threat_id, is_fp, notes)
    
    else:
        print("Invalid command or missing arguments")


if __name__ == '__main__':
    main()

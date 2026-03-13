#!/usr/bin/env python3
"""
DDoS Countermeasure - Active Mode
===================================
Manual control with full feature access and detailed workflow.
Provides complete visibility and control over all countermeasure operations.

Features:
- Manual intervention options
- Detailed logging to console
- Configurable thresholds
- Step-by-step workflow
- Full statistics
- Interactive controls
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Import core functionality
sys.path.insert(0, str(Path(__file__).parent))
from countermeasure_core import CountermeasureCore


class ActiveCountermeasure(CountermeasureCore):
    """
    Active Mode: Full manual control with detailed workflow
    
    Operation:
    - Manual start (not automatic)
    - User-configurable thresholds
    - Detailed console logging
    - Interactive prompts
    - Full control over all operations
    """
    
    def __init__(self,
                 block_threshold: int = 5,
                 time_window: int = 60,
                 auto_block: bool = True,
                 interactive: bool = True,
                 log_file: Optional[str] = None):
        """
        Initialize Active Mode countermeasure
        
        Args:
            block_threshold: Threats before blocking (default: 5)
            time_window: Time window in seconds (default: 60)
            auto_block: Auto-block threats (default: True, can be disabled)
            interactive: Enable interactive prompts (default: True)
            log_file: Path to log file (optional)
        """
        # Initialize with active mode settings
        log_path = Path(log_file) if log_file else None
        
        super().__init__(
            mode="active",
            block_threshold=block_threshold,
            time_window=time_window,
            auto_block=auto_block,
            log_file=log_path
        )
        
        self.interactive = interactive
        
        # Manual events log
        self.manual_actions: List[Dict] = []
        
        # Do NOT auto-start (manual control)
        print()
        print("=" * 80)
        print("Active Mode Initialized - Manual Control Enabled")
        print("=" * 80)
        print(f"Mode: ACTIVE")
        print(f"Auto-block: {'ENABLED' if auto_block else 'DISABLED'}")
        print(f"Interactive: {'YES' if interactive else 'NO'}")
        print(f"Threshold: {block_threshold} threats in {time_window}s window")
        print(f"Log file: {log_file}")
        print()
        print("Use start() to begin countermeasure processing")
        print("=" * 80)
        print()
    
    def _log(self, message: str, level: str = "INFO"):
        """Active logging (both console and file)"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Always print to console in active mode
        print(log_entry)
        
        # Also write to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except (OSError, IOError) as exc:
            print(f"[{timestamp}] [WARNING] Log file write failed: {exc}")
    
    def manual_block_ip(self, ip: str, reason: str = "Manual block"):
        """Manually block an IP address"""
        self._block_ip(ip, reason)
        self.manual_actions.append({
            'type': 'manual_block_ip',
            'ip': ip,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        self._log(f"Manual IP block: {ip} - {reason}", "MANUAL")
    
    def manual_unblock_ip(self, ip: str):
        """Manually unblock an IP address"""
        self.unblock_ip(ip)
        self.manual_actions.append({
            'type': 'manual_unblock_ip',
            'ip': ip,
            'timestamp': datetime.now().isoformat()
        })
        self._log(f"Manual IP unblock: {ip}", "MANUAL")
    
    def manual_block_port(self, port: int, reason: str = "Manual block"):
        """Manually block a port"""
        self._block_port(port, reason)
        self.manual_actions.append({
            'type': 'manual_block_port',
            'port': port,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        self._log(f"Manual port block: {port} - {reason}", "MANUAL")
    
    def manual_unblock_port(self, port: int):
        """Manually unblock a port"""
        self.unblock_port(port)
        self.manual_actions.append({
            'type': 'manual_unblock_port',
            'port': port,
            'timestamp': datetime.now().isoformat()
        })
        self._log(f"Manual port unblock: {port}", "MANUAL")
    
    def get_detailed_stats(self) -> Dict:
        """Get comprehensive statistics for active mode"""
        stats = self.get_statistics()
        status = self.get_status()
        
        return {
            # Core stats
            **stats,
            **status,
            
            # Manual actions
            'manual_actions_count': len(self.manual_actions),
            'manual_actions': self.manual_actions,
            
            # Currently blocked items
            'blocked_ips_list': list(self.blocked_ips),
            'blocked_ports_list': list(self.blocked_ports),
            
            # Threat history summary
            'unique_threat_sources': len(self.threat_history),
            'active_threats': sum(1 for ip in self.threat_history if len(self.threat_history[ip]) > 0)
        }
    
    def print_detailed_status(self):
        """Print detailed system status"""
        stats = self.get_detailed_stats()
        
        print()
        print("=" * 80)
        print("ACTIVE MODE - DETAILED STATUS")
        print("=" * 80)
        
        # System status
        print("\nSYSTEM STATUS:")
        print(f"  Mode: {stats['mode'].upper()}")
        print(f"  Running: {'YES' if stats['running'] else 'NO'}")
        print(f"  Runtime: {stats['runtime_seconds']:.1f} seconds")
        print(f"  Health: {self._get_health_indicator(stats)}")
        
        # Threat detection
        print("\nTHREAT DETECTION:")
        print(f"  Total threats detected: {stats['threats_detected']}")
        print(f"  Whitelisted (skipped): {stats['threats_whitelisted']}")
        print(f"  Greylisted (pending): {stats['threats_greylisted']}")
        print(f"  Unique threat sources: {stats['unique_threat_sources']}")
        print(f"  Threat rate: {stats['threats_per_minute']:.1f} threats/minute")
        
        # Countermeasures
        print("\nCOUNTERMEASURES:")
        print(f"  IPs blocked: {stats['ips_blocked']} ({stats['currently_blocked_ips']} active)")
        print(f"  Ports blocked: {stats['ports_blocked']} ({stats['currently_blocked_ports']} active)")
        print(f"  Total actions taken: {stats['actions_taken']}")
        print(f"  Manual interventions: {stats['manual_actions_count']}")
        print(f"  Errors encountered: {stats['errors']}")
        
        # Lists
        print("\nIP FILTERING LISTS:")
        print(f"  Whitelist: {stats['whitelist_size']} entries")
        print(f"  Blacklist: {stats['blacklist_size']} entries")
        print(f"  Greylist: {stats['greylist_size']} entries")
        
        # Configuration
        print("\nCONFIGURATION:")
        print(f"  Block threshold: {stats['block_threshold']} threats")
        print(f"  Time window: {stats['time_window']} seconds")
        print(f"  Auto-block: {'ENABLED' if stats['auto_block'] else 'DISABLED'}")
        print(f"  Interactive mode: {'YES' if self.interactive else 'NO'}")
        
        # Currently blocked
        if stats['currently_blocked_ips'] > 0:
            print("\nCURRENTLY BLOCKED IPs:")
            for ip in stats['blocked_ips_list']:
                print(f"  - {ip}")
        
        if stats['currently_blocked_ports'] > 0:
            print("\nCURRENTLY BLOCKED PORTS:")
            for port in stats['blocked_ports_list']:
                print(f"  - {port}")
        
        print("=" * 80)
        print()
    
    def _get_health_indicator(self, stats: Dict) -> str:
        """Get health status with indicator"""
        if stats['errors'] > 10:
            return "⚠️  ERROR"
        elif stats['errors'] > 3:
            return "⚠️  WARNING"
        elif stats['threats_per_minute'] > 100:
            return "⚠️  HIGH LOAD"
        else:
            return "✓ HEALTHY"
    
    def export_report(self, output_file: Optional[str] = None) -> str:
        """
        Export detailed report
        
        Args:
            output_file: Path to output file (auto-generated if None)
        
        Returns:
            Path to generated report
        """
        from datetime import datetime
        import json
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"Countermeasures/logs/countermeasure_report_{timestamp}.json"
        
        stats = self.get_detailed_stats()
        
        # Convert sets to lists for JSON serialization
        report = {
            **stats,
            'blocked_ips_list': list(self.blocked_ips),
            'blocked_ports_list': list(self.blocked_ports),
            'generated_at': datetime.now().isoformat()
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self._log(f"Report exported to: {output_path}")
        return str(output_path)


# Workflow helper functions
def show_workflow_manual():
    """Display the Active Mode workflow manual"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ACTIVE MODE - WORKFLOW MANUAL                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

STEP-BY-STEP WORKFLOW:

1. INITIALIZATION
   ---------------
   • Create ActiveCountermeasure instance
   • Configure thresholds and settings
   • Review initial configuration
   
   Example:
   >>> from countermeasure_active import ActiveCountermeasure
   >>> cm = ActiveCountermeasure(block_threshold=5, time_window=60)

2. START MONITORING
   ----------------
   • Start the countermeasure worker thread
   • Begin processing threats
   
   Example:
   >>> cm.start()

3. THREAT PROCESSING
   ------------------
   • Threats are detected by the main system
   • Passed to countermeasure via process_threat()
   • Automatically evaluated against thresholds
   • Actions taken based on configuration
   
   Automatic Actions:
   • Whitelist check → Skip if whitelisted
   • Greylist check → Skip if greylisted
   • Threat counting → Track recent threats
   • Threshold check → Block if exceeded
   
4. MANUAL INTERVENTION
   --------------------
   • Block specific IP manually
   • Unblock specific IP
   • Block specific port
   • Unblock specific port
   • Clear all blocks
   
   Examples:
   >>> cm.manual_block_ip('192.168.1.100', 'Confirmed threat')
   >>> cm.manual_unblock_ip('192.168.1.100')
   >>> cm.manual_block_port(22, 'SSH brute force')
   >>> cm.clear_all_blocks()

5. MONITORING & STATUS
   --------------------
   • View detailed statistics
   • Check system health
   • Review blocked items
   • Monitor threat rates
   
   Examples:
   >>> cm.print_detailed_status()
   >>> stats = cm.get_detailed_stats()

6. REPORTING
   ----------
   • Export detailed reports
   • Review manual interventions
   • Analyze threat patterns
   
   Example:
   >>> cm.export_report()

7. PAUSE/RESUME
   -------------
   • Temporarily pause auto-blocking
   • Resume normal operation
   
   Examples:
   >>> cm.auto_block = False  # Pause
   >>> cm.auto_block = True   # Resume

8. SHUTDOWN
   ---------
   • Stop monitoring
   • Optionally clear all blocks
   • Export final report
   
   Example:
   >>> cm.stop()
   >>> cm.clear_all_blocks()  # Optional
   >>> cm.export_report()

═══════════════════════════════════════════════════════════════════════════════

BEST PRACTICES:

✓ Monitor threat rates regularly
✓ Review whitelisted/greylisted items
✓ Manually verify high-severity blocks
✓ Export reports after significant events
✓ Clear blocks after testing
✓ Keep block thresholds appropriate for your environment

═══════════════════════════════════════════════════════════════════════════════
""")


if __name__ == '__main__':
    show_workflow_manual()
    
    print("\n" + "=" * 80)
    print("Starting Active Mode...")
    print("=" * 80)
    
    # Initialize active mode
    cm = ActiveCountermeasure(
        block_threshold=5,
        time_window=60,
        auto_block=True,
        interactive=True
    )
    
    # Start monitoring
    cm.start()
    
    print("\nActive mode is running.")
    print("Press Ctrl+C to stop and view final statistics.")
    print()
    
    try:
        import time
        while True:
            time.sleep(30)
            cm.print_detailed_status()
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        cm.stop()
        cm.print_detailed_status()
        
        # Ask about clearing blocks
        response = input("\nClear all iptables blocks? (y/n): ")
        if response.lower() == 'y':
            cm.clear_all_blocks()
            print("✓ All blocks cleared")
        
        # Export final report
        report_path = cm.export_report()
        print(f"\n✓ Final report exported to: {report_path}")
        print("\nDone.")

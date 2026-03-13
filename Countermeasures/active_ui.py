#!/usr/bin/env python3
"""
Active Mode - Full Featured UI
================================
Complete interface with workflow manual and full control.
Provides step-by-step guidance for manual intervention.

Features:
- Interactive workflow guidance
- Manual block/unblock controls
- Detailed statistics
- Report generation
- Threshold configuration
- List management interface
"""

import sys
from pathlib import Path
from datetime import datetime

# Import active mode countermeasure
sys.path.insert(0, str(Path(__file__).parent))
from countermeasure_active import ActiveCountermeasure, show_workflow_manual


class ActiveUI:
    """Full-featured UI for Active Mode"""
    
    def __init__(self):
        self.cm = None
    
    def show_main_menu(self):
        """Display main menu"""
        print("\n" + "=" * 80)
        print("ACTIVE MODE - COUNTERMEASURE SYSTEM")
        print("=" * 80)
        print()
        print("SYSTEM CONTROLS:")
        print("  1. Initialize System      - Configure and start countermeasures")
        print("  2. View Status            - Show detailed system status")
        print("  3. Start Monitoring       - Begin threat detection")
        print("  4. Stop Monitoring        - Stop threat detection")
        print()
        print("MANUAL INTERVENTION:")
        print("  5. Block IP Address       - Manually block specific IP")
        print("  6. Unblock IP Address     - Remove IP block")
        print("  7. Block Port             - Manually block specific port")
        print("  8. Unblock Port           - Remove port block")
        print("  9. Clear All Blocks       - Remove all active blocks")
        print()
        print("REPORTING & ANALYSIS:")
        print("  10. Export Report         - Generate detailed report")
        print("  11. View Blocked Items    - List currently blocked IPs/ports")
        print("  12. Configure Thresholds  - Adjust detection settings")
        print()
        print("HELP & DOCUMENTATION:")
        print("  13. Show Workflow Manual  - Display step-by-step guide")
        print("  14. Toggle Auto-Block     - Enable/disable automatic blocking")
        print()
        print("  0. Exit")
        print("=" * 80)
    
    def initialize_system(self):
        """Initialize countermeasure system"""
        print("\n" + "=" * 80)
        print("SYSTEM INITIALIZATION")
        print("=" * 80)
        print()
        
        # Get configuration from user
        print("Configure countermeasure thresholds:")
        print()
        
        try:
            threshold = input("Block threshold (threats before blocking) [5]: ").strip()
            threshold = int(threshold) if threshold else 5
            
            window = input("Time window in seconds [60]: ").strip()
            window = int(window) if window else 60
            
            auto = input("Enable auto-blocking? (y/n) [y]: ").strip().lower()
            auto_block = auto != 'n'
            
            print()
            print("Initializing with:")
            print(f"  • Block threshold: {threshold}")
            print(f"  • Time window: {window}s")
            print(f"  • Auto-block: {'ENABLED' if auto_block else 'DISABLED'}")
            print()
            
            self.cm = ActiveCountermeasure(
                block_threshold=threshold,
                time_window=window,
                auto_block=auto_block,
                interactive=True
            )
            
            # Check sudo availability
            if auto_block and not self.cm.sudo_available:
                print("\n" + "="*80)
                print("⚠️  WARNING: Sudo privileges not available!")
                print("="*80)
                print("Countermeasures will detect threats but CANNOT block IPs/ports.")
                print("\nTo enable blocking, either:")
                print("  1. Run with sudo: sudo python3 Countermeasures/active_ui.py")
                print("  2. Configure passwordless sudo:")
                print("     sudo bash Countermeasures/setup_passwordless_sudo.sh")
                print("="*80)
                print("\nAuto-blocking will be disabled. You can still monitor threats.")
                print("Consider toggling auto-block OFF (option 14) to suppress warnings.")
                print()
            
            print("\n✓ System initialized successfully")
        
        except ValueError:
            print("\n❌ Invalid input. Using defaults.")
            self.cm = ActiveCountermeasure()
    
    def start_monitoring(self):
        """Start threat monitoring"""
        if self.cm is None:
            print("\n❌ System not initialized. Please initialize first (option 1)")
            return
        
        if self.cm.running:
            print("\n⚠️  Monitoring already active")
            return
        
        self.cm.start()
        print("\n✓ Monitoring started")
        print("Threats will be automatically processed based on configuration")
    
    def stop_monitoring(self):
        """Stop threat monitoring"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        if not self.cm.running:
            print("\n⚠️  Monitoring not active")
            return
        
        self.cm.stop()
        print("\n✓ Monitoring stopped")
    
    def view_status(self):
        """Display detailed status"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        self.cm.print_detailed_status()
    
    def manual_block_ip(self):
        """Manually block an IP"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        print("\n" + "=" * 80)
        print("MANUAL IP BLOCK")
        print("=" * 80)
        
        ip = input("Enter IP address to block: ").strip()
        if not ip:
            print("❌ No IP provided")
            return
        
        reason = input("Reason for blocking [Manual intervention]: ").strip()
        if not reason:
            reason = "Manual intervention"
        
        confirm = input(f"\nBlock {ip}? (y/n): ").strip().lower()
        if confirm == 'y':
            self.cm.manual_block_ip(ip, reason)
            print(f"\n✓ IP {ip} blocked")
        else:
            print("\n❌ Cancelled")
    
    def manual_unblock_ip(self):
        """Manually unblock an IP"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        print("\n" + "=" * 80)
        print("MANUAL IP UNBLOCK")
        print("=" * 80)
        
        # Show currently blocked IPs
        if self.cm.blocked_ips:
            print("\nCurrently blocked IPs:")
            for ip in self.cm.blocked_ips:
                print(f"  • {ip}")
            print()
        else:
            print("\nNo IPs currently blocked")
            return
        
        ip = input("Enter IP address to unblock: ").strip()
        if not ip:
            print("❌ No IP provided")
            return
        
        if ip not in self.cm.blocked_ips:
            print(f"\n⚠️  IP {ip} is not currently blocked")
            return
        
        confirm = input(f"\nUnblock {ip}? (y/n): ").strip().lower()
        if confirm == 'y':
            self.cm.manual_unblock_ip(ip)
            print(f"\n✓ IP {ip} unblocked")
        else:
            print("\n❌ Cancelled")
    
    def manual_block_port(self):
        """Manually block a port"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        print("\n" + "=" * 80)
        print("MANUAL PORT BLOCK")
        print("=" * 80)
        
        try:
            port = input("Enter port number to block: ").strip()
            port = int(port)
            
            reason = input("Reason for blocking [Manual intervention]: ").strip()
            if not reason:
                reason = "Manual intervention"
            
            confirm = input(f"\nBlock port {port}? (y/n): ").strip().lower()
            if confirm == 'y':
                self.cm.manual_block_port(port, reason)
                print(f"\n✓ Port {port} blocked")
            else:
                print("\n❌ Cancelled")
        
        except ValueError:
            print("\n❌ Invalid port number")
    
    def manual_unblock_port(self):
        """Manually unblock a port"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        print("\n" + "=" * 80)
        print("MANUAL PORT UNBLOCK")
        print("=" * 80)
        
        # Show currently blocked ports
        if self.cm.blocked_ports:
            print("\nCurrently blocked ports:")
            for port in self.cm.blocked_ports:
                print(f"  • {port}")
            print()
        else:
            print("\nNo ports currently blocked")
            return
        
        try:
            port = input("Enter port number to unblock: ").strip()
            port = int(port)
            
            if port not in self.cm.blocked_ports:
                print(f"\n⚠️  Port {port} is not currently blocked")
                return
            
            confirm = input(f"\nUnblock port {port}? (y/n): ").strip().lower()
            if confirm == 'y':
                self.cm.manual_unblock_port(port)
                print(f"\n✓ Port {port} unblocked")
            else:
                print("\n❌ Cancelled")
        
        except ValueError:
            print("\n❌ Invalid port number")
    
    def clear_all_blocks(self):
        """Clear all blocks"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        if not self.cm.blocked_ips and not self.cm.blocked_ports:
            print("\n⚠️  No blocks currently active")
            return
        
        print("\n" + "=" * 80)
        print("CLEAR ALL BLOCKS")
        print("=" * 80)
        print(f"\nCurrently blocked:")
        print(f"  • IPs: {len(self.cm.blocked_ips)}")
        print(f"  • Ports: {len(self.cm.blocked_ports)}")
        print()
        
        confirm = input("Clear ALL blocks? (y/n): ").strip().lower()
        if confirm == 'y':
            self.cm.clear_all_blocks()
            print("\n✓ All blocks cleared")
        else:
            print("\n❌ Cancelled")
    
    def export_report(self):
        """Export detailed report"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        print("\n" + "=" * 80)
        print("EXPORT REPORT")
        print("=" * 80)
        
        print("\nGenerating report...")
        
        report_path = self.cm.export_report()
        print(f"\n✓ Report exported to: {report_path}")
    
    def view_blocked_items(self):
        """View currently blocked items"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        print("\n" + "=" * 80)
        print("CURRENTLY BLOCKED ITEMS")
        print("=" * 80)
        
        print("\nBLOCKED IPs:")
        if self.cm.blocked_ips:
            for ip in self.cm.blocked_ips:
                print(f"  • {ip}")
        else:
            print("  (none)")
        
        print("\nBLOCKED PORTS:")
        if self.cm.blocked_ports:
            for port in self.cm.blocked_ports:
                print(f"  • {port}")
        else:
            print("  (none)")
        
        print("=" * 80)
    
    def configure_thresholds(self):
        """Configure detection thresholds"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        print("\n" + "=" * 80)
        print("CONFIGURE THRESHOLDS")
        print("=" * 80)
        
        print(f"\nCurrent settings:")
        print(f"  • Block threshold: {self.cm.block_threshold}")
        print(f"  • Time window: {self.cm.time_window}s")
        print(f"  • Auto-block: {'ENABLED' if self.cm.auto_block else 'DISABLED'}")
        print()
        
        try:
            threshold = input(f"New block threshold [{self.cm.block_threshold}]: ").strip()
            if threshold:
                self.cm.block_threshold = int(threshold)
            
            window = input(f"New time window [{self.cm.time_window}]: ").strip()
            if window:
                self.cm.time_window = int(window)
            
            print("\n✓ Thresholds updated")
            print(f"  • Block threshold: {self.cm.block_threshold}")
            print(f"  • Time window: {self.cm.time_window}s")
        
        except ValueError:
            print("\n❌ Invalid input. Settings unchanged.")
    
    def toggle_auto_block(self):
        """Toggle auto-blocking"""
        if self.cm is None:
            print("\n❌ System not initialized")
            return
        
        self.cm.auto_block = not self.cm.auto_block
        status = "ENABLED" if self.cm.auto_block else "DISABLED"
        print(f"\n✓ Auto-block {status}")
    
    def run(self):
        """Run the UI"""
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ACTIVE MODE - MANUAL COUNTERMEASURES                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

Active Mode provides full manual control over countermeasure operations.

Features:
  • Manual intervention options
  • Detailed logging and statistics
  • Configurable thresholds
  • Step-by-step workflow guidance
  • Complete control over all operations

Recommended Workflow:
  1. Initialize System (option 1)
  2. Review Workflow Manual (option 13)
  3. Start Monitoring (option 3)
  4. Monitor and intervene as needed
  5. Export Report before shutdown (option 10)

╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        while True:
            try:
                self.show_main_menu()
                choice = input("\nSelect option: ").strip()
                
                if choice == '1':
                    self.initialize_system()
                elif choice == '2':
                    self.view_status()
                elif choice == '3':
                    self.start_monitoring()
                elif choice == '4':
                    self.stop_monitoring()
                elif choice == '5':
                    self.manual_block_ip()
                elif choice == '6':
                    self.manual_unblock_ip()
                elif choice == '7':
                    self.manual_block_port()
                elif choice == '8':
                    self.manual_unblock_port()
                elif choice == '9':
                    self.clear_all_blocks()
                elif choice == '10':
                    self.export_report()
                elif choice == '11':
                    self.view_blocked_items()
                elif choice == '12':
                    self.configure_thresholds()
                elif choice == '13':
                    show_workflow_manual()
                elif choice == '14':
                    self.toggle_auto_block()
                elif choice == '0':
                    if self.cm is not None and self.cm.running:
                        print("\nStopping monitoring first...")
                        self.cm.stop()
                        
                        if self.cm.blocked_ips or self.cm.blocked_ports:
                            clear = input("\nClear all blocks before exit? (y/n): ").strip().lower()
                            if clear == 'y':
                                self.cm.clear_all_blocks()
                    
                    print("\nExiting...")
                    break
                else:
                    print(f"\n❌ Invalid option: {choice}")
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Exiting...")
                if self.cm is not None and self.cm.running:
                    self.cm.stop()
                break
            
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    ui = ActiveUI()
    ui.run()


if __name__ == '__main__':
    main()

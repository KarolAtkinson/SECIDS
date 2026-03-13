#!/usr/bin/env python3
"""
Passive Mode - Minimal UI
===========================
Simple interface with only three controls: Start, Pause, Stop
Displays essential statistics in real-time.

Features:
- Start/Pause/Stop controls
- Real-time statistics display
- Input/Output traffic monitoring
- Threat detection count
- Whitelist/Blacklist/Greylist counts
- Countermeasure deployment status
- Success/Error indicators
"""

import sys
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

# Import passive mode countermeasure
sys.path.insert(0, str(Path(__file__).parent))
from countermeasure_passive import PassiveCountermeasure


class PassiveUI:
    """Minimal UI for Passive Mode"""
    
    def __init__(self):
        self.cm: Optional[PassiveCountermeasure] = None
        self.running = False
        self.display_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start passive countermeasure system"""
        if self.cm is not None and self.cm.running:
            print("⚠️  System already running")
            return
        
        print("Starting passive countermeasure system...")
        self.cm = PassiveCountermeasure()
        
        # Check sudo availability and warn user
        if not self.cm.sudo_available:
            print("\n" + "="*80)
            print("⚠️  WARNING: Sudo privileges not available!")
            print("="*80)
            print("Countermeasures will detect threats but CANNOT block IPs/ports.")
            print("\nTo enable blocking, either:")
            print("  1. Run with sudo: sudo python3 Countermeasures/passive_ui.py")
            print("  2. Configure passwordless sudo: sudo bash Countermeasures/setup_passwordless_sudo.sh")
            print("="*80)
            print()
            
            response = input("Continue without blocking capability? (y/n): ").strip().lower()
            if response != 'y':
                print("Cancelled.")
                self.cm.stop()
                self.cm = None
                return
        
        self.running = True
        
        # Start display thread
        self.display_thread = threading.Thread(target=self._update_display, daemon=True)
        self.display_thread.start()
        
        print("✓ System started")
    
    def pause(self):
        """Pause countermeasure processing"""
        if self.cm is None:
            print("⚠️  System not started")
            return
        
        self.cm.pause()
        print("⏸️  System paused (monitoring only, no blocking)")
    
    def stop(self):
        """Stop countermeasure system"""
        if self.cm is None:
            print("⚠️  System not started")
            return
        
        self.running = False
        self.cm.stop()
        print("⏹️  System stopped")
        
        # Show final stats
        self._print_final_stats()
    
    def _update_display(self):
        """Update statistics display (runs in background thread)"""
        while self.running:
            try:
                if self.cm is None:
                    break
                
                stats = self.cm.get_simple_stats()
                health = self.cm.get_health_status()
                
                # Clear previous line and display updated stats
                status_line = (
                    f"\r[{stats['runtime']:.0f}s] "
                    f"In: {stats['input_traffic']} | "
                    f"Out: {stats['output_traffic']} | "
                    f"Threats: {stats['threats_detected']} | "
                    f"Blocked: {stats['countermeasures_deployed']} | "
                    f"W:{stats['whitelist_count']} B:{stats['blacklist_count']} G:{stats['greylist_count']} | "
                    f"{'✓' if health == 'healthy' else '⚠️' if health == 'warning' else '❌'} "
                    f"Errors: {stats['countermeasures_errors']}"
                )
                
                print(status_line, end='', flush=True)
                
                time.sleep(2)  # Update every 2 seconds
            except Exception:
                break
    
    def _print_final_stats(self):
        """Print final statistics"""
        if self.cm is None:
            return
        
        stats = self.cm.get_simple_stats()
        
        print("\n")
        print("=" * 80)
        print("FINAL STATISTICS")
        print("=" * 80)
        print(f"Runtime: {stats['runtime']:.0f} seconds")
        print()
        print("TRAFFIC:")
        print(f"  Input (threats detected): {stats['input_traffic']}")
        print(f"  Output (actions taken): {stats['output_traffic']}")
        print()
        print("COUNTERMEASURES:")
        print(f"  Deployed: {stats['countermeasures_deployed']}")
        print(f"  Success: {stats['countermeasures_success']}")
        print(f"  Errors: {stats['countermeasures_errors']}")
        print()
        print("IP LISTS:")
        print(f"  Whitelist: {stats['whitelist_count']}")
        print(f"  Blacklist: {stats['blacklist_count']}")
        print(f"  Greylist: {stats['greylist_count']}")
        print("=" * 80)
    
    def show_menu(self):
        """Display simple menu"""
        print()
        print("=" * 80)
        print("PASSIVE MODE - COUNTERMEASURE SYSTEM")
        print("=" * 80)
        print()
        print("Controls:")
        print("  1. Start    - Begin automatic threat detection and blocking")
        print("  2. Pause    - Pause blocking (monitoring continues)")
        print("  3. Stop     - Stop system and show statistics")
        print("  q. Quit     - Exit")
        print()
        print("=" * 80)
        print()
    
    def run(self):
        """Run the UI"""
        self.show_menu()
        
        while True:
            try:
                choice = input("Select option [1/2/3/q]: ").strip().lower()
                
                if choice == '1':
                    self.start()
                    print("\nMonitoring (press Enter for menu)...")
                    print()
                
                elif choice == '2':
                    self.pause()
                
                elif choice == '3':
                    self.stop()
                
                elif choice == 'q':
                    if self.cm is not None and self.cm.running:
                        print("\nStopping system first...")
                        self.stop()
                    print("\nExiting...")
                    break
                
                else:
                    print(f"Invalid option: {choice}")
                    self.show_menu()
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Stopping...")
                if self.cm is not None and self.cm.running:
                    self.stop()
                break
            
            except Exception as e:
                print(f"\nError: {e}")


def main():
    """Main entry point"""
    ui = PassiveUI()
    ui.run()


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  PASSIVE MODE - AUTOMATED COUNTERMEASURES                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Passive Mode provides fully automatic threat response with minimal user interaction.

Features:
  • Automatic threat detection and blocking
  • Fast response (3 threats in 30 seconds triggers block)
  • Silent operation (logs to file)
  • Real-time statistics
  • Whitelist/Blacklist/Greylist integration

Display Legend:
  In:  Input traffic (threats detected)
  Out: Output traffic (actions taken)
  W/B/G: Whitelist/Blacklist/Greylist counts
  ✓/⚠️/❌: Health status (healthy/warning/error)

╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    main()

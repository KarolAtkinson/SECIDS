#!/usr/bin/env python3
"""
DDoS Countermeasure - Passive Mode
====================================
Automatic operation with minimal user interface.
Runs everything automatically using only the fastest and basic tools.

Features:
- Fully automatic threat response
- Minimal configuration
- Silent operation (logs only)
- Fast processing (no user interaction)
- Basic statistics export
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# Import core functionality
sys.path.insert(0, str(Path(__file__).parent))
from countermeasure_core import CountermeasureCore


class PassiveCountermeasure(CountermeasureCore):
    """
    Passive Mode: Automatic operation with minimal UI
    
    Operation:
    - Auto-start on initialization
    - Auto-block enabled by default
    - Fast thresholds (quick response)
    - Silent logging
    - No user prompts
    """
    
    def __init__(self,
                 block_threshold: int = 3,      # Lower threshold (faster response)
                 time_window: int = 30,         # Shorter window (faster detection)
                 log_file: Optional[str] = None):
        """
        Initialize Passive Mode countermeasure
        
        Args:
            block_threshold: Threats before auto-blocking (default: 3 - faster than Active)
            time_window: Time window in seconds (default: 30 - shorter than Active)
            log_file: Path to log file (optional)
        """
        # Initialize with passive mode settings
        log_path = Path(log_file) if log_file else None
        
        super().__init__(
            mode="passive",
            block_threshold=block_threshold,
            time_window=time_window,
            auto_block=True,  # Always auto-block in passive mode
            log_file=log_path
        )
        
        # Override logging to be silent (file only)
        self.silent = True
        
        # Auto-start
        self.start()
    
    def _log(self, message: str, level: str = "INFO"):
        """Silent logging (file only, no console output)"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # Write to log file only (no console output)
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except (OSError, IOError) as exc:
            print(f"[{timestamp}] [WARNING] Log file write failed: {exc}")
    
    def get_simple_stats(self) -> Dict:
        """
        Get simplified statistics for passive mode UI
        
        Returns:
            Dictionary with essential stats only
        """
        stats = self.get_statistics()
        status = self.get_status()
        
        return {
            # Traffic stats
            'threats_detected': stats['threats_detected'],
            'input_traffic': stats['threats_detected'],  # Simplified metric
            'output_traffic': stats['actions_taken'],     # Actions = output responses
            
            # List stats
            'whitelist_count': status['whitelist_size'],
            'blacklist_count': status['blacklist_size'],
            'greylist_count': status['greylist_size'],
            
            # Countermeasure stats
            'countermeasures_deployed': stats['ips_blocked'] + stats['ports_blocked'],
            'countermeasures_success': stats['ips_blocked'] + stats['ports_blocked'],
            'countermeasures_errors': stats['errors'],
            
            # Status
            'running': self.running,
            'runtime': stats['runtime_seconds']
        }
    
    def pause(self):
        """Pause countermeasure processing (stop auto-blocking)"""
        self.auto_block = False
        self._log("Passive mode PAUSED (auto-block disabled)")
    
    def resume(self):
        """Resume countermeasure processing"""
        self.auto_block = True
        self._log("Passive mode RESUMED (auto-block enabled)")
    
    def get_health_status(self) -> str:
        """
        Get system health status
        
        Returns:
            'healthy', 'warning', or 'error'
        """
        stats = self.get_statistics()
        
        # Error rate check
        if stats['errors'] > 10:
            return 'error'
        elif stats['errors'] > 3:
            return 'warning'
        
        # Threat rate check
        threat_rate = stats['threats_per_minute']
        if threat_rate > 100:
            return 'warning'
        
        return 'healthy'


# Convenience function for quick initialization
def start_passive_mode(block_threshold: int = 3, time_window: int = 30):
    """
    Quick start for passive mode
    
    Args:
        block_threshold: Threats before blocking (default: 3)
        time_window: Time window in seconds (default: 30)
    
    Returns:
        PassiveCountermeasure instance (already running)
    """
    return PassiveCountermeasure(
        block_threshold=block_threshold,
        time_window=time_window
    )


if __name__ == '__main__':
    print("=" * 80)
    print("DDoS Countermeasure - Passive Mode")
    print("=" * 80)
    print("Starting automatic countermeasure system...")
    print()
    
    # Start passive mode
    cm = start_passive_mode()
    
    print("✓ Passive mode active")
    print(f"✓ Threshold: {cm.block_threshold} threats in {cm.time_window}s")
    print(f"✓ Log file: {cm.log_file}")
    print()
    print("System running... (Press Ctrl+C to stop)")
    print()
    
    try:
        import time
        
        # Monitor and display stats periodically
        while True:
            time.sleep(10)
            stats = cm.get_simple_stats()
            
            print(f"\r[{stats['runtime']:.0f}s] Threats: {stats['threats_detected']} | "
                  f"Blocked: {stats['countermeasures_deployed']} | "
                  f"Errors: {stats['countermeasures_errors']}", end='', flush=True)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
        cm.stop()
        
        # Print final stats
        final_stats = cm.get_simple_stats()
        print("\n" + "=" * 80)
        print("FINAL STATISTICS")
        print("=" * 80)
        print(f"Runtime: {final_stats['runtime']:.0f} seconds")
        print(f"Threats detected: {final_stats['threats_detected']}")
        print(f"Countermeasures deployed: {final_stats['countermeasures_deployed']}")
        print(f"Success rate: {final_stats['countermeasures_success']}/{final_stats['countermeasures_deployed']}")
        print(f"Whitelist: {final_stats['whitelist_count']} | "
              f"Blacklist: {final_stats['blacklist_count']} | "
              f"Greylist: {final_stats['greylist_count']}")
        print("=" * 80)

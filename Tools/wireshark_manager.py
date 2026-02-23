#!/usr/bin/env python3
"""
Wireshark Manager - Auto-open/close Wireshark for live capture sessions.

This module provides automatic Wireshark management for live traffic capture:
- Starts Wireshark with the specified interface before capture begins
- Closes Wireshark gracefully when capture ends
- Supports both eth0 and any interface options
"""

import subprocess
import time
import os
import signal
import psutil
from pathlib import Path


class WiresharkManager:
    """Manages Wireshark process lifecycle for live capture sessions."""
    
    def __init__(self, interface='eth0', use_any=False):
        """
        Initialize Wireshark Manager.
        
        Args:
            interface: Network interface to capture on (default: eth0)
            use_any: If True, uses 'any' interface instead (captures all interfaces)
        """
        self.interface = 'any' if use_any else interface
        self.process = None
        self.pid = None
        self.is_running = False
        
    def start(self, background=True):
        """
        Start Wireshark with specified interface.
        
        Args:
            background: If True, runs in background without GUI. If False, opens GUI.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            # Check if Wireshark is already running
            if self._is_wireshark_running():
                print("⚠️  Wireshark is already running")
                return True
            
            # Build command based on mode
            if background:
                # Use dumpcap for background capture (more efficient)
                # Use timestamp-based filename to avoid conflicts
                timestamp = int(time.time())
                temp_file = f'/tmp/wireshark_live_capture_{timestamp}_{self.interface}.pcapng'
                cmd = ['dumpcap', '-i', self.interface, '-P', '-w', temp_file]
                print(f"🔍 Starting background packet capture on {self.interface}...")
                print(f"   Capture file: {temp_file}")
            else:
                # Open Wireshark GUI
                cmd = ['wireshark', '-i', self.interface, '-k']
                print(f"🦈 Starting Wireshark GUI on {self.interface}...")
            
            # Check if command exists
            if not self._command_exists(cmd[0]):
                print(f"❌ Error: {cmd[0]} not found. Please install Wireshark.")
                return False
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group
            )
            self.pid = self.process.pid
            self.is_running = True
            
            # Give it a moment to start
            time.sleep(2)
            
            # Verify it's running
            if self.process.poll() is None:
                print(f"✓ Wireshark started successfully (PID: {self.pid})")
                return True
            else:
                print("❌ Wireshark failed to start")
                self.is_running = False
                return False
                
        except Exception as e:
            print(f"❌ Error starting Wireshark: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """
        Stop Wireshark gracefully.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_running:
            print("ℹ️  Wireshark is not running")
            return True
        
        try:
            print("🛑 Stopping Wireshark...")
            
            # Try graceful shutdown first
            if self.process and self.process.poll() is None:
                # Send SIGTERM to the process group
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except ProcessLookupError as e:
                    pass  # Skip on error
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop gracefully
                    print("⚠️  Forcing Wireshark to close...")
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except ProcessLookupError as e:
                        pass  # Skip on error
            # Also kill any remaining Wireshark/dumpcap processes
            self._kill_remaining_processes()
            
            self.is_running = False
            self.process = None
            self.pid = None
            
            print("✓ Wireshark stopped successfully")
            return True
            
        except Exception as e:
            print(f"⚠️  Error stopping Wireshark: {e}")
            # Try to kill any remaining processes anyway
            self._kill_remaining_processes()
            self.is_running = False
            return False
    
    def _is_wireshark_running(self):
        """Check if Wireshark or dumpcap is already running."""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in ['wireshark', 'dumpcap']:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def _kill_remaining_processes(self):
        """Kill any remaining Wireshark/dumpcap processes."""
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] in ['wireshark', 'dumpcap']:
                    os.kill(proc.info['pid'], signal.SIGTERM)
                    time.sleep(0.5)
                    try:
                        os.kill(proc.info['pid'], signal.SIGKILL)
                    except ProcessLookupError as e:
                        pass  # Skip on error
            except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
                continue
    
    def _command_exists(self, command):
        """Check if a command exists in the system PATH."""
        return subprocess.call(
            ['which', command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ) == 0
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


# Convenience functions
def start_wireshark(interface='eth0', use_any=False, background=True):
    """
    Start Wireshark with specified interface.
    
    Args:
        interface: Network interface to capture on
        use_any: If True, uses 'any' interface
        background: If True, runs in background
    
    Returns:
        WiresharkManager: Manager instance
    """
    manager = WiresharkManager(interface, use_any)
    manager.start(background)
    return manager


def stop_wireshark(manager):
    """
    Stop Wireshark using manager instance.
    
    Args:
        manager: WiresharkManager instance
    
    Returns:
        bool: True if stopped successfully
    """
    if manager:
        return manager.stop()
    return True


if __name__ == '__main__':
    # Test the manager
    print("Testing Wireshark Manager...")
    print("-" * 60)
    
    # Test with context manager
    print("\nTest 1: Using context manager (auto-start/stop)")
    with WiresharkManager('eth0') as ws:
        print("Capturing for 5 seconds...")
        time.sleep(5)
    
    print("\nTest 2: Manual start/stop")
    manager = WiresharkManager('any', use_any=True)
    manager.start()
    print("Capturing for 5 seconds...")
    time.sleep(5)
    manager.stop()
    
    print("\nAll tests completed!")

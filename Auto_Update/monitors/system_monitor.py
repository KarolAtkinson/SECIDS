#!/usr/bin/env python3
"""
System Monitor
Monitors system health and triggers tasks when thresholds are exceeded
"""

import psutil
import json
from datetime import datetime
from pathlib import Path

class SystemMonitor:
    """Monitor system resources and dataset status"""
    
    def __init__(self):
        """Initialize system monitor"""
        self.project_root = Path(__file__).parent.parent.parent
        self.monitors_dir = Path(__file__).parent
        self.status_file = self.monitors_dir / 'system_status.json'
    
    def check_disk_space(self):
        """Check available disk space"""
        usage = psutil.disk_usage(str(self.project_root))
        
        return {
            'total_gb': round(usage.total / (1024**3), 2),
            'used_gb': round(usage.used / (1024**3), 2),
            'free_gb': round(usage.free / (1024**3), 2),
            'percent_used': usage.percent,
            'needs_cleanup': usage.percent > 80
        }
    
    def check_dataset_status(self):
        """Check dataset file counts and sizes"""
        datasets_dir = self.project_root / 'SecIDS-CNN' / 'datasets'
        
        if not datasets_dir.exists():
            return {'error': 'Datasets directory not found'}
        
        csv_files = list(datasets_dir.glob('*.csv'))
        refined_files = [f for f in csv_files if '_refined' in f.name]
        result_files = [f for f in csv_files if '_results' in f.name]
        raw_files = [f for f in csv_files if '_refined' not in f.name and '_results' not in f.name]
        
        total_size = sum(f.stat().st_size for f in csv_files)
        
        return {
            'total_csv_files': len(csv_files),
            'refined_datasets': len(refined_files),
            'result_files': len(result_files),
            'raw_datasets': len(raw_files),
            'total_size_mb': round(total_size / (1024**2), 2),
            'needs_refinement': len(raw_files) > 10,
            'needs_cleanup': len(result_files) > 20
        }
    
    def check_capture_files(self):
        """Check packet capture files"""
        captures_dir = self.project_root / 'captures'
        
        if not captures_dir.exists():
            return {'error': 'Captures directory not found'}
        
        pcap_files = list(captures_dir.glob('*.pcap'))
        total_size = sum(f.stat().st_size for f in pcap_files)
        
        return {
            'pcap_files': len(pcap_files),
            'total_size_mb': round(total_size / (1024**2), 2),
            'needs_processing': len(pcap_files) > 5
        }
    
    def check_blacklist_status(self):
        """Check blacklist size and status"""
        blacklist_dir = self.project_root / 'Device_Profile' / 'Blacklist'
        
        if not blacklist_dir.exists():
            return {'error': 'Blacklist directory not found'}
        
        threat_profiles = list((blacklist_dir / 'threat_profiles').glob('threat_*.json'))
        
        return {
            'threat_profiles': len(threat_profiles),
            'needs_cleanup': len(threat_profiles) > 1000
        }
    
    def check_trashdump(self):
        """Check TrashDump size"""
        trashdump_dir = self.project_root / 'TrashDump'
        
        if not trashdump_dir.exists():
            return {'files': 0, 'size_mb': 0}
        
        files = list(trashdump_dir.rglob('*'))
        files = [f for f in files if f.is_file()]
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            'files': len(files),
            'size_mb': round(total_size / (1024**2), 2),
            'needs_cleanup': total_size > 100 * 1024 * 1024  # >100MB
        }
    
    def get_system_status(self):
        """Get complete system status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'disk_space': self.check_disk_space(),
            'datasets': self.check_dataset_status(),
            'captures': self.check_capture_files(),
            'blacklist': self.check_blacklist_status(),
            'trashdump': self.check_trashdump()
        }
        
        # Determine if any action is needed
        needs_action = []
        
        if status['disk_space'].get('needs_cleanup', False):
            needs_action.append('disk_cleanup')
        
        if status['datasets'].get('needs_refinement', False):
            needs_action.append('dataset_refinement')
        
        if status['datasets'].get('needs_cleanup', False):
            needs_action.append('dataset_cleanup')
        
        if status['captures'].get('needs_processing', False):
            needs_action.append('capture_processing')
        
        if status['blacklist'].get('needs_cleanup', False):
            needs_action.append('blacklist_cleanup')
        
        if status['trashdump'].get('needs_cleanup', False):
            needs_action.append('trashdump_cleanup')
        
        status['actions_needed'] = needs_action
        
        return status
    
    def save_status(self):
        """Save system status to file"""
        status = self.get_system_status()
        
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        return status
    
    def print_status(self):
        """Print formatted system status"""
        status = self.get_system_status()
        
        print("\n" + "="*60)
        print("SYSTEM STATUS REPORT")
        print("="*60)
        print(f"Timestamp: {status['timestamp']}\n")
        
        print("Disk Space:")
        disk = status['disk_space']
        if 'error' not in disk:
            print(f"  Total: {disk['total_gb']} GB")
            print(f"  Used: {disk['used_gb']} GB ({disk['percent_used']}%)")
            print(f"  Free: {disk['free_gb']} GB")
            if disk['needs_cleanup']:
                print("  ⚠️  WARNING: Low disk space!")
        
        print("\nDatasets:")
        datasets = status['datasets']
        if 'error' not in datasets:
            print(f"  Total CSV files: {datasets['total_csv_files']}")
            print(f"  Refined datasets: {datasets['refined_datasets']}")
            print(f"  Raw datasets: {datasets['raw_datasets']}")
            print(f"  Result files: {datasets['result_files']}")
            print(f"  Total size: {datasets['total_size_mb']} MB")
            if datasets['needs_refinement']:
                print("  ⚠️  Action needed: Dataset refinement")
        
        print("\nPacket Captures:")
        captures = status['captures']
        if 'error' not in captures:
            print(f"  PCAP files: {captures['pcap_files']}")
            print(f"  Total size: {captures['total_size_mb']} MB")
            if captures['needs_processing']:
                print("  ⚠️  Action needed: Process captures")
        
        print("\nBlacklist:")
        blacklist = status['blacklist']
        if 'error' not in blacklist:
            print(f"  Threat profiles: {blacklist['threat_profiles']}")
            if blacklist['needs_cleanup']:
                print("  ⚠️  Action needed: Cleanup old entries")
        
        print("\nTrashDump:")
        trashdump = status['trashdump']
        print(f"  Files: {trashdump['files']}")
        print(f"  Size: {trashdump['size_mb']} MB")
        if trashdump['needs_cleanup']:
            print("  ⚠️  Action needed: Empty TrashDump")
        
        if status['actions_needed']:
            print("\n" + "="*60)
            print("RECOMMENDED ACTIONS:")
            for action in status['actions_needed']:
                print(f"  • {action}")
        else:
            print("\n✓ All systems nominal")
        
        print("="*60 + "\n")


if __name__ == '__main__':
    monitor = SystemMonitor()
    monitor.print_status()
    monitor.save_status()

#!/usr/bin/env python3
"""
SecIDS-CNN System Optimizer
============================
Removes redundant files, cleans cache, and optimizes disk usage.

Usage:
    python3 Scripts/optimize_system.py [--dry-run] [--aggressive]
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import argparse


class SystemOptimizer:
    """Optimize SecIDS-CNN system by removing redundant files"""
    
    def __init__(self, project_root: Path, dry_run: bool = False, aggressive: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.aggressive = aggressive
        self.total_saved = 0
        self.items_removed = 0
        
    def get_size(self, path: Path) -> int:
        """Get size of file or directory"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total = 0
            try:
                for item in path.rglob('*'):
                    if item.is_file():
                        total += item.stat().st_size
            except Exception as e:
                pass  # Skip on error
            return total
        return 0
    
    def format_size(self, bytes_size: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    
    def remove_pycache(self):
        """Remove __pycache__ directories"""
        print("\n🗑️  Removing Python cache files...")
        print("=" * 60)
        
        # Skip venv directories
        skip_dirs = {'.venv_test', '.venv', 'venv', 'env'}
        
        pycache_dirs = []
        for root, dirs, _ in os.walk(self.project_root):
            # Remove skip directories from search
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            if '__pycache__' in dirs:
                pycache_path = Path(root) / '__pycache__'
                pycache_dirs.append(pycache_path)
        
        for pycache in pycache_dirs:
            size = self.get_size(pycache)
            rel_path = pycache.relative_to(self.project_root)
            
            if self.dry_run:
                print(f"  [DRY RUN] Would remove: {rel_path} ({self.format_size(size)})")
            else:
                try:
                    shutil.rmtree(pycache)
                    print(f"  ✓ Removed: {rel_path} ({self.format_size(size)})")
                    self.total_saved += size
                    self.items_removed += 1
                except Exception as e:
                    print(f"  ✗ Error removing {rel_path}: {e}")
        
        print(f"\n  Found {len(pycache_dirs)} __pycache__ directories")
    
    def remove_pyc_files(self):
        """Remove .pyc files"""
        print("\n🗑️  Removing .pyc files...")
        print("=" * 60)
        
        skip_dirs = {'.venv_test', '.venv', 'venv', 'env'}
        pyc_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if file.endswith('.pyc'):
                    pyc_files.append(Path(root) / file)
        
        for pyc_file in pyc_files:
            size = self.get_size(pyc_file)
            
            if self.dry_run:
                print(f"  [DRY RUN] Would remove: {pyc_file.name}")
            else:
                try:
                    pyc_file.unlink()
                    self.total_saved += size
                    self.items_removed += 1
                except Exception as e:
                    print(f"  ✗ Error removing {pyc_file}: {e}")
        
        if not self.dry_run and pyc_files:
            print(f"  ✓ Removed {len(pyc_files)} .pyc files")
        else:
            print(f"  Found {len(pyc_files)} .pyc files")
    
    def clean_logs(self):
        """Clean old log files"""
        print("\n🗑️  Cleaning old log files...")
        print("=" * 60)
        
        log_dirs = [
            self.project_root / 'Logs',
            self.project_root / 'Auto_Update' / 'logs',
            self.project_root / 'logs'
        ]
        
        old_logs = []
        for log_dir in log_dirs:
            if log_dir.exists():
                for log_file in log_dir.glob('*.log'):
                    # Keep logs from today
                    age_days = (datetime.now().timestamp() - log_file.stat().st_mtime) / 86400
                    if age_days > 7:  # Older than 7 days
                        old_logs.append((log_file, age_days))
        
        for log_file, age in old_logs:
            size = self.get_size(log_file)
            rel_path = log_file.relative_to(self.project_root)
            
            if self.dry_run:
                print(f"  [DRY RUN] Would remove: {rel_path} ({int(age)} days old, {self.format_size(size)})")
            else:
                try:
                    log_file.unlink()
                    print(f"  ✓ Removed: {rel_path} ({int(age)} days old, {self.format_size(size)})")
                    self.total_saved += size
                    self.items_removed += 1
                except Exception as e:
                    print(f"  ✗ Error removing {rel_path}: {e}")
        
        print(f"\n  Processed {len(old_logs)} old log files")
    
    def clean_temp_captures(self):
        """Clean temporary capture files"""
        print("\n🗑️  Cleaning temporary captures...")
        print("=" * 60)
        
        captures_dir = self.project_root / 'Captures'
        if not captures_dir.exists():
            print("  No Captures directory found")
            return
        
        temp_files = list(captures_dir.glob('capture_temp_*.pcap'))
        
        for temp_file in temp_files:
            size = self.get_size(temp_file)
            
            if self.dry_run:
                print(f"  [DRY RUN] Would remove: {temp_file.name} ({self.format_size(size)})")
            else:
                try:
                    temp_file.unlink()
                    print(f"  ✓ Removed: {temp_file.name} ({self.format_size(size)})")
                    self.total_saved += size
                    self.items_removed += 1
                except Exception as e:
                    print(f"  ✗ Error removing {temp_file}: {e}")
        
        print(f"\n  Found {len(temp_files)} temporary capture files")
    
    def remove_duplicate_models(self):
        """Remove duplicate model files (keep newest)"""
        print("\n🗑️  Checking for duplicate models...")
        print("=" * 60)
        
        # Check for SecIDS-CNN.h5 in multiple locations
        models_locations = [
            self.project_root / 'Models' / 'SecIDS-CNN.h5',
            self.project_root / 'SecIDS-CNN' / 'SecIDS-CNN.h5'
        ]
        
        existing_models = [(m, m.stat().st_mtime) for m in models_locations if m.exists()]
        
        if len(existing_models) > 1:
            # Sort by modification time (newest first)
            existing_models.sort(key=lambda x: x[1], reverse=True)
            newest = existing_models[0][0]
            
            print(f"  ℹ️  Keeping newest: {newest.relative_to(self.project_root)}")
            
            # Remove older duplicates
            for model, _ in existing_models[1:]:
                size = self.get_size(model)
                rel_path = model.relative_to(self.project_root)
                
                if self.dry_run:
                    print(f"  [DRY RUN] Would remove duplicate: {rel_path} ({self.format_size(size)})")
                else:
                    print(f"  ℹ️  Keeping both models for compatibility")
                    # Don't actually remove - models in different locations serve different purposes
        else:
            print("  ✓ No duplicate models found")
    
    def clean_empty_dirs(self):
        """Remove empty directories"""
        if not self.aggressive:
            return
        
        print("\n🗑️  Removing empty directories...")
        print("=" * 60)
        
        skip_dirs = {'.venv_test', '.venv', 'venv', 'env', '.git'}
        empty_dirs = []
        
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        empty_dirs.append(dir_path)
                except Exception as e:
                    pass  # Skip on error
        for empty_dir in empty_dirs:
            rel_path = empty_dir.relative_to(self.project_root)
            
            if self.dry_run:
                print(f"  [DRY RUN] Would remove: {rel_path}/")
            else:
                try:
                    empty_dir.rmdir()
                    print(f"  ✓ Removed: {rel_path}/")
                    self.items_removed += 1
                except Exception as e:
                    print(f"  ✗ Error removing {rel_path}: {e}")
        
        print(f"\n  Found {len(empty_dirs)} empty directories")
    
    def optimize(self):
        """Run all optimization tasks"""
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║     SecIDS-CNN System Optimizer                         ║")
        print("╚══════════════════════════════════════════════════════════╝")
        
        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No files will be deleted\n")
        
        if self.aggressive:
            print("⚠️  AGGRESSIVE MODE - Will remove more files\n")
        
        print(f"📁 Project Root: {self.project_root}\n")
        
        # Run optimization tasks
        self.remove_pycache()
        self.remove_pyc_files()
        self.clean_logs()
        self.clean_temp_captures()
        self.remove_duplicate_models()
        self.clean_empty_dirs()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 OPTIMIZATION SUMMARY")
        print("=" * 60)
        
        if self.dry_run:
            print(f"Mode: DRY RUN (no changes made)")
        else:
            print(f"✓ Items removed: {self.items_removed}")
            print(f"✓ Disk space saved: {self.format_size(self.total_saved)}")
        
        print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Optimize SecIDS-CNN system')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--aggressive', action='store_true',
                       help='More aggressive cleanup (includes empty directories)')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    optimizer = SystemOptimizer(project_root, dry_run=args.dry_run, aggressive=args.aggressive)
    optimizer.optimize()
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to actually remove files")
    
    print()


if __name__ == "__main__":
    main()

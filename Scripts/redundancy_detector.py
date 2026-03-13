#!/usr/bin/env python3
"""
Redundant File Detector and Mover
Identifies duplicate and redundant files in the SECIDS-CNN project
and moves them to TrashDump for review/removal
"""

import os
import sys
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Set, Optional

PROJECT_ROOT = Path(__file__).parent.parent
TRASH_DUMP = PROJECT_ROOT / "TrashDump"
TRASH_DUMP.mkdir(exist_ok=True)

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    ".venv_test", ".venv", "__pycache__", ".git", 
    "Model_Tester/.venv", "SecIDS-CNN/.venv",
    "node_modules", ".pytest_cache", "TrashDump"
}

# File patterns to consider redundant
REDUNDANT_PATTERNS = [
    "*_old.*", "*_backup.*", "*.bak", "*_copy.*", "*~",
    "*.tmp", "*.temp", "*_test_old.*", "*_deprecated.*"
]

class RedundancyDetector:
    def __init__(self):
        self.duplicates = defaultdict(list)
        self.redundant_files = []
        self.pycache_dirs = []
        self.pyc_files = []
        self.moved_files = []
        self.stats = {
            "pycache_removed": 0,
            "pyc_removed": 0,
            "duplicates_found": 0,
            "redundant_patterns": 0,
            "total_moved": 0
        }
    
    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded from scanning"""
        path_str = str(path)
        return any(excluded in path_str for excluded in EXCLUDE_DIRS)
    
    def get_file_hash(self, filepath: Path) -> Optional[str]:
        """Calculate MD5 hash of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, IOError):
            # Cannot read file
            return None
    
    def find_pycache_dirs(self):
        """Find all __pycache__ directories"""
        print("\n🔍 Searching for __pycache__ directories...")
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
            
            if "__pycache__" in dirs:
                pycache_path = Path(root) / "__pycache__"
                self.pycache_dirs.append(pycache_path)
                size = sum(f.stat().st_size for f in pycache_path.rglob('*') if f.is_file())
                print(f"  Found: {pycache_path} ({size/1024:.1f} KB)")
    
    def find_pyc_files(self):
        """Find all .pyc files"""
        print("\n🔍 Searching for .pyc files...")
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
            
            for file in files:
                if file.endswith('.pyc'):
                    pyc_path = Path(root) / file
                    if not self.should_exclude(pyc_path):
                        self.pyc_files.append(pyc_path)
    
    def find_redundant_patterns(self):
        """Find files matching redundant patterns"""
        print("\n🔍 Searching for redundant file patterns...")
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
            
            for file in files:
                file_lower = file.lower()
                # Check for redundant patterns
                if any(pattern.replace('*', '') in file_lower for pattern in REDUNDANT_PATTERNS):
                    file_path = Path(root) / file
                    if not self.should_exclude(file_path):
                        self.redundant_files.append(file_path)
                        print(f"  Found redundant: {file_path.relative_to(PROJECT_ROOT)}")
    
    def find_duplicate_files(self):
        """Find duplicate files based on content hash"""
        print("\n🔍 Searching for duplicate files by content...")
        file_hashes = defaultdict(list)
        
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip very large files and certain types
                if file_path.stat().st_size > 10 * 1024 * 1024:  # Skip files > 10MB
                    continue
                
                if self.should_exclude(file_path):
                    continue
                
                # Skip certain file types
                if file_path.suffix in ['.csv', '.pcap', '.h5', '.log']:
                    continue
                
                file_hash = self.get_file_hash(file_path)
                if file_hash:
                    file_hashes[file_hash].append(file_path)
        
        # Identify duplicates
        for file_hash, paths in file_hashes.items():
            if len(paths) > 1:
                self.duplicates[file_hash] = paths
                self.stats["duplicates_found"] += len(paths) - 1
                print(f"\n  Duplicate set ({len(paths)} files):")
                for path in paths:
                    print(f"    - {path.relative_to(PROJECT_ROOT)}")
    
    def move_to_trash(self, file_path: Path, reason: str):
        """Move file to TrashDump with timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            relative_path = file_path.relative_to(PROJECT_ROOT)
            
            # Create subdirectory structure in TrashDump
            trash_subdir = TRASH_DUMP / relative_path.parent
            trash_subdir.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp to filename
            new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            trash_path = trash_subdir / new_name
            
            # Move file
            shutil.move(str(file_path), str(trash_path))
            self.moved_files.append((relative_path, reason))
            return True
        except Exception as e:
            print(f"  ⚠️  Error moving {file_path}: {e}")
            return False
    
    def cleanup_pycache(self):
        """Remove all __pycache__ directories"""
        if not self.pycache_dirs:
            return
        
        print(f"\n🗑️  Removing {len(self.pycache_dirs)} __pycache__ directories...")
        for pycache_dir in self.pycache_dirs:
            try:
                shutil.rmtree(pycache_dir)
                self.stats["pycache_removed"] += 1
                print(f"  ✓ Removed: {pycache_dir.relative_to(PROJECT_ROOT)}")
            except Exception as e:
                print(f"  ⚠️  Error removing {pycache_dir}: {e}")
    
    def cleanup_pyc_files(self):
        """Remove all .pyc files"""
        if not self.pyc_files:
            return
        
        print(f"\n🗑️  Removing {len(self.pyc_files)} .pyc files...")
        for pyc_file in self.pyc_files:
            try:
                pyc_file.unlink()
                self.stats["pyc_removed"] += 1
            except Exception as e:
                print(f"  ⚠️  Error removing {pyc_file}: {e}")
        
        if self.stats["pyc_removed"] > 0:
            print(f"  ✓ Removed {self.stats['pyc_removed']} .pyc files")
    
    def move_redundant_files(self):
        """Move files with redundant patterns to TrashDump"""
        if not self.redundant_files:
            print("\n✅ No redundant pattern files found")
            return
        
        print(f"\n🗑️  Moving {len(self.redundant_files)} redundant files to TrashDump...")
        for file_path in self.redundant_files:
            if self.move_to_trash(file_path, "Redundant pattern"):
                self.stats["redundant_patterns"] += 1
                self.stats["total_moved"] += 1
    
    def move_duplicate_files(self):
        """Move duplicate files (keeping one of each set)"""
        if not self.duplicates:
            print("\n✅ No duplicate files found")
            return
        
        print(f"\n🗑️  Moving duplicate files to TrashDump...")
        for file_hash, paths in self.duplicates.items():
            # Keep the first file, move the rest
            keep_file = paths[0]
            print(f"\n  Keeping: {keep_file.relative_to(PROJECT_ROOT)}")
            
            for dup_path in paths[1:]:
                if self.move_to_trash(dup_path, f"Duplicate of {keep_file.name}"):
                    self.stats["total_moved"] += 1
                    print(f"  ✓ Moved duplicate: {dup_path.relative_to(PROJECT_ROOT)}")
    
    def generate_report(self):
        """Generate summary report"""
        report_path = PROJECT_ROOT / "Reports" / f"REDUNDANCY_CLEANUP_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report = f"""# Redundancy Cleanup Report
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **__pycache__ directories removed:** {self.stats['pycache_removed']}
- **_.pyc files removed:** {self.stats['pyc_removed']}
- **Duplicate files found:** {self.stats['duplicates_found']}
- **Redundant pattern files moved:** {self.stats['redundant_patterns']}
- **Total files moved to TrashDump:** {self.stats['total_moved']}

## Files Moved to TrashDump

"""
        if self.moved_files:
            for file_path, reason in self.moved_files:
                report += f"- `{file_path}` - {reason}\n"
        else:
            report += "*No files moved*\n"
        
        report += f"""
## Recommendations

1. Review files in TrashDump/ before permanent deletion
2. Empty __pycache__ directories regenerate automatically
3. Consider adding .gitignore for *.pyc and __pycache__/
4. Run this cleanup periodically to maintain project hygiene

---
*Generated by redundancy_detector.py*
"""
        
        report_path.write_text(report)
        print(f"\n📄 Report saved to: {report_path}")
        return report_path
    
    def run(self):
        """Run complete redundancy detection and cleanup"""
        print("="*70)
        print("SecIDS-CNN Redundancy Detector")
        print("="*70)
        
        # Find all redundant items
        self.find_pycache_dirs()
        self.find_pyc_files()
        self.find_redundant_patterns()
        self.find_duplicate_files()
        
        # Cleanup
        self.cleanup_pycache()
        self.cleanup_pyc_files()
        self.move_redundant_files()
        self.move_duplicate_files()
        
        # Generate report
        self.generate_report()
        
        # Summary
        print("\n" + "="*70)
        print("Cleanup Summary")
        print("="*70)
        print(f"__pycache__ directories: {self.stats['pycache_removed']} removed")
        print(f".pyc files: {self.stats['pyc_removed']} removed")
        print(f"Duplicate files: {self.stats['duplicates_found']} found")
        print(f"Redundant files: {self.stats['redundant_patterns']} moved")
        print(f"Total moved to TrashDump: {self.stats['total_moved']}")
        print("="*70)
        print("\n✅ Cleanup complete!")

if __name__ == "__main__":
    detector = RedundancyDetector()
    detector.run()

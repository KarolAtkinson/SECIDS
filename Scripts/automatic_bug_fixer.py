#!/usr/bin/env python3
"""
Automatic Bug Fixer for SECIDS-CNN
Fixes common import path issues and adds sys.path corrections
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

class BugFixer:
    """Automatic bug fixer for Python import issues"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fixes_applied = []
        
    def fix_import_paths(self, file_path: Path, missing_modules: List[str]) -> bool:
        """Add sys.path fixes for missing local modules"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if already has sys.path fix
            if 'sys.path.insert' in content or 'sys.path.append' in content:
                return False
            
            # Determine which path to add based on missing modules
            paths_to_add = set()
            
            for module in missing_modules:
                if module in ['unified_wrapper', 'secids_cnn', 'run_model', 'train_and_test', 'train_master_model']:
                    paths_to_add.add('SecIDS-CNN')
                elif module in ['whitelist_checker', 'blacklist_manager', 'capture_device_info']:
                    paths_to_add.add('Device_Profile/device_info')
                elif module in ['train_unified_model', 'unified_threat_model', 'threat_detector', 'data_analyzer']:
                    paths_to_add.add('Model_Tester/Code')
                elif module in ['wireshark_manager', 'command_library', 'deep_scan']:
                    paths_to_add.add('Tools')
                elif 'UI.terminal_ui' in module or module == 'terminal_ui':
                    paths_to_add.add('UI')
            
            if not paths_to_add:
                return False
            
            # Find the import section
            lines = content.split('\n')
            insert_index = 0
            
            # Find first import or after shebang/docstring
            in_docstring = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Skip shebang
                if i == 0 and stripped.startswith('#!'):
                    continue
                
                # Track docstrings
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_docstring = not in_docstring
                    if not in_docstring:
                        insert_index = i + 1
                    continue
                
                if in_docstring:
                    continue
                
                # Found first import
                if stripped.startswith('import ') or stripped.startswith('from '):
                    insert_index = i
                    break
            
            # Create path insertion code
            path_code = []
            path_code.append("# Auto-fix: Add project paths to sys.path")
            path_code.append("import sys")
            path_code.append("from pathlib import Path")
            path_code.append("PROJECT_ROOT = Path(__file__).parent.parent")
            
            for path_to_add in sorted(paths_to_add):
                path_code.append(f"sys.path.insert(0, str(PROJECT_ROOT / '{path_to_add}'))")
            
            path_code.append("")  # Empty line
            
            # Insert the code
            new_lines = lines[:insert_index] + path_code + lines[insert_index:]
            new_content = '\n'.join(new_lines)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.fixes_applied.append({
                'file': str(file_path),
                'type': 'import_path_fix',
                'paths_added': list(paths_to_add)
            })
            
            return True
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def analyze_and_fix(self, debug_report_path: Path):
        """Analyze debug report and fix issues"""
        import json
        
        print("=" * 70)
        print("AUTOMATIC BUG FIXER")
        print("=" * 70)
        print()
        
        # Load debug report
        with open(debug_report_path, 'r') as f:
            report = json.load(f)
        
        # Group errors by file
        errors_by_file = {}
        for error_type, error_list in report['errors'].items():
            for error in error_list:
                file_path = error['file']
                if file_path not in errors_by_file:
                    errors_by_file[file_path] = []
                errors_by_file[file_path].append(error)
        
        print(f"Found {len(errors_by_file)} files with errors")
        print()
        
        # Fix each file
        for file_path, errors in errors_by_file.items():
            print(f"Fixing: {Path(file_path).relative_to(self.project_root)}")
            
            # Extract missing modules
            missing_modules = []
            for error in errors:
                if 'import' in error['type'].lower() or 'Cannot import' in error['message']:
                    if error['text']:
                        missing_modules.append(error['text'])
            
            if missing_modules:
                if self.fix_import_paths(Path(file_path), missing_modules):
                    print(f"  ✓ Added import path fixes for: {', '.join(missing_modules)}")
                else:
                    print(f"  ⚠ Already has path fix or no fix needed")
            else:
                print(f"  ℹ No fixable import errors")
        
        print()
        print("=" * 70)
        print(f"FIXES APPLIED: {len(self.fixes_applied)}")
        print("=" * 70)
        
        for fix in self.fixes_applied:
            file_short = Path(fix['file']).relative_to(self.project_root)
            print(f"\n✓ {file_short}")
            print(f"  Paths added: {', '.join(fix['paths_added'])}")
        
        # Save fix report
        fix_report_path = self.project_root / 'Reports' / f'bug_fixes_applied_{Path(debug_report_path).stem}.json'
        with open(fix_report_path, 'w') as f:
            json.dump(self.fixes_applied, f, indent=2)
        
        print(f"\n📄 Fix report saved: {fix_report_path.name}")


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    
    # Find latest debug report
    reports_dir = project_root / 'Reports'
    debug_reports = sorted(reports_dir.glob('debug_scan_report_*.json'), reverse=True)
    
    if not debug_reports:
        print("Error: No debug reports found. Run comprehensive_debug_scan.py first.")
        return
    
    latest_report = debug_reports[0]
    print(f"Using debug report: {latest_report.name}\n")
    
    fixer = BugFixer(str(project_root))
    fixer.analyze_and_fix(latest_report)


if __name__ == "__main__":
    main()

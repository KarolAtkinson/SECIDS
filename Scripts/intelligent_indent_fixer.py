#!/usr/bin/env python3
"""
Intelligent Indentation Fixer
Fixes malformed except blocks while preserving correct indentation
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent

BROKEN_FILES = [
    'Scripts/optimize_system.py',
    'UI/terminal_ui_enhanced.py',
    'UI/terminal_ui_v2.py',
    'Tools/continuous_live_capture.py',
    'Tools/create_enhanced_dataset.py',
    'Tools/live_capture_and_assess.py',
    'Tools/system_checker.py',
    'Tools/threat_reviewer.py',
    'Tools/vm_scanner.py',
    'Tools/wireshark_manager.py',
    'SecIDS-CNN/run_model.py',
    'Auto_Update/task_scheduler.py'
]

def fix_file(filepath: Path):
    """Fix except blocks with wrong indentation"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    fixed_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is an except line
        if re.match(r'^(\s+)except\s+.*:\s*$', line):
            indent_match = re.match(r'^(\s+)', line)
            if indent_match:
                indent = indent_match.group(1)
                block_indent = indent + '    '
                
                # Add the except line
                new_lines.append(line)
                i += 1
                
                # Check next lines - they might be malformed
                if i < len(lines):
                    next_line = lines[i]
                    
                    # If next line starts at wrong indentation or is a comment without proper indent
                    if next_line.strip() and not next_line.startswith(block_indent):
                        # Add a proper pass statement
                        new_lines.append(block_indent + 'pass  # Skip on error\n')
                        fixed_count += 1
                        # Skip the malformed lines until we get to properly indented code
                        while i < len(lines) and lines[i].strip() and not lines[i].startswith(indent[:-4] if len(indent) > 4 else ''):
                            if not lines[i].startswith(block_indent):
                                i += 1
                            else:
                                break
                        continue
        
        new_lines.append(line)
        i += 1
    
    if fixed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"✅ Fixed {fixed_count} blocks in: {filepath.name}")
        return True
    else:
        print(f"ℹ️  No fixes needed: {filepath.name}")
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("  INTELLIGENT INDENTATION FIXER")
    print("=" * 70)
    
    fixed_files = 0
    for filepath_str in BROKEN_FILES:
        filepath = PROJECT_ROOT / filepath_str
        if filepath.exists():
            if fix_file(filepath):
                fixed_files += 1
    
    print("\n" + "=" * 70)
    print(f"  Fixed {fixed_files} files")
    print("=" * 70)

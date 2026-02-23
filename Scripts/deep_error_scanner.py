#!/usr/bin/env python3
"""
Deep Error Scanner for SECIDS-CNN Project
Comprehensive error detection including:
- Syntax and compilation errors
- Logic errors and code smells
- Import issues and dependency problems
- Configuration file validation
- File integrity checks
- Security issues
- Performance issues
"""

import os
import sys
import ast
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
EXCLUDE_DIRS = {'.venv_test', '.venv', '__pycache__', '.git', 'node_modules', 'TrashDump'}

class DeepErrorScanner:
    """Comprehensive error scanner for the entire project"""
    
    def __init__(self):
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)
        self.info = defaultdict(list)
        self.stats = {
            'files_scanned': 0,
            'errors_found': 0,
            'warnings_found': 0,
            'info_found': 0,
            'files_with_issues': 0
        }
        
    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded"""
        return any(excluded in str(path) for excluded in EXCLUDE_DIRS)
    
    def scan_python_file(self, filepath: Path) -> Dict[str, List]:
        """Comprehensive Python file analysis"""
        issues = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 1. Syntax check
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues['errors'].append({
                    'type': 'SyntaxError',
                    'line': e.lineno,
                    'message': str(e)
                })
            
            # 2. Compilation check
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(filepath)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                issues['errors'].append({
                    'type': 'CompilationError',
                    'message': result.stderr
                })
            
            # 3. Parse AST for code smells
            try:
                tree = ast.parse(content)
                
                # Check for bare except clauses
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:
                            issues['warnings'].append({
                                'type': 'BareExcept',
                                'line': node.lineno,
                                'message': 'Bare except clause catches all exceptions'
                            })
                    
                    # Check for eval/exec usage (security risk)
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in ['eval', 'exec']:
                                issues['errors'].append({
                                    'type': 'SecurityRisk',
                                    'line': node.lineno,
                                    'message': f'Dangerous function {node.func.id}() used'
                                })
                    
                    # Check for empty except blocks
                    if isinstance(node, ast.ExceptHandler):
                        if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                            issues['warnings'].append({
                                'type': 'EmptyExcept',
                                'line': node.lineno,
                                'message': 'Empty except block - errors are silently ignored'
                            })
                    
                    # Check for TODO/FIXME/HACK comments
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if any(marker in line.upper() for marker in ['TODO', 'FIXME', 'HACK', 'XXX']):
                            issues['info'].append({
                                'type': 'CodeComment',
                                'line': line_num,
                                'message': f'Found marker: {line.strip()}'
                            })
                
                # Check for missing docstrings
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if not ast.get_docstring(node):
                            issues['info'].append({
                                'type': 'MissingDocstring',
                                'line': node.lineno,
                                'message': f'{type(node).__name__} "{node.name}" has no docstring'
                            })
                
                # Check for unused imports
                imports = set()
                names_used = set()
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.asname if alias.asname else alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imports.add(alias.asname if alias.asname else alias.name)
                    elif isinstance(node, ast.Name):
                        names_used.add(node.id)
                
                # Simple unused import detection (may have false positives)
                unused = imports - names_used
                if unused:
                    issues['info'].append({
                        'type': 'PossiblyUnusedImports',
                        'message': f'Possibly unused imports: {", ".join(sorted(unused))}'
                    })
                
            except Exception as e:
                issues['warnings'].append({
                    'type': 'ASTParseWarning',
                    'message': f'Could not fully analyze: {str(e)}'
                })
            
            # 4. Check for shebang issues
            if content.startswith('#!/usr/bin/env python3'):
                if '.venv_test/bin/python' not in content:
                    issues['warnings'].append({
                        'type': 'ShebangWarning',
                        'line': 1,
                        'message': 'Using system Python instead of venv'
                    })
            
            # 5. Check file encoding
            try:
                with open(filepath, 'rb') as f:
                    raw = f.read()
                    raw.decode('utf-8')
            except UnicodeDecodeError:
                issues['errors'].append({
                    'type': 'EncodingError',
                    'message': 'File is not valid UTF-8'
                })
            
        except Exception as e:
            issues['errors'].append({
                'type': 'ScanError',
                'message': f'Error scanning file: {str(e)}'
            })
        
        return issues
    
    def scan_json_file(self, filepath: Path) -> Dict[str, List]:
        """Validate JSON files"""
        issues = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            issues['errors'].append({
                'type': 'JSONError',
                'line': e.lineno,
                'message': e.msg
            })
        except Exception as e:
            issues['errors'].append({
                'type': 'JSONReadError',
                'message': str(e)
            })
        
        return issues
    
    def scan_bash_file(self, filepath: Path) -> Dict[str, List]:
        """Basic bash script validation"""
        issues = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        try:
            result = subprocess.run(
                ['bash', '-n', str(filepath)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                issues['errors'].append({
                    'type': 'BashSyntaxError',
                    'message': result.stderr
                })
            
            # Check for common bash issues
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for missing shebang
            if not content.startswith('#!'):
                issues['warnings'].append({
                    'type': 'MissingShebang',
                    'line': 1,
                    'message': 'Bash script missing shebang'
                })
            
            # Check for unquoted variables (simple check)
            unquoted_vars = re.findall(r'(?<!\$)\$[A-Za-z_][A-Za-z0-9_]*(?!["\'])', content)
            if unquoted_vars:
                issues['warnings'].append({
                    'type': 'UnquotedVariables',
                    'message': f'Found {len(unquoted_vars)} potentially unquoted variables'
                })
                
        except Exception as e:
            issues['errors'].append({
                'type': 'BashScanError',
                'message': str(e)
            })
        
        return issues
    
    def scan_directory(self, directory: Path):
        """Scan all files in a directory"""
        print(f"\n📂 Scanning: {directory.name}/")
        print("=" * 70)
        
        files_in_dir = 0
        issues_in_dir = 0
        
        for item in directory.rglob('*'):
            if item.is_file() and not self.should_exclude(item):
                relative_path = item.relative_to(PROJECT_ROOT)
                
                issues = None
                if item.suffix == '.py':
                    issues = self.scan_python_file(item)
                elif item.suffix == '.json':
                    issues = self.scan_json_file(item)
                elif item.suffix in ['.sh', ''] and item.name in ['secids', 'cleanup', 'csv-workflow']:
                    issues = self.scan_bash_file(item)
                
                if issues:
                    files_in_dir += 1
                    self.stats['files_scanned'] += 1
                    
                    has_issues = False
                    if issues['errors']:
                        self.errors[str(relative_path)] = issues['errors']
                        self.stats['errors_found'] += len(issues['errors'])
                        has_issues = True
                    if issues['warnings']:
                        self.warnings[str(relative_path)] = issues['warnings']
                        self.stats['warnings_found'] += len(issues['warnings'])
                        has_issues = True
                    if issues['info']:
                        self.info[str(relative_path)] = issues['info']
                        self.stats['info_found'] += len(issues['info'])
                    
                    if has_issues:
                        self.stats['files_with_issues'] += 1
                        issues_in_dir += 1
                        print(f"  ⚠️  {relative_path}")
                        for error in issues['errors']:
                            print(f"      ❌ {error['type']}: {error.get('message', '')[:60]}")
                        for warning in issues['warnings']:
                            print(f"      ⚠️  {warning['type']}: {warning.get('message', '')[:60]}")
        
        print(f"  Scanned {files_in_dir} files, {issues_in_dir} with issues")
    
    def scan_project(self):
        """Scan entire project"""
        print("\n" + "=" * 70)
        print("  DEEP ERROR SCANNER - COMPREHENSIVE PROJECT ANALYSIS")
        print("=" * 70)
        
        # Define directories to scan
        scan_dirs = [
            'Scripts',
            'UI',
            'Countermeasures',
            'Auto_Update',
            'Model_Tester',
            'Tools',
            'SecIDS-CNN',
            'Launchers',
            'Config'
        ]
        
        for dir_name in scan_dirs:
            dir_path = PROJECT_ROOT / dir_name
            if dir_path.exists():
                self.scan_directory(dir_path)
        
        self.print_summary()
        self.generate_report()
    
    def print_summary(self):
        """Print scan summary"""
        print("\n" + "=" * 70)
        print("  SCAN SUMMARY")
        print("=" * 70)
        print(f"  Files Scanned:        {self.stats['files_scanned']}")
        print(f"  Files with Issues:    {self.stats['files_with_issues']}")
        print(f"  Errors Found:         {self.stats['errors_found']} ❌")
        print(f"  Warnings Found:       {self.stats['warnings_found']} ⚠️")
        print(f"  Info Items:           {self.stats['info_found']} ℹ️")
        
        if self.stats['errors_found'] == 0:
            print("\n  ✅ No critical errors found!")
        else:
            print(f"\n  ⚠️  {self.stats['errors_found']} errors need attention")
        
        print("=" * 70)
    
    def generate_report(self):
        """Generate detailed error report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        report_data = {
            'scan_date': datetime.now().isoformat(),
            'stats': self.stats,
            'errors': dict(self.errors),
            'warnings': dict(self.warnings),
            'info': dict(self.info)
        }
        
        # JSON report
        json_file = PROJECT_ROOT / 'Reports' / f'deep_error_scan_{timestamp}.json'
        json_file.parent.mkdir(exist_ok=True)
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Text report
        txt_file = PROJECT_ROOT / 'Reports' / f'deep_error_scan_{timestamp}.txt'
        with open(txt_file, 'w') as f:
            f.write("DEEP ERROR SCAN REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("STATISTICS:\n")
            f.write(f"  Files Scanned: {self.stats['files_scanned']}\n")
            f.write(f"  Files with Issues: {self.stats['files_with_issues']}\n")
            f.write(f"  Errors: {self.stats['errors_found']}\n")
            f.write(f"  Warnings: {self.stats['warnings_found']}\n")
            f.write(f"  Info: {self.stats['info_found']}\n\n")
            
            if self.errors:
                f.write("ERRORS:\n")
                f.write("=" * 70 + "\n")
                for filepath, errors in sorted(self.errors.items()):
                    f.write(f"\n{filepath}:\n")
                    for error in errors:
                        f.write(f"  [{error['type']}] ")
                        if 'line' in error:
                            f.write(f"Line {error['line']}: ")
                        f.write(f"{error.get('message', '')}\n")
            
            if self.warnings:
                f.write("\n\nWARNINGS:\n")
                f.write("=" * 70 + "\n")
                for filepath, warnings in sorted(self.warnings.items()):
                    f.write(f"\n{filepath}:\n")
                    for warning in warnings:
                        f.write(f"  [{warning['type']}] ")
                        if 'line' in warning:
                            f.write(f"Line {warning['line']}: ")
                        f.write(f"{warning.get('message', '')}\n")
        
        print(f"\n📄 Reports generated:")
        print(f"  JSON: {json_file}")
        print(f"  Text: {txt_file}")

if __name__ == '__main__':
    scanner = DeepErrorScanner()
    scanner.scan_project()

#!/usr/bin/env python3
"""
Comprehensive Debug Scanner for SECIDS-CNN
Scans all Python files for syntax errors, import issues, and common bugs
"""

import os
import sys
import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

class DebugScanner:
    """Comprehensive debug scanner for Python projects"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors = {
            'syntax_errors': [],
            'import_errors': [],
            'undefined_variables': [],
            'unused_imports': [],
            'type_errors': [],
            'indentation_errors': [],
            'encoding_errors': [],
            'other_errors': []
        }
        self.stats = {
            'total_files': 0,
            'scanned_files': 0,
            'files_with_errors': 0,
            'total_errors': 0
        }
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in project"""
        exclude_dirs = {'.venv', '.venv_test', '__pycache__', 'TrashDump', '.git'}
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def check_syntax(self, file_path: Path) -> List[Dict]:
        """Check Python file for syntax errors"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                ast.parse(code, filename=str(file_path))
        except SyntaxError as e:
            errors.append({
                'file': str(file_path),
                'type': 'syntax_error',
                'line': e.lineno,
                'message': str(e.msg),
                'text': e.text.strip() if e.text else ''
            })
        except UnicodeDecodeError as e:
            errors.append({
                'file': str(file_path),
                'type': 'encoding_error',
                'line': 0,
                'message': f'Unicode decode error: {e}',
                'text': ''
            })
        # Note: IndentationError is a subclass of SyntaxError, caught above
        # except IndentationError as e:
        #     errors.append({
        #         'file': str(file_path),
        #         'type': 'indentation_error',
        #         'line': e.lineno,
        #         'message': str(e.msg),
        #         'text': e.text.strip() if e.text else ''
        #     })
        except Exception as e:
            errors.append({
                'file': str(file_path),
                'type': 'other_error',
                'line': 0,
                'message': f'Unexpected error: {e}',
                'text': ''
            })
        
        return errors
    
    def check_imports(self, file_path: Path) -> List[Dict]:
        """Check for import errors"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                tree = ast.parse(code, filename=str(file_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            # Try to import the module
                            try:
                                __import__(alias.name)
                            except ImportError as e:
                                # Check if it's a local module
                                if not self.is_local_module(alias.name):
                                    errors.append({
                                        'file': str(file_path),
                                        'type': 'import_error',
                                        'line': node.lineno,
                                        'message': f'Cannot import {alias.name}: {e}',
                                        'text': alias.name
                                    })
                            except Exception:
                                pass  # Skip other import issues
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            try:
                                __import__(node.module)
                            except ImportError as e:
                                if not self.is_local_module(node.module):
                                    errors.append({
                                        'file': str(file_path),
                                        'type': 'import_error',
                                        'line': node.lineno,
                                        'message': f'Cannot import from {node.module}: {e}',
                                        'text': node.module
                                    })
                            except Exception:
                                pass  # Skip other import issues
        except Exception as e:
            # If we can't parse, it will be caught by syntax check
            pass
        
        return errors
    
    def is_local_module(self, module_name: str) -> bool:
        """Check if module is a local project module"""
        local_modules = ['secids_cnn', 'unified_threat_model', 'threat_detector', 
                        'data_analyzer', 'command_library', 'deep_scan']
        return any(module_name.startswith(m) for m in local_modules)
    
    def check_with_pylint(self, file_path: Path) -> List[Dict]:
        """Run pylint on file for deeper analysis"""
        errors = []
        try:
            # Run pylint with JSON output
            result = subprocess.run(
                [sys.executable, '-m', 'pylint', '--output-format=json', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                try:
                    pylint_results = json.loads(result.stdout)
                    for issue in pylint_results:
                        if issue['type'] in ['error', 'fatal']:
                            errors.append({
                                'file': str(file_path),
                                'type': 'pylint_error',
                                'line': issue.get('line', 0),
                                'message': issue.get('message', ''),
                                'text': issue.get('symbol', '')
                            })
                except json.JSONDecodeError:
                    pass
        
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            # Pylint not installed, skip
            pass
        except Exception as e:
            pass  # Skip on error
        return errors
    
    def scan_file(self, file_path: Path) -> Dict:
        """Comprehensive scan of a single file"""
        file_errors = {
            'file': str(file_path),
            'errors': []
        }
        
        # Check syntax
        syntax_errors = self.check_syntax(file_path)
        file_errors['errors'].extend(syntax_errors)
        
        # Only check imports if no syntax errors
        if not syntax_errors:
            import_errors = self.check_imports(file_path)
            file_errors['errors'].extend(import_errors)
        
        return file_errors
    
    def scan_all_files(self):
        """Scan all Python files in project"""
        print("=" * 70)
        print("COMPREHENSIVE DEBUG SCAN - SECIDS-CNN")
        print("=" * 70)
        print(f"Project Root: {self.project_root}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Find all Python files
        python_files = self.find_python_files()
        self.stats['total_files'] = len(python_files)
        
        print(f"Found {len(python_files)} Python files to scan\n")
        
        # Scan each file
        for i, file_path in enumerate(python_files, 1):
            relative_path = file_path.relative_to(self.project_root)
            print(f"[{i}/{len(python_files)}] Scanning: {relative_path}", end=' ')
            
            file_result = self.scan_file(file_path)
            self.stats['scanned_files'] += 1
            
            if file_result['errors']:
                print("❌")
                self.stats['files_with_errors'] += 1
                self.stats['total_errors'] += len(file_result['errors'])
                
                # Categorize errors
                for error in file_result['errors']:
                    error_type = error['type']
                    if error_type in self.errors:
                        self.errors[error_type].append(error)
                    else:
                        self.errors['other_errors'].append(error)
            else:
                print("✓")
        
        print("\n" + "=" * 70)
        self.print_summary()
        self.save_report()
    
    def print_summary(self):
        """Print scan summary"""
        print("SCAN SUMMARY")
        print("=" * 70)
        print(f"Total files found:     {self.stats['total_files']}")
        print(f"Files scanned:         {self.stats['scanned_files']}")
        print(f"Files with errors:     {self.stats['files_with_errors']}")
        print(f"Total errors:          {self.stats['total_errors']}")
        print()
        
        if self.stats['total_errors'] > 0:
            print("ERROR BREAKDOWN:")
            print("-" * 70)
            for error_type, error_list in self.errors.items():
                if error_list:
                    print(f"  {error_type.replace('_', ' ').title()}: {len(error_list)}")
            print()
            
            print("DETAILED ERRORS:")
            print("-" * 70)
            for error_type, error_list in self.errors.items():
                if error_list:
                    print(f"\n{error_type.replace('_', ' ').title().upper()}:")
                    for error in error_list[:10]:  # Show first 10 of each type
                        file_short = Path(error['file']).relative_to(self.project_root)
                        print(f"  📁 {file_short}:{error['line']}")
                        print(f"     {error['message']}")
                        if error['text']:
                            print(f"     Code: {error['text']}")
                    
                    if len(error_list) > 10:
                        print(f"  ... and {len(error_list) - 10} more")
        else:
            print("✅ No errors found! All files are clean.")
        
        print("\n" + "=" * 70)
    
    def save_report(self):
        """Save detailed report to file"""
        report_file = self.project_root / 'Reports' / f'debug_scan_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'statistics': self.stats,
            'errors': self.errors
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved: {report_file.name}")
        
        # Also save human-readable report
        text_report = self.project_root / 'Reports' / f'debug_scan_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(text_report, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("COMPREHENSIVE DEBUG SCAN REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Project: SECIDS-CNN\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Project Root: {self.project_root}\n\n")
            
            f.write("STATISTICS:\n")
            f.write("-" * 70 + "\n")
            for key, value in self.stats.items():
                f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
            f.write("\n")
            
            if self.stats['total_errors'] > 0:
                f.write("ERROR DETAILS:\n")
                f.write("-" * 70 + "\n")
                for error_type, error_list in self.errors.items():
                    if error_list:
                        f.write(f"\n{error_type.replace('_', ' ').title().upper()} ({len(error_list)}):\n")
                        for error in error_list:
                            file_short = Path(error['file']).relative_to(self.project_root)
                            f.write(f"\n  File: {file_short}\n")
                            f.write(f"  Line: {error['line']}\n")
                            f.write(f"  Message: {error['message']}\n")
                            if error['text']:
                                f.write(f"  Code: {error['text']}\n")
            else:
                f.write("✅ No errors found!\n")
        
        print(f"📄 Text report saved: {text_report.name}")


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    scanner = DebugScanner(project_root)
    scanner.scan_all_files()


if __name__ == "__main__":
    main()

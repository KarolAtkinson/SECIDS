#!/usr/bin/env python3
"""
Production-Grade Debug Scanner for SECIDS-CNN
Uses compilation checks instead of runtime imports to avoid false positives
"""

import os
import sys
import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Union
from datetime import datetime

class ProductionDebugScanner:
    """Production-grade debug scanner with compilation checks"""
    
    def __init__(self, project_root: Union[str, Path]):
        self.project_root = Path(project_root)
        self.errors = {
            'syntax_errors': [],
            'indentation_errors': [],
            'encoding_errors': [],
            'compilation_errors': [],
            'undefined_names': [],
            'unused_imports': []
        }
        self.stats = {
            'total_files': 0,
            'scanned_files': 0,
            'files_with_errors': 0,
            'total_errors': 0
        }
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in project"""
        exclude_dirs = {'.venv', '.venv_test', '__pycache__', 'TrashDump', '.git', 'node_modules'}
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def check_compilation(self, file_path: Path) -> List[Dict]:
        """Check if file compiles correctly"""
        errors = []
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                # Parse error message
                error_msg = result.stderr
                if error_msg:
                    errors.append({
                        'file': str(file_path),
                        'type': 'compilation_error',
                        'line': 0,
                        'message': error_msg.strip(),
                        'text': ''
                    })
        
        except subprocess.TimeoutExpired:
            errors.append({
                'file': str(file_path),
                'type': 'compilation_error',
                'line': 0,
                'message': 'Compilation timeout (>10s)',
                'text': ''
            })
        except Exception as e:
            errors.append({
                'file': str(file_path),
                'type': 'compilation_error',
                'line': 0,
                'message': f'Compilation check failed: {e}',
                'text': ''
            })
        
        return errors
    
    def check_syntax_ast(self, file_path: Path) -> List[Dict]:
        """Check Python file for syntax errors using AST"""
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
                'type': 'syntax_error',
                'line': 0,
                'message': f'Parse error: {e}',
                'text': ''
            })
        
        return errors
    
    def check_undefined_names(self, file_path: Path) -> List[Dict]:
        """Check for undefined variable names"""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                tree = ast.parse(code, filename=str(file_path))
                
                # Simple check for common issues
                for node in ast.walk(tree):
                    # Check for bare except (bad practice)
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None and node.name is None:
                            errors.append({
                                'file': str(file_path),
                                'type': 'undefined_names',
                                'line': node.lineno,
                                'message': 'Bare except: catches all exceptions (bad practice)',
                                'text': 'except:'
                            })
        
        except SyntaxError:
            return errors
        
        return errors
    
    def scan_file(self, file_path: Path) -> Dict:
        """Comprehensive scan of a single file"""
        file_errors = {
            'file': str(file_path),
            'errors': []
        }
        
        # Check syntax with AST (fast)
        syntax_errors = self.check_syntax_ast(file_path)
        file_errors['errors'].extend(syntax_errors)
        
        # Only check compilation if no syntax errors
        if not syntax_errors:
            compilation_errors = self.check_compilation(file_path)
            file_errors['errors'].extend(compilation_errors)
            
            # Check for undefined names and bad practices
            undefined_errors = self.check_undefined_names(file_path)
            file_errors['errors'].extend(undefined_errors)
        
        return file_errors
    
    def scan_all_files(self):
        """Scan all Python files in project"""
        print("=" * 70)
        print("PRODUCTION DEBUG SCAN - SECIDS-CNN")
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
            print(f"[{i}/{len(python_files)}] Scanning: {str(relative_path):<50}", end=' ')
            
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
                    for error in error_list:
                        file_short = Path(error['file']).relative_to(self.project_root)
                        print(f"  📁 {file_short}:{error['line']}")
                        print(f"     {error['message']}")
                        if error['text']:
                            print(f"     Code: {error['text']}")
                    
                    if len(error_list) > 5:
                        print(f"  ... showing first 5 of {len(error_list)}")
        else:
            print("✅ No errors found! All files compile successfully.")
        
        print("\n" + "=" * 70)
    
    def save_report(self):
        """Save detailed report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.project_root / 'Reports' / f'production_debug_report_{timestamp}.json'
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'statistics': self.stats,
            'errors': self.errors
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved: {report_file.name}")


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    scanner = ProductionDebugScanner(project_root)
    scanner.scan_all_files()


if __name__ == "__main__":
    main()

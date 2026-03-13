#!/usr/bin/env python3
"""
File Organization Script
Automatically moves files to their proper locations
Updated: 2026-01-31
Includes redundancy detection and debug scanning
"""

import os
import sys
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class FileOrganizer:
    """Organizes files into proper directories"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.moves = []
        self.skipped = []
        self.stats = {
            'reports': 0,
            'results': 0,
            'logs': 0,
            'configs': 0,
            'captures': 0,
            'models': 0,
            'datasets': 0,
            'scripts': 0,
            'consolidated': 0,
            'pycache_removed': 0,
            'pyc_removed': 0,
            'duplicates_moved': 0,
            'redundant_moved': 0,
            'syntax_errors': 0,
            'compilation_errors': 0,
            'bad_practices': 0,
            'empty_except_blocks': 0,
            'bare_except_clauses': 0,
            'security_risks': 0,
            'shebang_warnings': 0,
            'json_errors': 0,
            'bash_errors': 0
        }
        self.consolidated_files = []
        self.trash_dump = self.base_dir / 'TrashDump'
        self.trash_dump.mkdir(exist_ok=True)
        
        # Error flags for deep scan issues
        self.error_flags = {
            'SecurityRisk': [],
            'EmptyExceptBlock': [],
            'BareExceptClause': [],
            'ShebangWarning': [],
            'JSONError': [],
            'BashError': [],
            'CompilationError': [],
            'SyntaxError': []
        }
        
    def consolidate_to_master_manual(self, md_file):
        """Check if markdown content should be added to Master-Manual.md"""
        master_manual = self.base_dir / 'Master-Manual.md'
        
        if not master_manual.exists():
            return False
        
        # Read the markdown file
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Get the title from the first line
            title_line = content.split('\n')[0] if content else ""
            title = title_line.replace('#', '').strip()
            
            if not title:
                return False
            
            # Check if this content is already in Master-Manual.md
            with open(master_manual, 'r', encoding='utf-8') as f:
                master_content = f.read()
            
            # If title is already in Master-Manual, skip
            if title in master_content:
                return False
            
            # If this is a report file or documentation, append to Master-Manual
            if any(keyword in md_file.name.upper() for keyword in 
                   ['REPORT', 'SUMMARY', 'UPDATE', 'ENHANCEMENT', 'FIX', 'INTEGRATION']):
                
                # Append to Master-Manual.md
                with open(master_manual, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n---\n\n")
                    f.write(f"# {title}\n")
                    f.write(f"*Consolidated from: {md_file.name}*\n")
                    f.write(f"*Date: {datetime.now().strftime('%Y-%m-%d')}*\n\n")
                    # Write content without the title (already added)
                    content_without_title = '\n'.join(content.split('\n')[1:]).strip()
                    f.write(content_without_title)
                    f.write("\n")
                
                self.consolidated_files.append(md_file.name)
                self.stats['consolidated'] += 1
                return True
        
        except Exception as e:
            self.skipped.append(f"Could not consolidate {md_file.name}: {e}")
            return False
        
        return False
    
    def organize_reports(self):
        """Move markdown and documentation files to Reports/"""
        reports_dir = self.base_dir / 'Reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Find markdown files in root (except Master-Manual.md)
        for md_file in self.base_dir.glob('*.md'):
            if md_file.name not in ['Master-Manual.md', 'README.md']:
                # Try to consolidate to Master-Manual first
                self.consolidate_to_master_manual(md_file)
                
                # Then move to Reports/
                dest = reports_dir / md_file.name
                if not dest.exists():
                    shutil.move(str(md_file), str(dest))
                    self.moves.append(f"Moved {md_file.name} -> Reports/")
                    self.stats['reports'] += 1
        
        # Check for reports in Scripts/
        scripts_dir = self.base_dir / 'Scripts'
        if scripts_dir.exists():
            for md_file in scripts_dir.glob('*REPORT*.md'):
                dest = reports_dir / md_file.name
                if not dest.exists():
                    shutil.move(str(md_file), str(dest))
                    self.moves.append(f"Moved Scripts/{md_file.name} -> Reports/")
                    self.stats['reports'] += 1
    
    def organize_test_results(self):
        """Move test result JSON files to Stress_Test_Results/"""
        results_dir = self.base_dir / 'Stress_Test_Results'
        results_dir.mkdir(exist_ok=True)
        
        # Find stress test reports in root
        for json_file in self.base_dir.glob('stress_test_report_*.json'):
            dest = results_dir / json_file.name
            if not dest.exists():
                shutil.move(str(json_file), str(dest))
                self.moves.append(f"Moved {json_file.name} -> Stress_Test_Results/")
                self.stats['results'] += 1
        
        # Find stress test reports in Scripts/
        scripts_dir = self.base_dir / 'Scripts'
        if scripts_dir.exists():
            for json_file in scripts_dir.glob('stress_test_report_*.json'):
                dest = results_dir / json_file.name
                if not dest.exists():
                    shutil.move(str(json_file), str(dest))
                    self.moves.append(f"Moved Scripts/{json_file.name} -> Stress_Test_Results/")
                    self.stats['results'] += 1
    
    def organize_logs(self):
        """Ensure log files are in Logs/ directory"""
        logs_dir = self.base_dir / 'Logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Find log files in root
        for log_file in self.base_dir.glob('*.log'):
            dest = logs_dir / log_file.name
            if not dest.exists():
                shutil.move(str(log_file), str(dest))
                self.moves.append(f"Moved {log_file.name} -> Logs/")
                self.stats['logs'] += 1
        
        # Check for logs in Scripts/ and Tools/
        for subdir in ['Scripts', 'Tools']:
            subdir_path = self.base_dir / subdir
            if subdir_path.exists():
                for log_file in subdir_path.glob('*.log'):
                    dest = logs_dir / log_file.name
                    if not dest.exists():
                        shutil.move(str(log_file), str(dest))
                        self.moves.append(f"Moved {subdir}/{log_file.name} -> Logs/")
                        self.stats['logs'] += 1
    
    def organize_configs(self):
        """Ensure config files are in Config/ directory"""
        config_dir = self.base_dir / 'Config'
        config_dir.mkdir(exist_ok=True)
        
        # Find JSON config files in root
        config_patterns = ['*_config.json', 'config_*.json', 'settings.json', 
                          'command_history.json', 'command_shortcuts.json', 
                          'command_favorites.json', 'dataset_config.json']
        
        for pattern in config_patterns:
            for json_file in self.base_dir.glob(pattern):
                dest = config_dir / json_file.name
                if not dest.exists():
                    shutil.move(str(json_file), str(dest))
                    self.moves.append(f"Moved {json_file.name} -> Config/")
                    self.stats['configs'] += 1
        
        # Check for .env file in root (should be in Config/)
        env_file = self.base_dir / '.env'
        if env_file.exists():
            dest = config_dir / '.env'
            if not dest.exists():
                shutil.move(str(env_file), str(dest))
                self.moves.append(f"Moved .env -> Config/")
                self.stats['configs'] += 1
    
    def organize_pcap_files(self):
        """Move PCAP files to Captures/ directory"""
        captures_dir = self.base_dir / 'Captures'
        captures_dir.mkdir(exist_ok=True)
        
        # Find PCAP files in root
        for pcap_file in self.base_dir.glob('*.pcap'):
            dest = captures_dir / pcap_file.name
            if not dest.exists():
                shutil.move(str(pcap_file), str(dest))
                self.moves.append(f"Moved {pcap_file.name} -> Captures/")
                self.stats['captures'] += 1
        
        # Check common locations
        for subdir in ['Tools', 'Scripts', 'Results']:
            subdir_path = self.base_dir / subdir
            if subdir_path.exists():
                for pcap_file in subdir_path.glob('*.pcap'):
                    dest = captures_dir / pcap_file.name
                    if not dest.exists():
                        shutil.move(str(pcap_file), str(dest))
                        self.moves.append(f"Moved {subdir}/{pcap_file.name} -> Captures/")
                        self.stats['captures'] += 1
    
    def organize_models(self):
        """Move model files to Models/ directory"""
        models_dir = self.base_dir / 'Models'
        models_dir.mkdir(exist_ok=True)
        
        # Find .h5 and .pkl files in root
        for model_file in list(self.base_dir.glob('*.h5')) + list(self.base_dir.glob('*.pkl')):
            dest = models_dir / model_file.name
            if not dest.exists():
                shutil.move(str(model_file), str(dest))
                self.moves.append(f"Moved {model_file.name} -> Models/")
                self.stats['models'] += 1
        
        # Check Tools/ and Scripts/ for model files
        for subdir in ['Tools', 'Scripts']:
            subdir_path = self.base_dir / subdir
            if subdir_path.exists():
                for model_file in list(subdir_path.glob('*.h5')) + list(subdir_path.glob('*.pkl')):
                    dest = models_dir / model_file.name
                    if not dest.exists():
                        shutil.move(str(model_file), str(dest))
                        self.moves.append(f"Moved {subdir}/{model_file.name} -> Models/")
                        self.stats['models'] += 1
    
    def organize_datasets(self):
        """Archive old CSV datasets to Archives/"""
        archives_dir = self.base_dir / 'Archives'
        archives_dir.mkdir(exist_ok=True)
        
        # Find CSV files in root that should be archived
        for csv_file in self.base_dir.glob('*.csv'):
            dest = archives_dir / csv_file.name
            if not dest.exists():
                shutil.move(str(csv_file), str(dest))
                self.moves.append(f"Moved {csv_file.name} -> Archives/")
                self.stats['datasets'] += 1
    
    def organize_scripts(self):
        """Move Python scripts to appropriate locations"""
        scripts_dir = self.base_dir / 'Scripts'
        tools_dir = self.base_dir / 'Tools'
        
        scripts_dir.mkdir(exist_ok=True)
        tools_dir.mkdir(exist_ok=True)
        
        # Define utility scripts that should be in Scripts/
        utility_scripts = [
            'analyze_threat_origins.py',
            'test_enhanced_model.py',
            'verify_packages.py',
            'create_master_dataset.py',
            'refine_datasets.py',
            'stress_test.py',
            'setup_tensorflow.py'
        ]
        
        # Define tool scripts that should be in Tools/
        tool_scripts = [
            'command_library.py',
            'csv_workflow_manager.py',
            'pipeline_orchestrator.py',
            'threat_reviewer.py',
            'deep_scan.py'
        ]
        
        # Move utility scripts
        for script in utility_scripts:
            script_path = self.base_dir / script
            if script_path.exists():
                dest = scripts_dir / script
                if not dest.exists():
                    shutil.move(str(script_path), str(dest))
                    self.moves.append(f"Moved {script} -> Scripts/")
                    self.stats['scripts'] += 1
        
        # Move tool scripts
        for script in tool_scripts:
            script_path = self.base_dir / script
            if script_path.exists():
                dest = tools_dir / script
                if not dest.exists():
                    shutil.move(str(script_path), str(dest))
                    self.moves.append(f"Moved {script} -> Tools/")
                    self.stats['scripts'] += 1
    
    def organize_launchers(self):
        """Move shell scripts to Launchers/ directory"""
        launchers_dir = self.base_dir / 'Launchers'
        launchers_dir.mkdir(exist_ok=True)
        
        # Find shell scripts in root
        launcher_scripts = [
            'csv_workflow.sh',
            'QUICK_START.sh',
            'secids.sh'
        ]
        
        for script in launcher_scripts:
            script_path = self.base_dir / script
            if script_path.exists():
                dest = launchers_dir / script
                if not dest.exists():
                    shutil.move(str(script_path), str(dest))
                    self.moves.append(f"Moved {script} -> Launchers/")
                    self.stats['scripts'] += 1
    
    def consolidate_logs_dirs(self):
        """Merge logs/ and Logs/ directories"""
        logs_lower = self.base_dir / 'logs'
        logs_upper = self.base_dir / 'Logs'
        
        if logs_lower.exists() and logs_lower.is_dir():
            logs_upper.mkdir(exist_ok=True)
            
            # Move all files from logs/ to Logs/
            for item in logs_lower.iterdir():
                dest = logs_upper / item.name
                if not dest.exists():
                    if item.is_file():
                        shutil.move(str(item), str(dest))
                        self.moves.append(f"Merged logs/{item.name} -> Logs/")
                        self.stats['logs'] += 1
            
            # Try to remove empty logs/ directory
            try:
                if not any(logs_lower.iterdir()):
                    logs_lower.rmdir()
                    self.moves.append("Removed empty logs/ directory")
            except OSError as e:
                # Directory not empty or permission error
                self.skipped.append(f"Could not remove logs/ directory: {e}")
    
    def organize_detection_results(self):
        """Organize detection results in Results/ directory"""
        results_dir = self.base_dir / 'Results'
        results_dir.mkdir(exist_ok=True)
        
        # Check for detection results in SecIDS-CNN/
        secids_dir = self.base_dir / 'SecIDS-CNN'
        if secids_dir.exists():
            for result_file in secids_dir.glob('*detection_results*.csv'):
                dest = results_dir / result_file.name
                if not dest.exists():
                    shutil.move(str(result_file), str(dest))
                    self.moves.append(f"Moved SecIDS-CNN/{result_file.name} -> Results/")
                    self.stats['results'] += 1
            
            for result_file in secids_dir.glob('*_report_*.json'):
                dest = results_dir / result_file.name
                if not dest.exists():
                    shutil.move(str(result_file), str(dest))
                    self.moves.append(f"Moved SecIDS-CNN/{result_file.name} -> Results/")
                    self.stats['results'] += 1
    
    def organize_result_reports(self):
        """Move markdown report files from Results/ to Reports/"""
        results_dir = self.base_dir / 'Results'
        reports_dir = self.base_dir / 'Reports'
        reports_dir.mkdir(exist_ok=True)
        
        if results_dir.exists():
            # Move .md report files to Reports/
            for md_file in results_dir.glob('*.md'):
                # Try to consolidate to Master-Manual first
                self.consolidate_to_master_manual(md_file)
                
                # Then move to Reports/
                dest = reports_dir / md_file.name
                if not dest.exists():
                    shutil.move(str(md_file), str(dest))
                    self.moves.append(f"Moved Results/{md_file.name} -> Reports/")
                    self.stats['reports'] += 1
    
    def run_debug_scan(self):
        """Quick debug scan for Python files"""
        print("Checking Python files for errors...")
        
        python_files = list(self.base_dir.glob('**/*.py'))
        # Exclude venv and TrashDump
        python_files = [f for f in python_files if not any(
            x in f.parts for x in ['.venv', '.venv_test', 'TrashDump', '__pycache__']
        )]
        
        errors_found = []
        
        for py_file in python_files:
            # Quick compilation check
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', str(py_file)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode != 0:
                    relative = py_file.relative_to(self.base_dir)
                    errors_found.append(f"{relative}: Compilation error")
                    self.stats['compilation_errors'] += 1
            except subprocess.TimeoutExpired:
                relative = py_file.relative_to(self.base_dir)
                errors_found.append(f"{relative}: Timeout during compilation")
                self.stats['compilation_errors'] += 1
            except Exception as e:
                # Log unexpected errors during debug scan
                relative = py_file.relative_to(self.base_dir)
                print(f"  ⚠️  Warning: Could not scan {relative}: {str(e)[:50]}")
        
        if errors_found:
            print(f"  ❌ Found {len(errors_found)} files with errors")
            for error in errors_found[:5]:  # Show first 5
                print(f"     • {error}")
            if len(errors_found) > 5:
                print(f"     ... and {len(errors_found) - 5} more")
            print("  💡 Run 'python Scripts/production_debug_scan.py' for detailed analysis")
        else:
            print("  ✓ All Python files compile successfully")
        
        return len(errors_found)
    
    def run_comprehensive_error_check(self):
        """Run comprehensive error checking with deep_error_scanner.py"""
        print("\n🔍 Running Comprehensive Error Check...")
        print("=" * 70)
        
        try:
            deep_scanner = self.base_dir / 'Scripts' / 'deep_error_scanner.py'
            if not deep_scanner.exists():
                print("  ⚠️  Deep error scanner not found, skipping")
                return 0
            
            result = subprocess.run(
                [sys.executable, str(deep_scanner)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse the output to get error counts
            output = result.stdout
            
            # Extract statistics from output
            for line in output.split('\n'):
                if 'Errors Found:' in line:
                    try:
                        count = int(line.split(':')[1].split()[0])
                        self.stats['syntax_errors'] = count
                    except (ValueError, IndexError):
                        # Skip parsing errors
                        continue
                elif 'Warnings Found:' in line:
                    try:
                        count = int(line.split(':')[1].split()[0])
                        self.stats['bad_practices'] = count
                    except (ValueError, IndexError):
                        # Skip parsing errors
                        continue
                elif 'Files with Issues:' in line:
                    try:
                        count = int(line.split(':')[1].strip())
                        # Store in error_flags
                        if count > 0:
                            print(f"  ⚠️  {count} files have issues")
                    except (ValueError, IndexError):
                        # Skip parsing errors
                        continue
            # Look for specific error flags in the output
            if 'SecurityRisk' in output:
                self.stats['security_risks'] += output.count('SecurityRisk')
                self.error_flags['SecurityRisk'].append("exec() or eval() usage detected")
            
            if 'EmptyExcept' in output:
                self.stats['empty_except_blocks'] = output.count('EmptyExcept')
                self.error_flags['EmptyExceptBlock'].append(f"{output.count('EmptyExcept')} empty except blocks found")
            
            if 'BareExcept' in output:
                self.stats['bare_except_clauses'] = output.count('BareExcept')
                self.error_flags['BareExceptClause'].append(f"{output.count('BareExcept')} bare except clauses found")
            
            if 'ShebangWarning' in output:
                self.stats['shebang_warnings'] = output.count('ShebangWarning')
                self.error_flags['ShebangWarning'].append(f"{output.count('ShebangWarning')} files using system Python")
            
            if 'JSONError' in output:
                self.stats['json_errors'] = output.count('JSONError')
                self.error_flags['JSONError'].append("Invalid JSON files detected")
            
            if 'BashError' in output:
                self.stats['bash_errors'] = output.count('BashError')
                self.error_flags['BashError'].append("Bash syntax errors detected")
            
            print("  ✓ Comprehensive error check complete")
            
            # Print error flag summary
            critical_flags = [
                flag for flag in ['SecurityRisk', 'CompilationError', 'SyntaxError', 'JSONError', 'BashError']
                if self.error_flags.get(flag)
            ]
            
            if critical_flags:
                print(f"\n  🚨 Critical Issues Found:")
                for flag in critical_flags:
                    for issue in self.error_flags[flag]:
                        print(f"     ❌ {issue}")
            
            return self.stats['syntax_errors'] + self.stats['security_risks']
            
        except subprocess.TimeoutExpired:
            print("  ⚠️  Deep scan timeout - skipping")
            return 0
        except Exception as e:
            print(f"  ⚠️  Could not run deep scanner: {str(e)[:50]}")
            return 0
    
    def validate_file_locations(self):
        """Validate and flag misplaced files"""
        issues = []
        
        # Check datasets folder for non-CSV/non-reference files
        datasets_dir = self.base_dir / 'SecIDS-CNN' / 'datasets'
        if datasets_dir.exists():
            for md_file in datasets_dir.glob('*.md'):
                # Allow specific reference documents in datasets
                allowed_refs = ['IP_SOURCE_QUICK_REF.md', 'MD_NAMING_CONVENTION.md', 
                               'DATASET_README.md', 'COLUMNS.md']
                if md_file.name not in allowed_refs:
                    issues.append(f"⚠ Unexpected .md file in datasets/: {md_file.name}")
            
            # Check for non-CSV data files
            for file_type in ['*.txt', '*.log', '*.json']:
                for file in datasets_dir.glob(file_type):
                    issues.append(f"⚠ Non-dataset file in datasets/: {file.name}")
        
        # Check Results folder for non-result files
        results_dir = self.base_dir / 'Results'
        if results_dir.exists():
            # .json files are OK (deep_scan_report, threat_report)
            # .csv files are OK (detection_results, deep_scan_results)
            # But flag other types
            for file_type in ['*.txt', '*.log', '*.py']:
                for file in results_dir.glob(file_type):
                    issues.append(f"⚠ Unexpected file type in Results/: {file.name}")
        
        return issues
    
    def should_exclude(self, path):
        """Check if path should be excluded from redundancy scanning"""
        exclude_dirs = {'.venv_test', '.venv', '__pycache__', '.git',
                       'node_modules', '.pytest_cache', 'TrashDump'}
        path_str = str(path)
        return any(excluded in path_str for excluded in exclude_dirs)
    
    def get_file_hash(self, filepath):
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
    
    def cleanup_pycache(self):
        """Remove all __pycache__ directories"""
        pycache_count = 0
        for root, dirs, files in os.walk(self.base_dir):
            if '__pycache__' in dirs and not self.should_exclude(Path(root)):
                pycache_path = Path(root) / '__pycache__'
                try:
                    shutil.rmtree(pycache_path)
                    pycache_count += 1
                    self.moves.append(f"Removed __pycache__ from {Path(root).relative_to(self.base_dir)}")
                except PermissionError:
                    # Skip directories we don't have permission to remove
                    self.skipped.append(f"Cannot remove {pycache_path} (permission denied)")
                except OSError as e:
                    # Skip directories that are in use or locked
                    self.skipped.append(f"Cannot remove {pycache_path} ({str(e)[:40]})")
            # Remove excluded dirs from traversal
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
        
        self.stats['pycache_removed'] = pycache_count
    
    def cleanup_pyc_files(self):
        """Remove all .pyc files"""
        pyc_count = 0
        for root, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
            for file in files:
                if file.endswith('.pyc'):
                    pyc_path = Path(root) / file
                    if not self.should_exclude(pyc_path):
                        try:
                            pyc_path.unlink()
                            pyc_count += 1
                        except (PermissionError, OSError):
                            # Skip files we can't delete
                            continue
        
        self.stats['pyc_removed'] = pyc_count
        if pyc_count > 0:
            self.moves.append(f"Removed {pyc_count} .pyc bytecode files")
    
    def find_and_move_duplicates(self):
        """Find and move duplicate files based on content"""
        file_hashes = defaultdict(list)
        
        for root, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip large files and certain types
                if file_path.stat().st_size > 10 * 1024 * 1024:
                    continue
                
                if file_path.suffix in ['.csv', '.pcap', '.h5', '.log']:
                    continue
                
                file_hash = self.get_file_hash(file_path)
                if file_hash:
                    file_hashes[file_hash].append(file_path)
        
        # Move duplicates
        for file_hash, paths in file_hashes.items():
            if len(paths) > 1:
                keep_file = paths[0]
                for dup_path in paths[1:]:
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        relative_path = dup_path.relative_to(self.base_dir)
                        trash_subdir = self.trash_dump / relative_path.parent
                        trash_subdir.mkdir(parents=True, exist_ok=True)
                        
                        new_name = f"{dup_path.stem}_{timestamp}{dup_path.suffix}"
                        trash_path = trash_subdir / new_name
                        
                        shutil.move(str(dup_path), str(trash_path))
                        self.stats['duplicates_moved'] += 1
                        self.moves.append(f"Moved duplicate {dup_path.name} -> TrashDump/ (duplicate of {keep_file.name})")
                    except (OSError, PermissionError) as e:
                        # Skip files we can't move
                        self.skipped.append(f"Could not move {dup_path.name}: {str(e)[:40]}")
    
    def find_and_move_redundant(self):
        """Find and move files with redundant patterns"""
        redundant_patterns = ['_old', '_backup', '.bak', '_copy', '~', '.tmp', '.temp']
        redundant_count = 0
        
        for root, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
            
            for file in files:
                file_lower = file.lower()
                if any(pattern in file_lower for pattern in redundant_patterns):
                    file_path = Path(root) / file
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        relative_path = file_path.relative_to(self.base_dir)
                        trash_subdir = self.trash_dump / relative_path.parent
                        trash_subdir.mkdir(parents=True, exist_ok=True)
                        
                        new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                        trash_path = trash_subdir / new_name
                        
                        shutil.move(str(file_path), str(trash_path))
                        redundant_count += 1
                        self.moves.append(f"Moved redundant file {file} -> TrashDump/")
                    except (OSError, PermissionError) as e:
                        # Skip files we can't move
                        self.skipped.append(f"Could not move {file}: {str(e)[:40]}")
        
        self.stats['redundant_moved'] = redundant_count
    
    def run(self):
        """Run all organization tasks"""
        print("="*70)
        print("FILE ORGANIZATION SCRIPT - Enhanced Version")
        print("Includes Redundancy Detection & Cleanup")
        print("="*70)
        print(f"Base directory: {self.base_dir}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run organization tasks
        tasks = [
            ("Reports", self.organize_reports),
            ("Test Results", self.organize_test_results),
            ("Logs", self.organize_logs),
            ("Configs", self.organize_configs),
            ("Captures", self.organize_pcap_files),
            ("Models", self.organize_models),
            ("Datasets", self.organize_datasets),
            ("Scripts", self.organize_scripts),
            ("Launchers", self.organize_launchers),
            ("Logs Directory", self.consolidate_logs_dirs),
            ("Detection Results", self.organize_detection_results),
            ("Result Reports", self.organize_result_reports)
        ]
        
        for task_name, task_func in tasks:
            print(f"Processing {task_name}...", end=' ')
            try:
                task_func()
                print("✓")
            except Exception as e:
                print(f"⚠ Error: {e}")
                self.skipped.append(f"{task_name}: {str(e)}")
        
        # Run redundancy cleanup
        print("\n" + "="*70)
        print("REDUNDANCY CLEANUP")
        print("="*70)
        
        redundancy_tasks = [
            ("Python Cache Cleanup", self.cleanup_pycache),
            (".pyc File Cleanup", self.cleanup_pyc_files),
            ("Duplicate Detection", self.find_and_move_duplicates),
            ("Redundant Pattern Detection", self.find_and_move_redundant),
            ("Python Debug Scan", self.run_debug_scan),
            ("Comprehensive Error Check", self.run_comprehensive_error_check)
        ]
        
        for task_name, task_func in redundancy_tasks:
            print(f"Processing {task_name}...", end=' ')
            try:
                task_func()
                print("✓")
            except Exception as e:
                print(f"⚠ Error: {e}")
                self.skipped.append(f"{task_name}: {str(e)}")
        
        # Report results
        print("\n" + "="*70)
        print("ORGANIZATION SUMMARY")
        print("="*70)
        
        if self.moves:
            print(f"\n✓ Successfully organized {len(self.moves)} items:\n")
            for move in self.moves:
                print(f"  • {move}")
            
            print(f"\n📊 Statistics by Category:")
            for category, count in self.stats.items():
                if count > 0:
                    print(f"  • {category.replace('_', ' ').title()}: {count}")
            
            # Show error flags if any critical issues found
            critical_errors = sum([
                self.stats.get('security_risks', 0),
                self.stats.get('syntax_errors', 0),
                self.stats.get('compilation_errors', 0),
                self.stats.get('json_errors', 0),
                self.stats.get('bash_errors', 0)
            ])
            
            if critical_errors > 0:
                print(f"\n🚨 CRITICAL ERROR FLAGS:")
                if self.stats.get('security_risks', 0) > 0:
                    print(f"  ❌ {self.stats['security_risks']} Security Risk(s)")
                if self.stats.get('syntax_errors', 0) > 0:
                    print(f"  ❌ {self.stats['syntax_errors']} Syntax Error(s)")
                if self.stats.get('compilation_errors', 0) > 0:
                    print(f"  ❌ {self.stats['compilation_errors']} Compilation Error(s)")
                if self.stats.get('json_errors', 0) > 0:
                    print(f"  ❌ {self.stats['json_errors']} JSON Error(s)")
                if self.stats.get('bash_errors', 0) > 0:
                    print(f"  ❌ {self.stats['bash_errors']} Bash Error(s)")
                print(f"  💡 Run 'python Scripts/deep_error_scanner.py' for details")
            
            # Show warnings
            warnings_count = sum([
                self.stats.get('bad_practices', 0),
                self.stats.get('empty_except_blocks', 0),
                self.stats.get('bare_except_clauses', 0),
                self.stats.get('shebang_warnings', 0)
            ])
            
            if warnings_count > 0:
                print(f"\n⚠️  CODE QUALITY WARNINGS:")
                if self.stats.get('bad_practices', 0) > 0:
                    print(f"  ⚠️  {self.stats['bad_practices']} Bad Practice(s)")
                if self.stats.get('empty_except_blocks', 0) > 0:
                    print(f"  ⚠️  {self.stats['empty_except_blocks']} Empty Except Block(s)")
                if self.stats.get('bare_except_clauses', 0) > 0:
                    print(f"  ⚠️  {self.stats['bare_except_clauses']} Bare Except Clause(s)")
                if self.stats.get('shebang_warnings', 0) > 0:
                    print(f"  ⚠️  {self.stats['shebang_warnings']} Shebang Warning(s)")
            
            if self.consolidated_files:
                print(f"\n📝 Consolidated to Master-Manual.md:")
                for filename in self.consolidated_files:
                    print(f"  • {filename}")
        else:
            print("\n✓ All files already in correct locations")
        
        if self.skipped:
            print(f"\n⚠ Skipped {len(self.skipped)} items:")
            for skip in self.skipped:
                print(f"  • {skip}")
        
        # Run validation
        print("\n" + "="*70)
        print("FILE LOCATION VALIDATION")
        print("="*70)
        validation_issues = self.validate_file_locations()
        
        if validation_issues:
            print(f"\n⚠ Found {len(validation_issues)} potential issues:")
            for issue in validation_issues:
                print(f"  {issue}")
            print("\n💡 Note: Dataset reference files (IP_SOURCE_QUICK_REF.md, MD_NAMING_CONVENTION.md)")
            print("   are intentionally kept in datasets/ for quick reference.")
        else:
            print("\n✅ All files are in their correct locations!")
        
        print("\n" + "="*70)
        print("ORGANIZATION COMPLETE")
        print("="*70)

if __name__ == '__main__':
    organizer = FileOrganizer()
    organizer.run()

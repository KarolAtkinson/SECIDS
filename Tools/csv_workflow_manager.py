#!/usr/bin/env python3
"""
CSV Workflow Manager - Automated Dataset Pipeline
Manages the flow of CSV files for continuous model improvement
"""

import os
import sys
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime
import json


class CSVWorkflowManager:
    """
    Manages CSV file workflow for continuous model improvement:
    1. Training data → Threat_Detection_Model_1
    2. Train models → Generate predictions CSV
    3. Transfer predictions → datasets folder
    4. Use for improved detection accuracy
    """
    
    def __init__(self, project_root=None):
        """Initialize workflow manager"""
        if project_root is None:
            project_root = Path(__file__).parent
        else:
            project_root = Path(project_root)
        
        self.project_root = project_root
        
        # Define key directories
        self.training_dir = project_root / "Model_Tester" / "Threat_Detection_Model_1"
        self.datasets_dir = project_root / "Model_Tester" / "Code" / "datasets"
        self.secids_datasets_dir = project_root / "SecIDS-CNN" / "datasets"
        
        # Workflow tracking
        self.workflow_log = project_root / "csv_workflow_log.json"
        self.history = self._load_history()
        
        # Ensure directories exist
        self.training_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.secids_datasets_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self):
        """Load workflow history"""
        if self.workflow_log.exists():
            with open(self.workflow_log, 'r') as f:
                return json.load(f)
        return {'workflows': [], 'transfers': []}
    
    def _save_history(self):
        """Save workflow history"""
        with open(self.workflow_log, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def log(self, message, level="INFO"):
        """Print and log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def organize_training_data(self, dry_run=False):
        """
        Step 1: Organize all CSV files into Threat_Detection_Model_1
        Moves raw data and test files to training directory
        """
        self.log("=" * 80)
        self.log("STEP 1: ORGANIZING TRAINING DATA")
        self.log("=" * 80)
        
        # Files to move to training directory
        source_locations = [
            self.secids_datasets_dir / "Test1.csv",
            self.secids_datasets_dir / "Test2.csv",
            self.secids_datasets_dir / "Test3.csv",
            self.datasets_dir / "Test3.csv",
        ]
        
        moved_count = 0
        
        for source in source_locations:
            if not source.exists():
                continue
            
            dest = self.training_dir / source.name
            
            # Check if file already exists in training dir
            if dest.exists():
                self.log(f"  ⚠️  Already in training: {source.name}", "SKIP")
                continue
            
            if dry_run:
                self.log(f"  [DRY RUN] Would move: {source.name} → Threat_Detection_Model_1/", "INFO")
            else:
                try:
                    shutil.copy2(source, dest)
                    self.log(f"  ✅ Copied: {source.name} → Threat_Detection_Model_1/", "SUCCESS")
                    moved_count += 1
                except Exception as e:
                    self.log(f"  ❌ Error copying {source.name}: {e}", "ERROR")
        
        self.log(f"\n✅ Organized {moved_count} files into training directory")
        return moved_count
    
    def train_and_generate_results(self, model_type='unified', dry_run=False):
        """
        Step 2: Train models and generate prediction CSV
        Uses training data to create improved predictions
        """
        self.log("=" * 80)
        self.log("STEP 2: TRAIN MODELS & GENERATE RESULTS")
        self.log("=" * 80)
        
        if dry_run:
            self.log("[DRY RUN] Would train models and generate predictions", "INFO")
            return None
        
        # Import training modules
        try:
            sys.path.insert(0, str(self.project_root / "Model_Tester" / "Code"))
            
            if model_type == 'unified':
                self.log("Training unified threat model...", "INFO")
                from train_unified_model import main as train_unified
                
                # Train the model
                train_unified()
                
                self.log("✅ Unified model training complete", "SUCCESS")
                
            elif model_type == 'secids':
                self.log("Training SecIDS-CNN model...", "INFO")
                os.chdir(self.project_root / "SecIDS-CNN")
                
                # Import and train
                sys.path.insert(0, str(self.project_root / "SecIDS-CNN"))
                from train_and_test import main as train_secids
                
                train_secids()
                
                self.log("✅ SecIDS-CNN training complete", "SUCCESS")
            
            # Generate predictions on test data
            self._generate_predictions()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Training error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_predictions(self):
        """Generate predictions CSV from trained models"""
        self.log("\nGenerating predictions from trained models...", "INFO")
        
        # Use the trained model to predict on test data
        test_files = list(self.training_dir.glob("Test*.csv"))
        
        if not test_files:
            self.log("  ⚠️  No test files found for prediction", "WARNING")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.datasets_dir / f"training_results_{timestamp}.csv"
        
        # Run detection on test files
        try:
            os.chdir(self.project_root / "SecIDS-CNN")
            sys.path.insert(0, str(self.project_root / "SecIDS-CNN"))
            
            from run_model import main as run_detection
            
            # Temporarily modify sys.argv to pass file arguments
            original_argv = sys.argv
            sys.argv = ['run_model.py', 'file'] + [str(f) for f in test_files[:1]]  # Use first test file
            
            run_detection()
            
            sys.argv = original_argv
            
            # Check if detection results were generated
            results_path = self.project_root / "Results" / "detection_results_latest.csv"
            if results_path.exists():
                shutil.copy2(results_path, results_file)
                self.log(f"  ✅ Predictions saved: {results_file.name}", "SUCCESS")
                return results_file
            
        except Exception as e:
            self.log(f"  ⚠️  Prediction generation error: {e}", "WARNING")
        
        return None
    
    def transfer_to_datasets(self, dry_run=False):
        """
        Step 3: Transfer new prediction results to datasets folder
        Moves generated predictions for use in detection
        """
        self.log("=" * 80)
        self.log("STEP 3: TRANSFER RESULTS TO DATASETS")
        self.log("=" * 80)
        
        # Find recent training results
        result_files = sorted(
            self.datasets_dir.glob("training_results_*.csv"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        if not result_files:
            self.log("  ⚠️  No training results found to transfer", "WARNING")
            return 0
        
        transferred_count = 0
        
        # Transfer to both dataset locations for accessibility
        for result_file in result_files[:3]:  # Latest 3 results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Copy to Model_Tester datasets using MD_*.csv naming convention
            dest1 = self.datasets_dir / f"MD_{timestamp}.csv"
            
            # Copy to SecIDS datasets using MD_*.csv naming convention
            dest2 = self.secids_datasets_dir / f"MD_{timestamp}.csv"
            
            if dry_run:
                self.log(f"  [DRY RUN] Would transfer: {result_file.name}", "INFO")
            else:
                try:
                    if not dest1.exists():
                        shutil.copy2(result_file, dest1)
                        self.log(f"  ✅ Transferred: {result_file.name} → ML datasets/", "SUCCESS")
                        transferred_count += 1
                    
                    if not dest2.exists():
                        shutil.copy2(result_file, dest2)
                        self.log(f"  ✅ Transferred: {result_file.name} → SecIDS datasets/", "SUCCESS")
                    
                    # Record transfer
                    self.history['transfers'].append({
                        'timestamp': timestamp,
                        'source': result_file.name,
                        'destinations': [str(dest1), str(dest2)]
                    })
                    
                except Exception as e:
                    self.log(f"  ❌ Transfer error: {e}", "ERROR")
        
        self._save_history()
        self.log(f"\n✅ Transferred {transferred_count} result files to datasets")
        return transferred_count
    
    def run_improved_detection(self, dry_run=False):
        """
        Step 4: Run detection with improved datasets
        Uses transferred results to improve detection accuracy
        """
        self.log("=" * 80)
        self.log("STEP 4: RUN IMPROVED DETECTION")
        self.log("=" * 80)
        
        if dry_run:
            self.log("[DRY RUN] Would run detection with improved datasets", "INFO")
            return
        
        # Find improved datasets (now using MD_*.csv convention)
        improved_files = list(self.secids_datasets_dir.glob("MD_*.csv"))
        
        if not improved_files:
            self.log("  ⚠️  No improved datasets found", "WARNING")
            return
        
        # Use latest improved dataset
        latest_improved = max(improved_files, key=lambda f: f.stat().st_mtime)
        
        self.log(f"Using improved dataset: {latest_improved.name}", "INFO")
        
        try:
            # Run detection
            os.chdir(self.project_root / "SecIDS-CNN")
            sys.path.insert(0, str(self.project_root / "SecIDS-CNN"))
            
            from run_model import main as run_detection
            
            original_argv = sys.argv
            sys.argv = ['run_model.py', 'file', str(latest_improved)]
            
            run_detection()
            
            sys.argv = original_argv
            
            self.log("✅ Improved detection complete", "SUCCESS")
            
        except Exception as e:
            self.log(f"❌ Detection error: {e}", "ERROR")
    
    def run_full_workflow(self, dry_run=False):
        """
        Run complete workflow: organize → train → transfer → detect
        """
        self.log("\n" + "=" * 80)
        self.log("CSV WORKFLOW MANAGER - FULL PIPELINE")
        self.log("=" * 80)
        self.log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Dry Run: {dry_run}\n")
        
        workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Step 1: Organize training data
        moved = self.organize_training_data(dry_run)
        
        if not dry_run and moved > 0:
            print()
        
        # Step 2: Train and generate results
        if not dry_run:
            trained = self.train_and_generate_results(model_type='unified', dry_run=dry_run)
            print()
        
        # Step 3: Transfer results
        transferred = self.transfer_to_datasets(dry_run)
        print()
        
        # Step 4: Run improved detection
        if not dry_run:
            self.run_improved_detection(dry_run)
        
        # Record workflow
        if not dry_run:
            self.history['workflows'].append({
                'id': workflow_id,
                'timestamp': datetime.now().isoformat(),
                'files_moved': moved,
                'files_transferred': transferred
            })
            self._save_history()
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("WORKFLOW SUMMARY")
        self.log("=" * 80)
        self.log(f"Files organized: {moved}")
        self.log(f"Files transferred: {transferred}")
        self.log(f"Workflow ID: {workflow_id}")
        self.log("=" * 80)
    
    def show_status(self):
        """Show current CSV workflow status"""
        self.log("=" * 80)
        self.log("CSV WORKFLOW STATUS")
        self.log("=" * 80)
        
        # Count files in each location
        training_files = list(self.training_dir.glob("*.csv"))
        dataset_files = list(self.datasets_dir.glob("*.csv"))
        secids_files = list(self.secids_datasets_dir.glob("*.csv"))
        improved_files = list(self.secids_datasets_dir.glob("MD_*.csv"))
        
        self.log(f"\nTraining Data (Threat_Detection_Model_1): {len(training_files)} files")
        for f in sorted(training_files)[:5]:
            self.log(f"  - {f.name}")
        if len(training_files) > 5:
            self.log(f"  ... and {len(training_files) - 5} more")
        
        self.log(f"\nML Datasets: {len(dataset_files)} files")
        for f in sorted(dataset_files)[:5]:
            self.log(f"  - {f.name}")
        if len(dataset_files) > 5:
            self.log(f"  ... and {len(dataset_files) - 5} more")
        
        self.log(f"\nSecIDS Datasets: {len(secids_files)} files")
        for f in sorted(secids_files)[:5]:
            self.log(f"  - {f.name}")
        if len(secids_files) > 5:
            self.log(f"  ... and {len(secids_files) - 5} more")
        
        self.log(f"\nImproved Datasets: {len(improved_files)} files")
        for f in sorted(improved_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            age = datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)
            self.log(f"  - {f.name} ({age.days} days old)")
        
        self.log(f"\nTotal workflows run: {len(self.history.get('workflows', []))}")
        self.log(f"Total transfers: {len(self.history.get('transfers', []))}")
        
        self.log("=" * 80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='CSV Workflow Manager - Automated dataset pipeline for continuous improvement'
    )
    parser.add_argument(
        '--action',
        choices=['full', 'organize', 'train', 'transfer', 'detect', 'status'],
        default='status',
        help='Action to perform (default: status)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--model',
        choices=['unified', 'secids'],
        default='unified',
        help='Model type to train (default: unified)'
    )
    
    args = parser.parse_args()
    
    manager = CSVWorkflowManager()
    
    if args.action == 'full':
        manager.run_full_workflow(dry_run=args.dry_run)
    elif args.action == 'organize':
        manager.organize_training_data(dry_run=args.dry_run)
    elif args.action == 'train':
        manager.train_and_generate_results(model_type=args.model, dry_run=args.dry_run)
    elif args.action == 'transfer':
        manager.transfer_to_datasets(dry_run=args.dry_run)
    elif args.action == 'detect':
        manager.run_improved_detection(dry_run=args.dry_run)
    elif args.action == 'status':
        manager.show_status()


if __name__ == '__main__':
    main()

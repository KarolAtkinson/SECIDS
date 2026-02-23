#!/usr/bin/env python3
"""
SecIDS-CNN Pipeline Orchestrator
=================================
Unified automation pipeline that connects all components of the SecIDS-CNN project.
This orchestrator manages the complete workflow from data capture to threat detection.

Workflow Stages:
1. Data Collection (PCAP capture or existing files)
2. Feature Extraction (PCAP to CSV conversion)
3. Dataset Creation & Enhancement
4. Model Training (Both SecIDS-CNN and Unified models)
5. Threat Detection (Live or batch mode)
6. Results Analysis & Reporting

Usage:
    # Run complete pipeline
    python3 pipeline_orchestrator.py --mode full
    
    # Capture and analyze
    python3 pipeline_orchestrator.py --mode capture --iface eth0 --duration 60
    
    # Train models from existing data
    python3 pipeline_orchestrator.py --mode train
    
    # Live detection only
    python3 pipeline_orchestrator.py --mode detect-live --iface eth0
    
    # Batch detection
    python3 pipeline_orchestrator.py --mode detect-batch --input datasets/Test1.csv
"""

import os
import sys
import argparse
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json
import shutil

# Setup project paths
PROJECT_ROOT = Path(__file__).resolve().parent
SECIDS_DIR = PROJECT_ROOT / 'SecIDS-CNN'
MASTER_ML_DIR = PROJECT_ROOT / 'Model_Tester'
TOOLS_DIR = PROJECT_ROOT / 'tools'
CAPTURES_DIR = PROJECT_ROOT / 'Captures'
DATASETS_DIR = PROJECT_ROOT / 'SecIDS-CNN' / 'datasets'

# Add to Python path
sys.path.insert(0, str(SECIDS_DIR))
sys.path.insert(0, str(MASTER_ML_DIR / 'Code'))
sys.path.insert(0, str(TOOLS_DIR))

# Setup logging
log_file = PROJECT_ROOT / f'pipeline_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PipelineConfig:
    """Configuration for pipeline execution"""
    def __init__(self):
        self.capture_duration = 120  # seconds
        self.capture_interface = 'eth0'
        self.window_size = 10.0  # seconds for live detection
        self.processing_interval = 4.0  # seconds
        self.model_backend = 'tf'  # 'tf' or 'unified'
        self.enable_enhanced_features = True
        self.train_unified_model = True
        self.save_intermediate_results = True
        self.output_dir = PROJECT_ROOT / 'pipeline_outputs'
        
    def to_dict(self):
        return {
            'capture_duration': self.capture_duration,
            'capture_interface': self.capture_interface,
            'window_size': self.window_size,
            'processing_interval': self.processing_interval,
            'model_backend': self.model_backend,
            'enable_enhanced_features': self.enable_enhanced_features,
            'train_unified_model': self.train_unified_model,
            'save_intermediate_results': self.save_intermediate_results,
            'output_dir': str(self.output_dir)
        }


class PipelineOrchestrator:
    """Main orchestrator for the SecIDS-CNN pipeline"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.config.output_dir.mkdir(exist_ok=True, parents=True)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'stages': {},
            'errors': []
        }
        
    def log_stage(self, stage_name: str, status: str, details: Dict = None):
        """Log stage execution"""
        self.results['stages'][stage_name] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        logger.info(f"Stage [{stage_name}]: {status}")
        
    def run_command(self, cmd: List[str], stage_name: str, sudo: bool = False) -> bool:
        """Execute a shell command and track results"""
        if sudo and os.geteuid() != 0:
            cmd = ['sudo'] + cmd
            
        logger.info(f"Executing: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                self.log_stage(stage_name, 'SUCCESS', {'output': result.stdout[:500]})
                return True
            else:
                error_msg = result.stderr or result.stdout
                self.log_stage(stage_name, 'FAILED', {'error': error_msg[:500]})
                self.results['errors'].append({
                    'stage': stage_name,
                    'error': error_msg[:500]
                })
                return False
        except subprocess.TimeoutExpired:
            self.log_stage(stage_name, 'TIMEOUT', {'error': 'Command timed out'})
            return False
        except Exception as e:
            self.log_stage(stage_name, 'ERROR', {'error': str(e)})
            self.results['errors'].append({'stage': stage_name, 'error': str(e)})
            return False
    
    def stage_1_verify_setup(self) -> bool:
        """Stage 1: Verify system setup and dependencies"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 1: SYSTEM VERIFICATION")
        logger.info("="*80)
        
        cmd = [sys.executable, str(TOOLS_DIR / 'verify_setup.py')]
        return self.run_command(cmd, 'verify_setup')
    
    def stage_2_capture_traffic(self, duration: int = None, iface: str = None) -> Optional[Path]:
        """Stage 2: Capture network traffic"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 2: NETWORK TRAFFIC CAPTURE")
        logger.info("="*80)
        
        duration = duration or self.config.capture_duration
        iface = iface or self.config.capture_interface
        
        timestamp = int(time.time())
        pcap_file = CAPTURES_DIR / f'capture_{timestamp}.pcap'
        CAPTURES_DIR.mkdir(exist_ok=True)
        
        # Try dumpcap first, then tshark
        for tool in ['dumpcap', 'tshark']:
            cmd = [tool, '-i', iface, '-a', f'duration:{duration}', '-w', str(pcap_file)]
            if self.run_command(cmd, f'capture_traffic_{tool}', sudo=True):
                logger.info(f"Capture saved to: {pcap_file}")
                return pcap_file
        
        logger.error("No capture tool available (dumpcap/tshark)")
        return None
    
    def stage_3_convert_pcap_to_csv(self, pcap_file: Path) -> Optional[Path]:
        """Stage 3: Convert PCAP to CSV features"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 3: FEATURE EXTRACTION")
        logger.info("="*80)
        
        csv_file = DATASETS_DIR / f'{pcap_file.stem}.csv'
        DATASETS_DIR.mkdir(exist_ok=True, parents=True)
        
        cmd = [
            sys.executable,
            str(TOOLS_DIR / 'pcap_to_secids_csv.py'),
            '-i', str(pcap_file),
            '-o', str(csv_file)
        ]
        
        if self.run_command(cmd, 'pcap_to_csv'):
            logger.info(f"CSV features saved to: {csv_file}")
            return csv_file
        return None
    
    def stage_4_enhance_dataset(self, csv_file: Path) -> Optional[Path]:
        """Stage 4: Enhance dataset with additional features"""
        if not self.config.enable_enhanced_features:
            logger.info("Enhanced features disabled, skipping...")
            return csv_file
            
        logger.info("\n" + "="*80)
        logger.info("STAGE 4: DATASET ENHANCEMENT")
        logger.info("="*80)
        
        enhanced_file = csv_file.parent / f'{csv_file.stem}_enhanced.csv'
        
        cmd = [
            sys.executable,
            str(TOOLS_DIR / 'create_enhanced_dataset.py'),
            str(csv_file),
            str(enhanced_file)
        ]
        
        if self.run_command(cmd, 'enhance_dataset'):
            logger.info(f"Enhanced dataset saved to: {enhanced_file}")
            return enhanced_file
        return csv_file  # Return original if enhancement fails
    
    def stage_5_train_secids_model(self) -> bool:
        """Stage 5: Train SecIDS-CNN model"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 5: SECIDS-CNN MODEL TRAINING")
        logger.info("="*80)
        
        cmd = [
            sys.executable,
            str(SECIDS_DIR / 'train_and_test.py')
        ]
        
        return self.run_command(cmd, 'train_secids_model')
    
    def stage_6_train_unified_model(self) -> bool:
        """Stage 6: Train Unified Threat Model"""
        if not self.config.train_unified_model:
            logger.info("Unified model training disabled, skipping...")
            return True
            
        logger.info("\n" + "="*80)
        logger.info("STAGE 6: UNIFIED MODEL TRAINING")
        logger.info("="*80)
        
        cmd = [
            sys.executable,
            str(MASTER_ML_DIR / 'Code' / 'train_unified_model.py')
        ]
        
        return self.run_command(cmd, 'train_unified_model')
    
    def stage_7_run_master_pipeline(self) -> bool:
        """Stage 7: Run Master ML/AI pipeline"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 7: MASTER ML/AI PIPELINE")
        logger.info("="*80)
        
        cmd = [
            sys.executable,
            str(MASTER_ML_DIR / 'Code' / 'main.py')
        ]
        
        return self.run_command(cmd, 'master_pipeline')
    
    def stage_8_detect_batch(self, csv_file: Path) -> bool:
        """Stage 8: Batch threat detection"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 8: BATCH THREAT DETECTION")
        logger.info("="*80)
        
        cmd = [
            sys.executable,
            str(SECIDS_DIR / 'run_model.py'),
            'file',
            str(csv_file)
        ]
        
        return self.run_command(cmd, 'batch_detection')
    
    def stage_9_detect_live(self, duration: int = 60) -> bool:
        """Stage 9: Live threat detection"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 9: LIVE THREAT DETECTION")
        logger.info("="*80)
        
        cmd = [
            sys.executable,
            str(SECIDS_DIR / 'run_model.py'),
            'live',
            '--iface', self.config.capture_interface,
            '--window', str(self.config.window_size),
            '--interval', str(self.config.processing_interval),
            '--backend', self.config.model_backend
        ]
        
        # Live detection runs indefinitely, so we'll start it and let it run
        logger.info(f"Starting live detection for {duration} seconds...")
        logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Let it run for specified duration
            time.sleep(duration)
            process.terminate()
            
            stdout, stderr = process.communicate(timeout=5)
            logger.info(f"Live detection output:\n{stdout}")
            
            self.log_stage('live_detection', 'SUCCESS', {
                'duration': duration,
                'output_sample': stdout[:500]
            })
            return True
            
        except Exception as e:
            logger.error(f"Live detection failed: {e}")
            self.log_stage('live_detection', 'FAILED', {'error': str(e)})
            return False
    
    def stage_10_analyze_results(self) -> bool:
        """Stage 10: Analyze and report results"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 10: RESULTS ANALYSIS")
        logger.info("="*80)
        
        # Look for recent result files
        result_files = []
        
        # Check for detection results
        detection_results = Path('Results') / 'detection_results_latest.csv'
        if detection_results.exists():
            result_files.append(detection_results)
            
        # Check for threat origins analysis
        threat_origins = PROJECT_ROOT / 'threat_origins_analysis.csv'
        if threat_origins.exists():
            result_files.append(threat_origins)
        
        if result_files:
            logger.info("Result files found:")
            for rf in result_files:
                logger.info(f"  - {rf}")
                if self.config.save_intermediate_results:
                    # Copy to output directory
                    dest = self.config.output_dir / rf.name
                    shutil.copy2(rf, dest)
                    logger.info(f"    Copied to: {dest}")
        
        # Run threat origins analysis if detect results exist
        if detection_results.exists():
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / 'analyze_threat_origins.py')
            ]
            self.run_command(cmd, 'analyze_threat_origins')
        
        self.log_stage('results_analysis', 'SUCCESS', {
            'result_files': [str(f) for f in result_files]
        })
        return True
    
    def save_pipeline_report(self):
        """Save comprehensive pipeline report"""
        report_file = self.config.output_dir / f'pipeline_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        report = {
            'config': self.config.to_dict(),
            'results': self.results,
            'summary': {
                'total_stages': len(self.results['stages']),
                'successful_stages': sum(1 for s in self.results['stages'].values() if s['status'] == 'SUCCESS'),
                'failed_stages': sum(1 for s in self.results['stages'].values() if s['status'] in ['FAILED', 'ERROR']),
                'total_errors': len(self.results['errors'])
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Pipeline report saved to: {report_file}")
        logger.info(f"{'='*80}")
        
        return report_file
    
    def run_full_pipeline(self):
        """Execute complete pipeline"""
        logger.info("\n" + "="*80)
        logger.info("SECIDS-CNN COMPLETE PIPELINE EXECUTION")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        # Stage 1: Verify setup
        if not self.stage_1_verify_setup():
            logger.warning("Setup verification failed, continuing anyway...")
        
        # Stage 2: Capture traffic
        pcap_file = self.stage_2_capture_traffic()
        if not pcap_file:
            logger.error("Traffic capture failed")
            return False
        
        # Stage 3: Convert to CSV
        csv_file = self.stage_3_convert_pcap_to_csv(pcap_file)
        if not csv_file:
            logger.error("PCAP to CSV conversion failed")
            return False
        
        # Stage 4: Enhance dataset
        enhanced_file = self.stage_4_enhance_dataset(csv_file)
        
        # Stage 5: Train SecIDS model
        self.stage_5_train_secids_model()
        
        # Stage 6: Train Unified model
        self.stage_6_train_unified_model()
        
        # Stage 7: Run Master pipeline
        self.stage_7_run_master_pipeline()
        
        # Stage 8: Batch detection on captured data
        self.stage_8_detect_batch(enhanced_file or csv_file)
        
        # Stage 9: Live detection demo
        self.stage_9_detect_live(duration=30)
        
        # Stage 10: Analyze results
        self.stage_10_analyze_results()
        
        # Save report
        report_file = self.save_pipeline_report()
        
        logger.info("\n" + "="*80)
        logger.info("PIPELINE EXECUTION COMPLETE")
        logger.info(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Report: {report_file}")
        logger.info(f"Log: {log_file}")
        logger.info("="*80)
        
        return True
    
    def run_capture_mode(self, duration: int, iface: str):
        """Capture and analyze mode"""
        logger.info("Running in CAPTURE mode...")
        
        self.stage_1_verify_setup()
        pcap_file = self.stage_2_capture_traffic(duration, iface)
        if pcap_file:
            csv_file = self.stage_3_convert_pcap_to_csv(pcap_file)
            if csv_file:
                enhanced_file = self.stage_4_enhance_dataset(csv_file)
                self.stage_8_detect_batch(enhanced_file or csv_file)
                self.stage_10_analyze_results()
        
        self.save_pipeline_report()
    
    def run_train_mode(self):
        """Training only mode"""
        logger.info("Running in TRAIN mode...")
        
        self.stage_5_train_secids_model()
        self.stage_6_train_unified_model()
        self.stage_7_run_master_pipeline()
        
        self.save_pipeline_report()
    
    def run_detect_live_mode(self, iface: str, duration: int = 60):
        """Live detection only mode"""
        logger.info("Running in LIVE DETECTION mode...")
        
        self.stage_1_verify_setup()
        self.stage_9_detect_live(duration)
        
        self.save_pipeline_report()
    
    def run_detect_batch_mode(self, input_file: Path):
        """Batch detection only mode"""
        logger.info("Running in BATCH DETECTION mode...")
        
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            return False
        
        self.stage_8_detect_batch(input_file)
        self.stage_10_analyze_results()
        
        self.save_pipeline_report()


def main():
    parser = argparse.ArgumentParser(
        description='SecIDS-CNN Pipeline Orchestrator - Unified Automation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python3 pipeline_orchestrator.py --mode full
  
  # Capture and analyze for 2 minutes
  python3 pipeline_orchestrator.py --mode capture --iface eth0 --duration 120
  
  # Train all models
  python3 pipeline_orchestrator.py --mode train
  
  # Live detection for 5 minutes
  python3 pipeline_orchestrator.py --mode detect-live --iface eth0 --duration 300
  
  # Analyze existing file
  python3 pipeline_orchestrator.py --mode detect-batch --input datasets/Test1.csv
        """
    )
    
    parser.add_argument('--mode', required=True,
                       choices=['full', 'capture', 'train', 'detect-live', 'detect-batch'],
                       help='Pipeline execution mode')
    parser.add_argument('--iface', default='eth0',
                       help='Network interface for capture/live detection (default: eth0)')
    parser.add_argument('--duration', type=int, default=120,
                       help='Duration in seconds for capture or live detection (default: 120)')
    parser.add_argument('--input', type=Path,
                       help='Input CSV file for batch detection')
    parser.add_argument('--window', type=float, default=10.0,
                       help='Window size for live detection (default: 10.0)')
    parser.add_argument('--interval', type=float, default=4.0,
                       help='Processing interval for live detection (default: 4.0)')
    parser.add_argument('--backend', choices=['tf', 'unified'], default='tf',
                       help='Model backend to use (default: tf)')
    parser.add_argument('--no-enhance', action='store_true',
                       help='Disable dataset enhancement')
    parser.add_argument('--no-unified', action='store_true',
                       help='Skip unified model training')
    
    args = parser.parse_args()
    
    # Create configuration
    config = PipelineConfig()
    config.capture_interface = args.iface
    config.capture_duration = args.duration
    config.window_size = args.window
    config.processing_interval = args.interval
    config.model_backend = args.backend
    config.enable_enhanced_features = not args.no_enhance
    config.train_unified_model = not args.no_unified
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(config)
    
    # Execute based on mode
    try:
        if args.mode == 'full':
            orchestrator.run_full_pipeline()
        elif args.mode == 'capture':
            orchestrator.run_capture_mode(args.duration, args.iface)
        elif args.mode == 'train':
            orchestrator.run_train_mode()
        elif args.mode == 'detect-live':
            orchestrator.run_detect_live_mode(args.iface, args.duration)
        elif args.mode == 'detect-batch':
            if not args.input:
                logger.error("--input required for detect-batch mode")
                sys.exit(1)
            orchestrator.run_detect_batch_mode(args.input)
    except KeyboardInterrupt:
        logger.info("\nPipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

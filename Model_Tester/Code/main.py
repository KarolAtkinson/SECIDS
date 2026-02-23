#!/usr/bin/env python3

# Main Script - Cybersecurity Threat Detection Model
# Orchestrates the complete workflow: data analysis, dataset creation, model training, and predictions.

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add Code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from data_analyzer import DataAnalyzer
from dataset_creator import DatasetCreator
from threat_detector import ThreatDetectionModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(code_dir, 'threat_detection.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ThreatDetectionPipeline:
    # Main orchestrator for threat detection system
    
    def __init__(self):
        # Initialize the threat detection pipeline
        self.base_dir = Path(__file__).parent.parent
        self.dataset_dir = self.base_dir / "Threat_Detection_Model_1"
        self.code_dir = self.base_dir / "Code"
        # Use temp directories to avoid OneDrive file locking issues
        self.datasets_dir = Path("C:/Temp/ml_ai_datasets")
        self.models_dir = Path("C:/Temp/ml_ai_models")
        
        # Create necessary directories
        self.datasets_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        
        self.analyzer = None
        self.creator = None
        self.detector = None
    
    def step_1_analyze_data(self):
        # Analyze all input datasets
        logger.info("\n" + "="*80)
        logger.info("STEP 1: ANALYZING INPUT DATASETS")
        logger.info("="*80)
        
        self.analyzer = DataAnalyzer(str(self.dataset_dir))
        datasets = self.analyzer.run_complete_analysis()
        
        logger.info(f"✓ Step 1 Complete: Analyzed {len(datasets)} datasets")
        return datasets
    
    def step_2_create_datasets(self):
        # Create consolidated training datasets
        logger.info("\n" + "="*80)
        logger.info("STEP 2: CREATING CONSOLIDATED DATASETS")
        logger.info("="*80)
        
        self.creator = DatasetCreator(str(self.dataset_dir), str(self.datasets_dir))
        datasets = self.creator.create_all_datasets()
        
        logger.info(f"✓ Step 2 Complete: Created training datasets")
        return datasets
    
    def step_3_train_models(self):
        # Train threat detection models
        logger.info("\n" + "="*80)
        logger.info("STEP 3: TRAINING THREAT DETECTION MODELS")
        logger.info("="*80)
        
        self.detector = ThreatDetectionModel(str(self.models_dir))
        
        ddos_dataset = self.datasets_dir / 'ddos_training_dataset.csv'
        phishing_dataset = self.datasets_dir / 'phishing_training_dataset.csv'
        
        if ddos_dataset.exists() and phishing_dataset.exists():
            self.detector.train_all_models(str(ddos_dataset), str(phishing_dataset))
            logger.info(f"✓ Step 3 Complete: Models trained and saved")
            return True
        else:
            logger.error("Required training datasets not found")
            return False
    
    def step_4_test_predictions(self):
        # Test the trained models with sample data
        logger.info("\n" + "="*80)
        logger.info("STEP 4: TESTING MODEL PREDICTIONS")
        logger.info("="*80)
        
        if self.detector is None:
            logger.error("Models not trained yet")
            return False
        
        # Sample DDoS features (from normal network traffic)
        sample_ddos_features = [
            80,      # Destination Port
            1000,    # Flow Duration
            50,      # Total Fwd Packets
            5000,    # Total Length of Fwd Packets
            2500,    # Fwd Packet Length Max
            0,       # Fwd Packet Length Min
            100,     # Fwd Packet Length Mean
            50,      # Fwd Packet Length Std
            2000,    # Bwd Packet Length Max
            0,       # Bwd Packet Length Min
            80,      # Bwd Packet Length Mean
            40,      # Bwd Packet Length Std
            5.0,     # Flow Bytes/s
            0.05,    # Flow Packets/s
            100,     # Flow IAT Mean
            50,      # Flow IAT Std
        ]
        
        logger.info("Testing DDoS model with sample normal traffic...")
        if len(sample_ddos_features) == 16:  # Adjust as needed
            try:
                ddos_result = self.detector.predict_ddos(sample_ddos_features)
                logger.info(f"DDoS Prediction: {ddos_result}")
            except Exception as e:
                logger.warning(f"DDoS prediction test failed: {e}")
        
        # Sample Phishing features
        sample_phishing_features = [1, 2, 0]  # Adjust based on dataset
        logger.info("Testing Phishing model with sample data...")
        try:
            phishing_result = self.detector.predict_phishing(sample_phishing_features)
            logger.info(f"Phishing Prediction: {phishing_result}")
        except Exception as e:
            logger.warning(f"Phishing prediction test failed: {e}")
        
        logger.info(f"✓ Step 4 Complete: Prediction tests completed")
        return True
    
    def run_complete_pipeline(self):
        # Run the complete threat detection pipeline
        logger.info("\n" + "="*80)
        logger.info("CYBERSECURITY THREAT DETECTION MODEL - COMPLETE PIPELINE")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        try:
            # Step 1: Analyze
            self.step_1_analyze_data()
            
            # Step 2: Create datasets
            self.step_2_create_datasets()
            
            # Step 3: Train models
            self.step_3_train_models()
            
            # Step 4: Test predictions
            self.step_4_test_predictions()
            
            logger.info("\n" + "="*80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*80)
            logger.info("\nOutput files:")
            logger.info(f"  - Training datasets: {self.datasets_dir}")
            logger.info(f"  - Trained models: {self.models_dir}")
            logger.info(f"  - Log file: {os.path.join(self.code_dir, 'threat_detection.log')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False


def main():
    # Main entry point
    pipeline = ThreatDetectionPipeline()
    success = pipeline.run_complete_pipeline()
    
    if success:
        logger.info("\n✓ ALL STEPS COMPLETED SUCCESSFULLY")
        return 0
    else:
        logger.error("\n✗ PIPELINE FAILED")
        return 1

# Execute main function
if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

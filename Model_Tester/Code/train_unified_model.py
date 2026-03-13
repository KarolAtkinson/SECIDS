#!/usr/bin/env python3
# Unified Model Training Pipeline
# Combines all datasets (SecIDS-CNN + Threat_Detection_Model_1)
# Trains a new ensemble model using DDOS training dataset parameters

import sys
import os
import logging
from pathlib import Path

# Setup paths
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from unified_threat_model import UnifiedThreatModel
from path_config import CODE_DIR, DATASETS_DIR, LOGS_DIR, MODELS_DIR, TRAINING_DATA_DIR, ensure_model_tester_dirs

ensure_model_tester_dirs()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'unified_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    logger.info("\n" + "="*80)
    logger.info("UNIFIED THREAT DETECTION MODEL - TRAINING PIPELINE")
    logger.info("="*80)
    logger.info("\nThis pipeline:")
    logger.info("  1. Loads datasets from SecIDS-CNN project (datasets/)")
    logger.info("  2. Loads existing datasets from Threat_Detection_Model_1/")
    logger.info("  3. Combines all datasets")
    logger.info("  4. Uses DDOS training dataset parameters for feature engineering")
    logger.info("  5. Trains an ensemble model (Random Forest + Gradient Boosting)")
    logger.info("  6. Evaluates performance and saves the model")
    logger.info("\n" + "="*80 + "\n")
    
    try:
        # Setup model directory
        base_path = CODE_DIR.parent
        model_dir = MODELS_DIR
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Dataset directories
        dataset_dirs = [
            DATASETS_DIR,
            TRAINING_DATA_DIR,
        ]
        
        logger.info("Dataset Directories:")
        for dataset_dir in dataset_dirs:
            logger.info(f"  - {dataset_dir}")
            if dataset_dir.exists():
                csv_count = len(list(dataset_dir.glob('*.csv')))
                logger.info(f"    (Contains {csv_count} CSV files)")
        logger.info("")
        
        # Initialize model
        unified_model = UnifiedThreatModel(
            model_dir=model_dir,
            dataset_dirs=dataset_dirs
        )
        
        # Train model
        logger.info("Starting model training...\n")
        model = unified_model.train_model(test_size=0.2, random_state=42)
        
        logger.info("\n" + "="*80)
        logger.info("✓ MODEL TRAINING COMPLETED SUCCESSFULLY!")
        logger.info("="*80)
        logger.info(f"\nModel saved to: {model_dir}")
        logger.info("\nTo use the trained model:")
        logger.info("  from unified_threat_model import UnifiedThreatModel")
        logger.info("  model = UnifiedThreatModel(model_dir)")
        logger.info("  predictions, probabilities = model.predict(X)")
        logger.info("\n" + "="*80 + "\n")
        
        return True
        
    except Exception as e:
        logger.error("\n" + "="*80)
        logger.error("✗ ERROR DURING MODEL TRAINING")
        logger.error("="*80)
        logger.error(f"\nError: {e}")
        
        import traceback
        logger.error("\nTraceback:")
        logger.error(traceback.format_exc())
        logger.error("\n" + "="*80 + "\n")
        
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

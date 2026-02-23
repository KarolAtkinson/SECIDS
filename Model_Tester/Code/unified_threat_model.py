#!/usr/bin/env python3
# Unified Threat Detection Model
# Combines multiple datasets from both the workspace and SecIDS-CNN project
# Uses parameters from ddos_training_dataset.csv for consistent feature engineering
# Trains an ensemble model for DDoS and intrusion detection

import pandas as pd
import numpy as np
import os
import logging
import pickle
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score, roc_auc_score, roc_curve, auc
)
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedThreatModel:
    """
    Unified threat detection model using multiple datasets
    Features based on ddos_training_dataset parameters:
    - Destination Port
    - Flow Duration
    - Total Fwd Packets
    - Total Length of Fwd Packets
    - Flow Bytes/s
    - Flow Packets/s
    - Average Packet Size
    - Packet Length Std
    - FIN Flag Count
    - ACK Flag Count
    """
    
    # Standard features from ddos_training_dataset
    DDOS_FEATURES = [
        'Destination Port',
        'Flow Duration',
        'Total Fwd Packets',
        'Total Length of Fwd Packets',
        'Flow Bytes/s',
        'Flow Packets/s',
        'Average Packet Size',
        'Packet Length Std',
        'FIN Flag Count',
        'ACK Flag Count'
    ]
    
    # Enhanced features for legitimacy detection (Test3 dataset)
    ENHANCED_FEATURES = [
        'Destination Port',
        'Flow Duration',
        'Total Fwd Packets',
        'Total Length of Fwd Packets',
        'Flow Bytes/s',
        'Flow Packets/s',
        'Average Packet Size',
        'Packet Length Std',
        'FIN Flag Count',
        'ACK Flag Count',
        'Source Is Private',
        'Destination Is Private',
        'Source Is Known Provider',
        'Destination Is Known Provider',
        'Is Bidirectional Flow',
        'Destination Port Is Legitimate',
        'IAT Mean',
        'IAT Std',
        'Legitimacy Score'
    ]
    
    # Alternative feature mappings for different datasets
    FEATURE_MAPPINGS = {
        'capture': {
            'dst_port': 'Destination Port',
            'duration': 'Flow Duration',
            'fwd_packets': 'Total Fwd Packets',
            'fwd_bytes': 'Total Length of Fwd Packets',
            'bytes_per_sec': 'Flow Bytes/s',
            'packets_per_sec': 'Flow Packets/s',
            'avg_packet_len': 'Average Packet Size',
            'pkt_len_std': 'Packet Length Std',
            'fin_flags': 'FIN Flag Count',
            'ack_flags': 'ACK Flag Count'
        }
    }
    
    def __init__(self, model_dir, dataset_dirs=None):
        """
        Initialize the unified threat model
        
        Args:
            model_dir: Directory to save trained models
            dataset_dirs: List of dataset directories to load from
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Default dataset directories
        if dataset_dirs is None:
            base_path = Path(__file__).parent.parent
            dataset_dirs = [
                base_path / "Code" / "datasets",  # New SecIDS-CNN datasets
                base_path / "Threat_Detection_Model_1"  # Existing datasets
            ]
        
        self.dataset_dirs = [Path(d) for d in dataset_dirs]
        
        # Model components
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.metrics = {}
        
        # Data storage
        self.combined_df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
        # Feature tracking
        self.numeric_features = []
        self.categorical_features = []
        
    def load_all_datasets(self):
        """Load and combine datasets from all configured directories"""
        logger.info("Loading datasets from all configured directories...")
        
        all_dataframes = []
        
        for dataset_dir in self.dataset_dirs:
            if not dataset_dir.exists():
                logger.warning(f"Dataset directory not found: {dataset_dir}")
                continue
                
            logger.info(f"\nLoading from {dataset_dir}")
            csv_files = list(dataset_dir.glob('*.csv'))
            
            for csv_file in csv_files:
                try:
                    # Skip result files
                    if '_results' in csv_file.name or 'Test_Results' in csv_file.name:
                        logger.info(f"  Skipping results file: {csv_file.name}")
                        continue
                    
                    df = pd.read_csv(csv_file, on_bad_lines='skip')
                    logger.info(f"  ✓ Loaded {csv_file.name}: {df.shape[0]} rows, {df.shape[1]} columns")
                    all_dataframes.append(df)
                    
                except Exception as e:
                    logger.error(f"  ✗ Error loading {csv_file.name}: {e}")
                    continue
        
        if not all_dataframes:
            raise ValueError("No datasets were successfully loaded")
        
        # Combine all dataframes
        self.combined_df = pd.concat(all_dataframes, ignore_index=True)
        logger.info(f"\n✓ Combined dataset shape: {self.combined_df.shape}")
        logger.info(f"  Total rows: {self.combined_df.shape[0]}")
        logger.info(f"  Total columns: {self.combined_df.shape[1]}")
        logger.info(f"\nColumn names in combined dataset:")
        for i, col in enumerate(self.combined_df.columns, 1):
            logger.info(f"  {i}. {col}")
        
        return self.combined_df
    
    def prepare_features(self, df, target_col=None):
        """
        Prepare features using standardized parameter set
        
        Args:
            df: Input dataframe
            target_col: Name of target column (auto-detected if None)
            
        Returns:
            Tuple of (X, y, feature_names)
        """
        logger.info("\nPreparing features...")
        
        # Auto-detect target column
        if target_col is None:
            target_candidates = ['is_ddos', 'is_attack', 'label', 'attack', 'class', 'target']
            target_col = None
            for candidate in target_candidates:
                if candidate.lower() in [col.lower() for col in df.columns]:
                    target_col = [col for col in df.columns if col.lower() == candidate.lower()][0]
                    break
        
        if target_col is None:
            logger.error("Could not auto-detect target column")
            logger.info("Available columns: " + ", ".join(df.columns))
            raise ValueError("Target column could not be determined")
        
        logger.info(f"Using target column: {target_col}")
        
        # Identify available features - try enhanced first, then fallback to standard
        available_features = []
        
        # Check if we have enhanced features
        enhanced_count = sum(1 for f in self.ENHANCED_FEATURES if f in df.columns)
        standard_count = sum(1 for f in self.DDOS_FEATURES if f in df.columns)
        
        if enhanced_count >= len(self.ENHANCED_FEATURES) - 2:  # Allow missing 2 features
            logger.info("Using ENHANCED feature set with legitimacy detection")
            for feature in self.ENHANCED_FEATURES:
                if feature in df.columns:
                    available_features.append(feature)
        elif standard_count >= len(self.DDOS_FEATURES) - 2:
            logger.info("Using STANDARD feature set")
            for feature in self.DDOS_FEATURES:
                if feature in df.columns:
                    available_features.append(feature)
        else:
            logger.warning("Neither enhanced nor standard features found, using all numeric columns")
            available_features = df.select_dtypes(include=[np.number]).columns.tolist()
            # Remove target if it's included
            if target_col in available_features:
                available_features.remove(target_col)
        
        logger.info(f"Using {len(available_features)} features:")
        for i, feat in enumerate(available_features, 1):
            logger.info(f"  {i}. {feat}")
        
        # Prepare X and y
        X = df[available_features].copy()
        y = df[target_col].copy()
        
        # Remove rows where target is NaN
        valid_mask = y.notna()
        X = X[valid_mask].copy()
        y = y[valid_mask].copy()
        
        logger.info(f"\nAfter removing NaN targets:")
        logger.info(f"  Removed {(~valid_mask).sum()} rows with NaN target")
        logger.info(f"  Kept {len(X)} rows with valid target values")
        
        # Handle missing values in features
        X = X.fillna(X.mean(numeric_only=True))
        
        # Handle infinite values
        X = X.replace([np.inf, -np.inf], 0)
        
        logger.info(f"\nFeature data prepared:")
        logger.info(f"  X shape: {X.shape}")
        logger.info(f"  y shape: {y.shape}")
        logger.info(f"  y value counts:\n{y.value_counts()}")
        
        return X, y, available_features
    
    def train_model(self, test_size=0.2, random_state=42):
        """
        Train the unified threat detection model
        
        Args:
            test_size: Test set proportion
            random_state: Random seed for reproducibility
        """
        logger.info("\n" + "="*80)
        logger.info("TRAINING UNIFIED THREAT DETECTION MODEL")
        logger.info("="*80)
        
        # Load and combine datasets
        combined_df = self.load_all_datasets()
        
        # Prepare features
        X, y, feature_names = self.prepare_features(combined_df)
        
        # Split data
        logger.info("\nSplitting data...")
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        logger.info(f"  Training set: {self.X_train.shape[0]} samples")
        logger.info(f"  Test set: {self.X_test.shape[0]} samples")
        
        # Scale features
        logger.info("\nScaling features...")
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(self.X_train)
        X_test_scaled = self.scaler.transform(self.X_test)
        
        # Train ensemble model
        logger.info("\nTraining ensemble model...")
        logger.info("  Model: Random Forest + Gradient Boosting ensemble")
        
        # Base models
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1,
            class_weight='balanced'
        )
        
        gb_model = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            subsample=0.8
        )
        
        # Train base models
        logger.info("  Training Random Forest...")
        rf_model.fit(X_train_scaled, self.y_train)
        
        logger.info("  Training Gradient Boosting...")
        gb_model.fit(X_train_scaled, self.y_train)
        
        # Create ensemble predictions (average of probabilities)
        rf_proba = rf_model.predict_proba(X_test_scaled)[:, 1]
        gb_proba = gb_model.predict_proba(X_test_scaled)[:, 1]
        ensemble_proba = (rf_proba + gb_proba) / 2
        self.y_pred = (ensemble_proba >= 0.5).astype(int)
        
        # Store models for later use
        self.model = {
            'rf': rf_model,
            'gb': gb_model,
            'ensemble_proba': ensemble_proba
        }
        
        # Evaluate
        self._evaluate_model(X_train_scaled, X_test_scaled, feature_names)
        
        # Save model
        self._save_model(feature_names)
        
        return self.model
    
    def _evaluate_model(self, X_train_scaled, X_test_scaled, feature_names):
        """Evaluate model performance"""
        logger.info("\n" + "="*80)
        logger.info("MODEL EVALUATION")
        logger.info("="*80)
        
        # Calculate metrics
        accuracy = accuracy_score(self.y_test, self.y_pred)
        precision = precision_score(self.y_test, self.y_pred, zero_division=0)
        recall = recall_score(self.y_test, self.y_pred, zero_division=0)
        f1 = f1_score(self.y_test, self.y_pred, zero_division=0)
        
        # ROC-AUC
        if len(np.unique(self.y_test)) > 1:
            roc_auc = roc_auc_score(self.y_test, self.model['ensemble_proba'])  # type: ignore
        else:
            roc_auc = 0.0
        
        self.metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc
        }
        
        logger.info(f"\nPerformance Metrics:")
        logger.info(f"  Accuracy:  {accuracy:.4f}")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall:    {recall:.4f}")
        logger.info(f"  F1-Score:  {f1:.4f}")
        logger.info(f"  ROC-AUC:   {roc_auc:.4f}")
        
        # Classification report
        logger.info(f"\nDetailed Classification Report:")
        logger.info("\n" + classification_report(self.y_test, self.y_pred, zero_division=0))
        
        # Confusion matrix
        cm = confusion_matrix(self.y_test, self.y_pred)
        logger.info(f"\nConfusion Matrix:")
        logger.info(f"  True Negatives:  {cm[0, 0]}")
        logger.info(f"  False Positives: {cm[0, 1]}")
        logger.info(f"  False Negatives: {cm[1, 0]}")
        logger.info(f"  True Positives:  {cm[1, 1]}")
        
        # Feature importance (from Random Forest)
        logger.info(f"\nTop 10 Most Important Features:")
        rf_model = self.model['rf']  # type: ignore
        importances = rf_model.feature_importances_
        feature_importance = list(zip(feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        for i, (feature, importance) in enumerate(feature_importance[:10], 1):
            logger.info(f"  {i:2d}. {feature:40s} {importance:.4f}")
    
    def _save_model(self, feature_names):
        """Save trained model and metadata"""
        logger.info("\n" + "="*80)
        logger.info("SAVING MODEL")
        logger.info("="*80)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save models
        model_path = os.path.join(self.model_dir, f"unified_threat_model_{timestamp}.pkl")
        scaler_path = os.path.join(self.model_dir, f"unified_scaler_{timestamp}.pkl")
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"  ✓ Model saved: {model_path}")
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        logger.info(f"  ✓ Scaler saved: {scaler_path}")
        
        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'feature_names': feature_names,
            'n_features': len(feature_names),
            'metrics': self.metrics,
            'training_samples': len(self.X_train),
            'test_samples': len(self.X_test),
            'feature_set': 'DDOS_FEATURES_FROM_DDOS_TRAINING_DATASET'
        }
        
        metadata_path = os.path.join(self.model_dir, f"unified_metadata_{timestamp}.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        logger.info(f"  ✓ Metadata saved: {metadata_path}")
        
        # Save metrics summary
        metrics_path = os.path.join(self.model_dir, f"unified_metrics_{timestamp}.txt")
        with open(metrics_path, 'w') as f:
            f.write("UNIFIED THREAT DETECTION MODEL - METRICS SUMMARY\n")
            f.write("="*80 + "\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Training Samples: {metadata['training_samples']}\n")
            f.write(f"Test Samples: {metadata['test_samples']}\n")
            f.write(f"Features Used: {metadata['n_features']}\n")
            f.write(f"\nFeatures:\n")
            for i, feat in enumerate(feature_names, 1):
                f.write(f"  {i}. {feat}\n")
            f.write(f"\nPerformance Metrics:\n")
            for metric, value in self.metrics.items():
                f.write(f"  {metric}: {value:.4f}\n")
        logger.info(f"  ✓ Metrics summary saved: {metrics_path}")
    
    def predict(self, X):
        """
        Make predictions using the trained model
        
        Args:
            X: Features dataframe
            
        Returns:
            Predictions array
        """
        if self.scaler is None or self.model is None:
            raise ValueError("Model has not been trained yet")
        
        X_scaled = self.scaler.transform(X)
        rf_proba = self.model['rf'].predict_proba(X_scaled)[:, 1]
        gb_proba = self.model['gb'].predict_proba(X_scaled)[:, 1]
        ensemble_proba = (rf_proba + gb_proba) / 2
        
        return (ensemble_proba >= 0.5).astype(int), ensemble_proba


def main():
    """Main execution function"""
    logger.info("Initializing Unified Threat Detection Model...")
    
    # Setup paths
    base_path = Path(__file__).parent.parent
    model_dir = base_path / "Code" / "models"
    
    # Initialize and train model
    unified_model = UnifiedThreatModel(model_dir=model_dir)
    
    try:
        unified_model.train_model(test_size=0.2)
        logger.info("\n✓ Model training completed successfully!")
    except Exception as e:
        logger.error(f"✗ Error during model training: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

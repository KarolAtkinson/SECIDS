#!/usr/bin/env python3
# Threat Detection Model
# Trains and evaluates machine learning models for DDoS and Phishing threat detection.

import pandas as pd
import numpy as np
import os
import logging
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score, roc_auc_score, roc_curve
)
from sklearn.linear_model import LogisticRegression
import warnings
# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThreatDetectionModel:
    # Machine Learning model for threat detection
    
    def __init__(self, model_dir):
        """
         # Initialize threat detection model
        
        Args:
            model_dir: Directory to save trained models
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        self.ddos_model = None
        self.phishing_model = None
        self.ddos_scaler = None
        self.phishing_scaler = None
        self.ddos_metrics = {}
        self.phishing_metrics = {}
    
    def prepare_data(self, df, target_col, test_size=0.2):
        """
        Prepare data for model training
        
        Args:
            df: DataFrame with features and target
            target_col: Name of target column
            test_size: Test set size ratio
            
        Returns:
            Prepared data tuple (X_train, X_test, y_train, y_test, scaler)
        """
        # Separate features and target
        y = df[target_col].copy()
        X = df.drop(target_col, axis=1).copy()
        
        # Handle non-numeric columns
        for col in X.columns:
            if X[col].dtype == 'object':
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        
        # Fill missing values
        X = X.fillna(X.mean(numeric_only=True))
        X = X.replace([np.inf, -np.inf], 0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        logger.info(f"Data prepared: {X_train_scaled.shape[0]} training, {X_test_scaled.shape[0]} testing samples")
        
        return X_train_scaled, X_test_scaled, y_train, y_test, scaler
    
    def train_ddos_model(self, dataset_path):
        # Train DDoS detection model
        logger.info("\n" + "="*70)
        logger.info("TRAINING DDoS DETECTION MODEL")
        logger.info("="*70)
        
        if not os.path.exists(dataset_path):
            logger.error(f"Dataset not found: {dataset_path}")
            return False
        
        logger.info(f"Loading dataset from {dataset_path}")
        df = pd.read_csv(dataset_path)
        logger.info(f"Dataset shape: {df.shape}")
        
        # Prepare data
        logger.info("Preparing data...")
        X_train, X_test, y_train, y_test, scaler = self.prepare_data(df, 'is_ddos')
        
        # Train multiple models and use ensemble
        logger.info("Training Random Forest model...")
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
        rf_model.fit(X_train, y_train)
        
        logger.info("Training Gradient Boosting model...")
        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
            verbose=0
        )
        gb_model.fit(X_train, y_train)
        
        # Ensemble predictions
        rf_pred = rf_model.predict(X_test)
        gb_pred = gb_model.predict(X_test)
        y_pred = (rf_pred + gb_pred) >= 1  # Majority voting
        
        # Evaluate
        logger.info("\nModel Evaluation:")
        self.ddos_metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0)
        }
        
        for metric, value in self.ddos_metrics.items():
            logger.info(f"  {metric.upper()}: {value:.4f}")
        
        logger.info("\nDetailed Classification Report:")
        logger.info(classification_report(y_test, y_pred))
        
        # Save models
        self.ddos_model = {
            'rf_model': rf_model,
            'gb_model': gb_model,
            'feature_names': list(X_train.T) if hasattr(X_train, 'T') else list(range(X_train.shape[1]))
        }
        self.ddos_scaler = scaler
        
        self._save_model('ddos', rf_model, gb_model, scaler)
        
        return True
    
    def train_phishing_model(self, dataset_path):
        # Train Phishing detection model
        logger.info("\n" + "="*70)
        logger.info("TRAINING PHISHING DETECTION MODEL")
        logger.info("="*70)
        
        if not os.path.exists(dataset_path):
            logger.error(f"Dataset not found: {dataset_path}")
            return False
        
        logger.info(f"Loading dataset from {dataset_path}")
        df = pd.read_csv(dataset_path)
        logger.info(f"Dataset shape: {df.shape}")
        
        # Check if we have the target column
        if 'is_phishing' not in df.columns:
            logger.warning("'is_phishing' column not found, creating synthetic labels")
            df['is_phishing'] = np.random.choice([0, 1], size=len(df), p=[0.7, 0.3])
        
        # Create balanced dataset by duplicating and adding synthetic negative examples
        logger.info("Balancing dataset...")
        phishing_count = (df['is_phishing'] == 1).sum()
        if phishing_count > 0:
            # Create synthetic normal traffic examples
            phishing_df = df[df['is_phishing'] == 1].copy()
            normal_df = df[df['is_phishing'] == 0].copy()
            
            # If we don't have enough normal examples, create synthetic ones
            if len(normal_df) < phishing_count:
                synthetic_normal = phishing_df.copy()
                synthetic_normal['is_phishing'] = 0
                df = pd.concat([phishing_df, normal_df, synthetic_normal], ignore_index=True)
            elif len(normal_df) > phishing_count * 2:
                normal_df = normal_df.sample(phishing_count * 2, random_state=42)
                df = pd.concat([phishing_df, normal_df], ignore_index=True)
        
        logger.info(f"Balanced dataset shape: {df.shape}")
        logger.info(f"Phishing samples: {(df['is_phishing'] == 1).sum()}, Normal samples: {(df['is_phishing'] == 0).sum()}")
        
        # Prepare data
        logger.info("Preparing data...")
        X_train, X_test, y_train, y_test, scaler = self.prepare_data(df, 'is_phishing')
        
        # Train models
        logger.info("Training Logistic Regression model...")
        lr_model = LogisticRegression(max_iter=1000, random_state=42)
        lr_model.fit(X_train, y_train)
        
        logger.info("Training Random Forest model...")
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        
        # Ensemble predictions
        lr_pred = lr_model.predict(X_test)
        rf_pred = rf_model.predict(X_test)
        y_pred = (lr_pred + rf_pred) >= 1  # Majority voting
        
        # Evaluate
        logger.info("\nModel Evaluation:")
        self.phishing_metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0)
        }
        
        for metric, value in self.phishing_metrics.items():
            logger.info(f"  {metric.upper()}: {value:.4f}")
        
        logger.info("\nDetailed Classification Report:")
        logger.info(classification_report(y_test, y_pred))
        
        # Save models
        self.phishing_model = {
            'lr_model': lr_model,
            'rf_model': rf_model,
            'feature_names': list(range(X_train.shape[1]))
        }
        self.phishing_scaler = scaler
        
        self._save_model('phishing', lr_model, rf_model, scaler)
        
        return True
    
    def _save_model(self, threat_type, model1, model2, scaler):
        # Save trained models to disk
        model_path = os.path.join(self.model_dir, f'{threat_type}_model.pkl')
        scaler_path = os.path.join(self.model_dir, f'{threat_type}_scaler.pkl')
        
        with open(model_path, 'wb') as f:
            pickle.dump({'model1': model1, 'model2': model2}, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        
        logger.info(f"✓ Saved {threat_type} models to {model_path}")
        logger.info(f"✓ Saved {threat_type} scaler to {scaler_path}")
    
    def predict_ddos(self, features):
        # Predict if traffic is DDoS attack
        if self.ddos_model is None:
            logger.error("DDoS model not trained")
            return None
        
        scaled_features = self.ddos_scaler.transform([features])  # type: ignore
        rf_pred = self.ddos_model['rf_model'].predict(scaled_features)[0]
        gb_pred = self.ddos_model['gb_model'].predict(scaled_features)[0]
        
        prediction = 1 if (rf_pred + gb_pred) >= 1 else 0
        confidence = self.ddos_model['rf_model'].predict_proba(scaled_features)[0][prediction]
        
        return {
            'is_ddos': prediction,
            'confidence': confidence,
            'threat_level': 'HIGH' if prediction and confidence > 0.7 else 'MEDIUM' if prediction else 'LOW'
        }
    
    def predict_phishing(self, features):
        # Predict if communication is phishing attack
        if self.phishing_model is None:
            logger.error("Phishing model not trained")
            return None
        
        scaled_features = self.phishing_scaler.transform([features])  # type: ignore
        lr_pred = self.phishing_model['lr_model'].predict(scaled_features)[0]
        rf_pred = self.phishing_model['rf_model'].predict(scaled_features)[0]
        
        prediction = 1 if (lr_pred + rf_pred) >= 1 else 0
        confidence = self.phishing_model['rf_model'].predict_proba(scaled_features)[0][prediction]
        
        return {
            'is_phishing': prediction,
            'confidence': confidence,
            'threat_level': 'HIGH' if prediction and confidence > 0.7 else 'MEDIUM' if prediction else 'LOW'
        }
    
    def train_all_models(self, ddos_dataset_path, phishing_dataset_path):
        # Train all threat detection models
        logger.info("\n" + "="*70)
        logger.info("TRAINING ALL THREAT DETECTION MODELS")
        logger.info("="*70)
        
        self.train_ddos_model(ddos_dataset_path)
        self.train_phishing_model(phishing_dataset_path)
        
        logger.info("\n" + "="*70)
        logger.info("ALL MODELS TRAINED SUCCESSFULLY")
        logger.info("="*70)

# Execute main function
if __name__ == "__main__":
    dataset_dir = r"c:\Users\karol\OneDrive\Pulpit\Master ML_AI\Code\datasets"
    model_dir = r"c:\Users\karol\OneDrive\Pulpit\Master ML_AI\Code\models"
    
    threat_detector = ThreatDetectionModel(model_dir)
    
    ddos_dataset = os.path.join(dataset_dir, 'ddos_training_dataset.csv')
    phishing_dataset = os.path.join(dataset_dir, 'phishing_training_dataset.csv')
    
    threat_detector.train_all_models(ddos_dataset, phishing_dataset)

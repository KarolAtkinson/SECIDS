#!/usr/bin/env python3

# Dataset Creator Module
# Creates consolidated training dataset for DDoS and Phishing threat detection.
# Processes raw datasets and engineers relevant features.


import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatasetCreator:
    # Creates consolidated training datasets for threat detection
    
    def __init__(self, dataset_dir, output_dir):
        
        # Initialize dataset creator
        
        # Args:
           # dataset_dir: Path to raw datasets
           # output_dir: Path to save created datasets
        self.dataset_dir = dataset_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def extract_ddos_features(self):
        # Extract DDoS features from network traffic data
        logger.info("\n" + "="*70)
        logger.info("EXTRACTING DDoS FEATURES FROM CICIDS2017")
        logger.info("="*70)
        
        cicids_path = os.path.join(self.dataset_dir, 'cicids2017_cleaned.csv')
        
        if not os.path.exists(cicids_path):
            logger.error(f"CICIDs2017 file not found: {cicids_path}")
            return None
        
        logger.info("Loading CICIDs2017 network traffic data...")
        df = pd.read_csv(cicids_path, on_bad_lines='skip')
        
        logger.info(f"Original shape: {df.shape}")
        
        # Select relevant features for DDoS detection
        feature_cols = [
            'Destination Port', 'Flow Duration', 'Total Fwd Packets',
            'Total Length of Fwd Packets', 'Total Backward Packets',
            'Flow Bytes/s', 'Flow Packets/s', 'Average Packet Size',
            'Packet Length Std', 'FIN Flag Count', 'SYN Flag Count',
            'RST Flag Count', 'ACK Flag Count'
        ]
        
        # Keep only available columns
        available_cols = [col for col in feature_cols if col in df.columns]
        logger.info(f"Using {len(available_cols)} features: {available_cols}")
        
        ddos_df = df[available_cols + ['Attack Type']].copy() if 'Attack Type' in df.columns else df[available_cols].copy()
        
        # Add label: 1 for DDoS, 0 for Normal
        if 'Attack Type' in ddos_df.columns:
            ddos_df['is_ddos'] = ddos_df['Attack Type'].str.contains('DDoS', case=False, na=False).astype(int)
            ddos_df = ddos_df.drop('Attack Type', axis=1)
        else:
            ddos_df['is_ddos'] = 0
        
        # Fill missing values
        ddos_df = ddos_df.fillna(ddos_df.mean(numeric_only=True))
        
        # Handle infinite values
        ddos_df = ddos_df.replace([np.inf, -np.inf], 0)
        
        logger.info(f"DDoS dataset shape: {ddos_df.shape}")
        logger.info(f"DDoS samples: {(ddos_df['is_ddos'] == 1).sum()}")
        logger.info(f"Normal samples: {(ddos_df['is_ddos'] == 0).sum()}")
        
        # Sample for balanced dataset
        normal_samples = ddos_df[ddos_df['is_ddos'] == 0]
        ddos_samples = ddos_df[ddos_df['is_ddos'] == 1]
        
        # Take samples to create balanced dataset
        sample_size = min(10000, len(normal_samples), len(ddos_samples) * 2)
        balanced_ddos = pd.concat([
            normal_samples.sample(min(sample_size, len(normal_samples)), random_state=42),
            ddos_samples.sample(min(sample_size//2, len(ddos_samples)), random_state=42)
        ])
        
        balanced_ddos = balanced_ddos.sample(frac=1, random_state=42).reset_index(drop=True)
        logger.info(f"Balanced DDoS dataset shape: {balanced_ddos.shape}")
        
        return balanced_ddos
    
    def extract_phishing_features(self):
        # Extract Phishing features from multiple sources
        logger.info("\n" + "="*70)
        logger.info("EXTRACTING PHISHING FEATURES")
        logger.info("="*70)
        
        global_threats_path = os.path.join(self.dataset_dir, 'Global_Cybersecurity_Threats_2015-2024.csv')
        attacks_path = os.path.join(self.dataset_dir, 'cybersecurity_attacks.csv')
        
        phishing_data = []
        
        # Extract from Global Cybersecurity Threats
        if os.path.exists(global_threats_path):
            logger.info("Processing Global Cybersecurity Threats data...")
            df_global = pd.read_csv(global_threats_path, on_bad_lines='skip')
            
            # Filter for phishing attacks
            phishing_global = df_global[
                df_global['Attack Type'].str.contains('Phishing', case=False, na=False)
            ].copy()
            
            logger.info(f"Found {len(phishing_global)} phishing records")
            
            phishing_global['threat_type'] = 'phishing'
            phishing_global['financial_loss_million_usd'] = phishing_global.get('Financial Loss (in Million $)', 0)
            phishing_global['affected_users'] = phishing_global.get('Number of Affected Users', 0)
            phishing_global['year'] = phishing_global['Year']
            
            phishing_data.append(phishing_global)
        
        # Extract from detailed attacks
        if os.path.exists(attacks_path):
            logger.info("Processing detailed attacks data...")
            df_attacks = pd.read_csv(attacks_path, on_bad_lines='skip')
            
            phishing_attacks = df_attacks[
                df_attacks['Attack Type'].str.contains('Phishing', case=False, na=False)
            ].copy() if 'Attack Type' in df_attacks.columns else pd.DataFrame()
            
            if len(phishing_attacks) > 0:
                logger.info(f"Found {len(phishing_attacks)} detailed phishing records")
                phishing_attacks['threat_type'] = 'phishing'
                phishing_data.append(phishing_attacks)
        
        # Combine phishing data
        if phishing_data:
            phishing_df = pd.concat(phishing_data, ignore_index=True, sort=False)
            
            # Create features
            feature_df = pd.DataFrame({
                'threat_type': phishing_df.get('threat_type', 'phishing'),
                'severity_indicator': phishing_df['Severity Level'].map({'High': 3, 'Medium': 2, 'Low': 1, 'Critical': 4}).fillna(1) if 'Severity Level' in phishing_df.columns else 2,
                'is_phishing': 1
            })
            
            # Sample to 10000
            if len(feature_df) > 10000:
                feature_df = feature_df.sample(10000, random_state=42)
            
            logger.info(f"Phishing dataset shape: {feature_df.shape}")
            return feature_df
        
        logger.warning("No phishing data found")
        return None
    
    def extract_intrusion_features(self):
        # Extract intrusion detection features
        logger.info("\n" + "="*70)
        logger.info("EXTRACTING INTRUSION DETECTION FEATURES")
        logger.info("="*70)
        
        intrusion_path = os.path.join(self.dataset_dir, 'cybersecurity_intrusion_data.csv')
        
        if not os.path.exists(intrusion_path):
            logger.warning(f"Intrusion data not found: {intrusion_path}")
            return None
        
        df = pd.read_csv(intrusion_path, on_bad_lines='skip')
        logger.info(f"Intrusion data shape: {df.shape}")
        
        # Select relevant features
        feature_cols = [
            'network_packet_size', 'login_attempts', 'session_duration',
            'failed_logins', 'unusual_time_access', 'ip_reputation_score'
        ]
        
        available_cols = [col for col in feature_cols if col in df.columns]
        intrusion_df = df[available_cols + ['attack_detected']].copy() if 'attack_detected' in df.columns else df[available_cols].copy()
        
        # Fill missing values
        intrusion_df = intrusion_df.fillna(intrusion_df.mean(numeric_only=True))
        
        if 'attack_detected' in intrusion_df.columns:
            intrusion_df = intrusion_df.rename(columns={'attack_detected': 'is_attack'})
        else:
            intrusion_df['is_attack'] = 0
        
        logger.info(f"Intrusion dataset shape: {intrusion_df.shape}")
        logger.info(f"Attack samples: {(intrusion_df['is_attack'] == 1).sum()}")
        
        return intrusion_df
    
    def create_consolidated_ddos_dataset(self):
        # Create final consolidated DDoS training dataset
        logger.info("\n" + "="*70)
        logger.info("CREATING CONSOLIDATED DDoS DATASET")
        logger.info("="*70)
        
        ddos_df = self.extract_ddos_features()
        
        if ddos_df is not None:
            output_path = os.path.join(self.output_dir, 'ddos_training_dataset.csv')
            ddos_df.to_csv(output_path, index=False)
            logger.info(f"✓ Saved DDoS dataset to {output_path}")
            logger.info(f"  Shape: {ddos_df.shape}")
            logger.info(f"  Columns: {list(ddos_df.columns)}")
            return ddos_df
        
        return None
    
    def create_consolidated_phishing_dataset(self):
        # Create final consolidated Phishing training dataset
        logger.info("\n" + "="*70)
        logger.info("CREATING CONSOLIDATED PHISHING DATASET")
        logger.info("="*70)
        
        phishing_df = self.extract_phishing_features()
        
        if phishing_df is not None:
            output_path = os.path.join(self.output_dir, 'phishing_training_dataset.csv')
            phishing_df.to_csv(output_path, index=False)
            logger.info(f"✓ Saved Phishing dataset to {output_path}")
            logger.info(f"  Shape: {phishing_df.shape}")
            logger.info(f"  Columns: {list(phishing_df.columns)}")
            return phishing_df
        
        return None
    
    def create_consolidated_intrusion_dataset(self):
        # Create final consolidated Intrusion detection dataset
        logger.info("\n" + "="*70)
        logger.info("CREATING CONSOLIDATED INTRUSION DATASET")
        logger.info("="*70)
        
        intrusion_df = self.extract_intrusion_features()
        
        if intrusion_df is not None:
            output_path = os.path.join(self.output_dir, 'intrusion_training_dataset.csv')
            intrusion_df.to_csv(output_path, index=False)
            logger.info(f"✓ Saved Intrusion dataset to {output_path}")
            logger.info(f"  Shape: {intrusion_df.shape}")
            logger.info(f"  Columns: {list(intrusion_df.columns)}")
            return intrusion_df
        
        return None
    
    def create_all_datasets(self):
        # Create all consolidated datasets
        logger.info("\n" + "="*70)
        logger.info("STARTING DATASET CREATION PROCESS")
        logger.info("="*70)
        
        datasets = {
            'ddos': self.create_consolidated_ddos_dataset(),
            'phishing': self.create_consolidated_phishing_dataset(),
            'intrusion': self.create_consolidated_intrusion_dataset()
        }
        
        logger.info("\n" + "="*70)
        logger.info("DATASET CREATION COMPLETE")
        logger.info("="*70)
        
        return datasets

# Example usage
if __name__ == "__main__":
    from path_config import DATASETS_DIR, TRAINING_DATA_DIR, ensure_model_tester_dirs

    ensure_model_tester_dirs()
    dataset_dir = str(TRAINING_DATA_DIR)
    output_dir = str(DATASETS_DIR)
    
    creator = DatasetCreator(dataset_dir, output_dir)
    datasets = creator.create_all_datasets()

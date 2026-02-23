#!/usr/bin/env python3

# Data Analyzer Module
# Analyzes all datasets from Threat_Detection_Model_1 directory and extracts relevant threat information.
# Focuses on DDoS and Phishing attack patterns.


import pandas as pd
import numpy as np
import os
import warnings
from pathlib import Path
import logging

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataAnalyzer:
    # Analyzes cybersecurity threat datasets
    
    def __init__(self, dataset_dir):
        
        # Initialize the data analyzer
        
        # Args:
            # Dataset_dir: Path to directory containing CSV files
        
        self.dataset_dir = dataset_dir
        self.datasets = {}
        self.analysis_results = {}
        
    def load_all_datasets(self):
        # Load all CSV files from the dataset directory
        logger.info(f"Loading datasets from {self.dataset_dir}")
        
        csv_files = [f for f in os.listdir(self.dataset_dir) if f.endswith('.csv')]
        logger.info(f"Found {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            file_path = os.path.join(self.dataset_dir, csv_file)
            try:
                df = pd.read_csv(file_path, on_bad_lines='skip')
                self.datasets[csv_file] = df
                logger.info(f"✓ Loaded {csv_file}: {df.shape[0]} rows, {df.shape[1]} columns")
            except Exception as e:
                logger.warning(f"✗ Failed to load {csv_file}: {e}")
    
    def analyze_cicids2017(self):
        # Analyze CICIDs2017 network traffic data - excellent for DDoS detection
        logger.info("\n" + "="*70)
        logger.info("ANALYZING: CICIDs2017 Network Traffic Data (Best for DDoS)")
        logger.info("="*70)
        
        if 'cicids2017_cleaned.csv' not in self.datasets:
            logger.warning("CICIDs2017 dataset not found")
            return None
        
        df = self.datasets['cicids2017_cleaned.csv'].copy()
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Analyze attack types
        if 'Attack Type' in df.columns:
            attack_counts = df['Attack Type'].value_counts()
            logger.info(f"\nAttack Type Distribution:")
            for attack_type, count in attack_counts.items():
                logger.info(f"  - {attack_type}: {count} ({count/len(df)*100:.2f}%)")
        
        # Network flow statistics
        flow_cols = ['Total Fwd Packets', 'Total Backward Packets', 'Flow Duration', 'Flow Bytes/s']
        existing_cols = [col for col in flow_cols if col in df.columns]
        if existing_cols:
            logger.info(f"\nNetwork Flow Statistics:")
            for col in existing_cols:
                if col in df.columns:
                    logger.info(f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}")
        
        return df
    
    def analyze_global_cybersecurity_threats(self):
        # Analyze Global Cybersecurity Threats - good for Phishing and other attacks
        logger.info("\n" + "="*70)
        logger.info("ANALYZING: Global Cybersecurity Threats (Good for Phishing)")
        logger.info("="*70)
        
        if 'Global_Cybersecurity_Threats_2015-2024.csv' not in self.datasets:
            logger.warning("Global Cybersecurity Threats dataset not found")
            return None
        
        df = self.datasets['Global_Cybersecurity_Threats_2015-2024.csv'].copy()
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Years covered: {df['Year'].min()} to {df['Year'].max()}")
        
        # Attack type distribution
        if 'Attack Type' in df.columns:
            attack_counts = df['Attack Type'].value_counts()
            logger.info(f"\nAttack Type Distribution:")
            for attack_type, count in attack_counts.head(10).items():
                logger.info(f"  - {attack_type}: {count} ({count/len(df)*100:.2f}%)")
            
            # Identify Phishing and DDoS
            ddos_attacks = df[df['Attack Type'].str.contains('DDoS', case=False, na=False)]
            phishing_attacks = df[df['Attack Type'].str.contains('Phishing', case=False, na=False)]
            logger.info(f"\nTarget Threat Types:")
            logger.info(f"  - DDoS attacks: {len(ddos_attacks)}")
            logger.info(f"  - Phishing attacks: {len(phishing_attacks)}")
        
        # Industry targets
        if 'Target Industry' in df.columns:
            industry_counts = df['Target Industry'].value_counts()
            logger.info(f"\nMost Targeted Industries:")
            for industry, count in industry_counts.head(5).items():
                logger.info(f"  - {industry}: {count}")
        
        return df
    
    def analyze_cybersecurity_attacks(self):
        """Analyze detailed cybersecurity attacks"""
        logger.info("\n" + "="*70)
        logger.info("ANALYZING: Detailed Cybersecurity Attacks")
        logger.info("="*70)
        
        if 'cybersecurity_attacks.csv' not in self.datasets:
            logger.warning("Cybersecurity attacks dataset not found")
            return None
        
        df = self.datasets['cybersecurity_attacks.csv'].copy()
        logger.info(f"Dataset shape: {df.shape}")
        
        # Attack types
        if 'Attack Type' in df.columns:
            attack_counts = df['Attack Type'].value_counts()
            logger.info(f"\nAttack Type Distribution:")
            for attack_type, count in attack_counts.head(10).items():
                logger.info(f"  - {attack_type}: {count}")
        
        # Severity levels
        if 'Severity Level' in df.columns:
            severity_counts = df['Severity Level'].value_counts()
            logger.info(f"\nSeverity Distribution:")
            for severity, count in severity_counts.items():
                logger.info(f"  - {severity}: {count}")
        
        return df
    
    def analyze_intrusion_data(self):
        # Analyze intrusion detection data
        logger.info("\n" + "="*70)
        logger.info("ANALYZING: Cybersecurity Intrusion Data")
        logger.info("="*70)
        
        if 'cybersecurity_intrusion_data.csv' not in self.datasets:
            logger.warning("Intrusion data not found")
            return None
        
        df = self.datasets['cybersecurity_intrusion_data.csv'].copy()
        logger.info(f"Dataset shape: {df.shape}")
        
        if 'attack_detected' in df.columns:
            attack_distribution = df['attack_detected'].value_counts()
            logger.info(f"\nAttack Detection Distribution:")
            for attack_label, count in attack_distribution.items():
                logger.info(f"  - {attack_label}: {count} ({count/len(df)*100:.2f}%)")
        
        # Session statistics
        if 'session_duration' in df.columns:
            logger.info(f"\nSession Duration Statistics:")
            logger.info(f"  - Min: {df['session_duration'].min():.2f}")
            logger.info(f"  - Max: {df['session_duration'].max():.2f}")
            logger.info(f"  - Mean: {df['session_duration'].mean():.2f}")
        
        return df
    
    def analyze_india_cases(self):
        # Analyze India cybersecurity cases
        logger.info("\n" + "="*70)
        logger.info("ANALYZING: India Cybersecurity Cases")
        logger.info("="*70)
        
        if 'cybersecurity_cases_india_combined.csv' not in self.datasets:
            logger.warning("India cases dataset not found")
            return None
        
        df = self.datasets['cybersecurity_cases_india_combined.csv'].copy()
        logger.info(f"Dataset shape: {df.shape}")
        
        if 'Incident_Type' in df.columns:
            incident_counts = df['Incident_Type'].value_counts()
            logger.info(f"\nIncident Type Distribution:")
            for incident_type, count in incident_counts.items():
                logger.info(f"  - {incident_type}: {count}")
        
        if 'Amount_Lost_INR' in df.columns:
            logger.info(f"\nFinancial Loss (INR):")
            logger.info(f"  - Total: ₹{df['Amount_Lost_INR'].sum():,.0f}")
            logger.info(f"  - Average: ₹{df['Amount_Lost_INR'].mean():,.0f}")
        
        return df
    
    def run_complete_analysis(self):
        # Run analysis on all datasets
        logger.info("\n" + "="*70)
        logger.info("STARTING COMPLETE DATASET ANALYSIS")
        logger.info("="*70)
        
        self.load_all_datasets()
        
        # Analyze each dataset
        self.analyze_cicids2017()
        self.analyze_global_cybersecurity_threats()
        self.analyze_cybersecurity_attacks()
        self.analyze_intrusion_data()
        self.analyze_india_cases()
        
        logger.info("\n" + "="*70)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*70)
        
        return self.datasets

# Example usage
if __name__ == "__main__":
    dataset_dir = r"c:\Users\karol\OneDrive\Pulpit\Master ML_AI\Threat_Detection_Model_1"
    analyzer = DataAnalyzer(dataset_dir)
    datasets = analyzer.run_complete_analysis()

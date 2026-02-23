#!/usr/bin/env python3
"""
Create Master Dataset
Consolidates all CSV files with whitelist/blacklist data to create a master dataset
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MasterDatasetCreator:
    """Creates consolidated master dataset from all available CSVs"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.datasets_dir = self.base_dir / 'SecIDS-CNN' / 'datasets'
        self.whitelist_file = self.base_dir / 'Device_Profile' / 'whitelists' / 'whitelist_20260129.json'
        self.blacklist_file = self.base_dir / 'Device_Profile' / 'Blacklist' / 'blacklist_20260129.json'
        
        self.whitelist_data = self._load_whitelist()
        self.blacklist_data = self._load_blacklist()
        
    def _load_whitelist(self):
        """Load whitelist data"""
        try:
            with open(self.whitelist_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded whitelist with {len(data.get('processes', []))} processes")
                return data
        except Exception as e:
            logger.warning(f"Could not load whitelist: {e}")
            return {}
    
    def _load_blacklist(self):
        """Load blacklist data"""
        try:
            with open(self.blacklist_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded blacklist with {len(data.get('flagged_items', []))} items")
                return data
        except Exception as e:
            logger.warning(f"Could not load blacklist: {e}")
            return {}
    
    def find_all_csv_files(self):
        """Find all CSV files in datasets directory"""
        csv_files = []
        
        # Get all CSV files except results files
        for csv_file in self.datasets_dir.glob('*.csv'):
            # Skip files that are results or temporary
            if 'results' not in csv_file.name.lower() and 'temp' not in csv_file.name.lower():
                csv_files.append(csv_file)
        
        logger.info(f"Found {len(csv_files)} CSV files")
        for f in csv_files:
            logger.info(f"  - {f.name}")
        
        return csv_files
    
    def load_and_process_csv(self, csv_path):
        """Load and process a single CSV file"""
        try:
            logger.info(f"Processing {csv_path.name}...")
            
            # Try different encodings
            for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding, on_bad_lines='skip')
                    break
                except UnicodeDecodeError:
                    continue
            else:
                logger.error(f"Could not decode {csv_path.name}")
                return None
            
            logger.info(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Add source file column
            df['source_file'] = csv_path.name
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing {csv_path.name}: {e}")
            return None
    
    def apply_whitelist_blacklist(self, df):
        """Apply whitelist/blacklist rules to refine labels"""
        
        if 'Label' not in df.columns:
            logger.info("No Label column found, skipping whitelist/blacklist application")
            return df
        
        # Count original labels
        original_attack_count = (df['Label'] == 1).sum()
        
        # If there are IP columns, check against whitelist/blacklist
        ip_columns = [col for col in df.columns if 'ip' in col.lower() or 'address' in col.lower()]
        
        if ip_columns:
            logger.info(f"Found IP columns: {ip_columns}")
            # Add logic here to check IPs against whitelist/blacklist if needed
        
        new_attack_count = (df['Label'] == 1).sum()
        
        if original_attack_count != new_attack_count:
            logger.info(f"  Relabeled: {original_attack_count} -> {new_attack_count} attacks")
        
        return df
    
    def create_master_dataset(self, output_name='MD_1.csv'):
        """Create consolidated master dataset"""
        logger.info("\n" + "="*80)
        logger.info("CREATING MASTER DATASET")
        logger.info("="*80)
        
        csv_files = self.find_all_csv_files()
        
        if not csv_files:
            logger.error("No CSV files found!")
            return None
        
        all_dataframes = []
        
        for csv_file in csv_files:
            df = self.load_and_process_csv(csv_file)
            if df is not None and len(df) > 0:
                # Apply whitelist/blacklist rules
                df = self.apply_whitelist_blacklist(df)
                all_dataframes.append(df)
        
        if not all_dataframes:
            logger.error("No valid dataframes to combine!")
            return None
        
        logger.info("\n" + "="*80)
        logger.info("COMBINING DATASETS")
        logger.info("="*80)
        
        # Prioritize refined and combined datasets
        priority_order = ['combined_refined', 'ddos_training_dataset_refined', 'Test1_refined']
        
        # Sort dataframes by priority
        def get_priority(df):
            source = df['source_file'].iloc[0] if 'source_file' in df.columns else ''
            for idx, pattern in enumerate(priority_order):
                if pattern in source:
                    return idx
            return 999
        
        all_dataframes.sort(key=get_priority)
        
        # Use the first (highest priority) dataframe as base
        base_df = all_dataframes[0].copy()
        base_columns = set(base_df.columns) - {'source_file'}
        
        logger.info(f"Using {base_df['source_file'].iloc[0]} as base structure")
        logger.info(f"Base columns: {len(base_columns)}")
        
        # Try to merge other dataframes
        merged_dfs = [base_df]
        
        for df in all_dataframes[1:]:
            df_columns = set(df.columns) - {'source_file'}
            common = base_columns.intersection(df_columns)
            
            if len(common) >= 5:  # At least 5 common columns
                logger.info(f"  Adding {df['source_file'].iloc[0]}: {len(common)} common columns")
                # Keep only common columns plus source_file
                df_subset = df[[col for col in df.columns if col in common or col == 'source_file']]
                # Reindex to match base columns
                for col in base_columns:
                    if col not in df_subset.columns:
                        df_subset[col] = 0
                merged_dfs.append(df_subset[list(base_df.columns)])
            else:
                logger.info(f"  Skipping {df['source_file'].iloc[0]}: only {len(common)} common columns")
        
        # Concatenate all dataframes
        master_df = pd.concat(merged_dfs, ignore_index=True)
        
        logger.info("\n" + "="*80)
        logger.info("MASTER DATASET STATISTICS")
        logger.info("="*80)
        logger.info(f"Total rows: {len(master_df)}")
        logger.info(f"Total columns: {len(master_df.columns)}")
        
        if 'Label' in master_df.columns:
            attack_count = (master_df['Label'] == 1).sum()
            benign_count = (master_df['Label'] == 0).sum()
            logger.info(f"Attack samples: {attack_count}")
            logger.info(f"Benign samples: {benign_count}")
        
        # Handle missing values
        logger.info("\nHandling missing values...")
        master_df = master_df.fillna(0)
        
        # Handle infinite values
        master_df = master_df.replace([np.inf, -np.inf], 0)
        
        # Save master dataset
        output_path = self.datasets_dir / output_name
        master_df.to_csv(output_path, index=False)
        
        logger.info("\n" + "="*80)
        logger.info(f"✓ Master dataset saved to: {output_path}")
        logger.info(f"  Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        logger.info("="*80)
        
        return output_path


def main():
    """Main function"""
    base_dir = Path(__file__).parent.parent
    
    creator = MasterDatasetCreator(base_dir)
    
    # Create master dataset
    timestamp = datetime.now().strftime('%Y%m%d')
    output_name = f'MD_{timestamp}.csv'
    
    master_path = creator.create_master_dataset(output_name)
    
    if master_path:
        logger.info("\n✓ Master dataset creation complete!")
        return 0
    else:
        logger.error("\n✗ Master dataset creation failed!")
        return 1


if __name__ == '__main__':
    exit(main())

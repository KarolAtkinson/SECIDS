#!/usr/bin/env python3
"""
Dataset Path Helper
Provides centralized dataset path resolution for the entire project
"""

import json
import os
from pathlib import Path
from datetime import datetime


class DatasetPathHelper:
    """Helper class for resolving dataset paths"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_file = self.base_dir / 'Config' / 'dataset_config.json'
        self.config = self._load_config()
    
    def _load_config(self):
        """Load dataset configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load dataset config: {e}")
            return {}
    
    def get_master_dataset_path(self):
        """Get path to current master dataset"""
        if 'master_dataset' in self.config:
            master_path = self.base_dir / self.config['master_dataset']['path']
            if master_path.exists():
                return str(master_path)
        
        # Fallback: search for master dataset
        datasets_dir = self.base_dir / 'SecIDS-CNN' / 'datasets'
        master_files = list(datasets_dir.glob('MD_*.csv'))
        
        if master_files:
            # Return most recent
            master_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return str(master_files[0])
        
        return None
    
    def get_fallback_dataset_path(self, dataset_type='ddos'):
        """Get fallback dataset path"""
        if 'fallback_datasets' in self.config and dataset_type in self.config['fallback_datasets']:
            fallback_path = self.base_dir / self.config['fallback_datasets'][dataset_type]
            if fallback_path.exists():
                return str(fallback_path)
        
        # Search in archives
        archives_dir = self.base_dir / 'Archives'
        if archives_dir.exists():
            if dataset_type == 'ddos':
                ddos_file = archives_dir / 'ddos_training_dataset.csv'
                if ddos_file.exists():
                    return str(ddos_file)
            elif dataset_type == 'combined':
                combined_files = list(archives_dir.glob('combined_refined_dataset_*.csv'))
                if combined_files:
                    combined_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    return str(combined_files[0])
        
        return None
    
    def get_dataset_path(self, prefer_master=True):
        """
        Get best available dataset path
        
        Args:
            prefer_master: If True, use master dataset. If False, use fallback.
        
        Returns:
            Path to dataset file or None if not found
        """
        if prefer_master:
            master_path = self.get_master_dataset_path()
            if master_path:
                return master_path
            print("⚠️  Master dataset not found, using fallback")
        
        fallback_path = self.get_fallback_dataset_path('ddos')
        if fallback_path:
            return fallback_path
        
        fallback_combined = self.get_fallback_dataset_path('combined')
        if fallback_combined:
            return fallback_combined
        
        return None
    
    def get_archives_path(self):
        """Get path to archives directory"""
        archives_path = self.base_dir / 'Archives'
        if archives_path.exists():
            return str(archives_path)
        return None
    
    def update_master_dataset_config(self, dataset_path, rows, columns, size_mb):
        """Update config with new master dataset info"""
        config = self.config.copy()
        
        dataset_name = Path(dataset_path).name
        relative_path = Path(dataset_path).relative_to(self.base_dir)
        
        config['updated'] = datetime.now().isoformat()
        config['master_dataset'] = {
            'path': str(relative_path).replace('\\', '/'),
            'name': dataset_name,
            'created': datetime.now().isoformat(),
            'rows': rows,
            'columns': columns,
            'size_mb': round(size_mb, 2),
            'description': 'Consolidated master dataset from all refined CSV files with whitelist/blacklist application'
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✓ Updated dataset config: {dataset_name}")
        except Exception as e:
            print(f"✗ Failed to update config: {e}")


# Convenience functions for quick access
def get_master_dataset():
    """Get path to master dataset"""
    helper = DatasetPathHelper()
    return helper.get_master_dataset_path()


def get_dataset(prefer_master=True):
    """Get best available dataset"""
    helper = DatasetPathHelper()
    return helper.get_dataset_path(prefer_master)


def get_archives():
    """Get path to archives"""
    helper = DatasetPathHelper()
    return helper.get_archives_path()


if __name__ == '__main__':
    # Test the helper
    helper = DatasetPathHelper()
    
    print("Dataset Path Helper - Configuration")
    print("=" * 60)
    
    master = helper.get_master_dataset_path()
    print(f"Master dataset: {master if master else 'NOT FOUND'}")
    
    fallback = helper.get_fallback_dataset_path('ddos')
    print(f"Fallback dataset: {fallback if fallback else 'NOT FOUND'}")
    
    archives = helper.get_archives_path()
    print(f"Archives directory: {archives if archives else 'NOT FOUND'}")
    
    best = helper.get_dataset_path()
    print(f"\nBest available: {best if best else 'NOT FOUND'}")

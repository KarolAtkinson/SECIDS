#!/usr/bin/env python3
"""
Dataset Refinement Script
Re-labels existing datasets using whitelist rules to reduce false positives
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add Device_Profile to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'Device_Profile' / 'device_info'))
from whitelist_checker import WhitelistChecker

def refine_dataset(input_csv, output_csv=None, whitelist_checker=None):
    """
    Refine dataset by applying whitelist rules
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file (optional)
        whitelist_checker: WhitelistChecker instance (optional)
    
    Returns:
        DataFrame with refined labels
    """
    print(f"\n{'='*80}")
    print(f"REFINING DATASET: {Path(input_csv).name}")
    print(f"{'='*80}\n")
    
    # Load dataset
    try:
        df = pd.read_csv(input_csv)
        print(f"✓ Loaded {len(df)} flows")
    except Exception as e:
        print(f"✗ Error loading dataset: {e}")
        return None
    
    # Initialize whitelist checker if not provided
    if whitelist_checker is None:
        whitelist_checker = WhitelistChecker()
    
    # Get statistics before refinement
    if 'Label' in df.columns:
        original_attacks = (df['Label'] == 'ATTACK').sum()
        original_benign = (df['Label'] == 'Benign').sum()
        print(f"Original labels: {original_attacks} attacks, {original_benign} benign")
    else:
        print("No 'Label' column found - will add labels based on heuristics")
        df['Label'] = 'Benign'  # Default to benign
    
    # Track refinements
    refined_count = 0
    whitelist_reasons = []
    
    # Process each flow
    for idx, row in df.iterrows():
        # Extract flow information
        dst_port = int(row.get('Destination Port', 0))
        
        # Get source/destination IPs if available
        src_ip = row.get(' Source IP', row.get('Source IP', 'unknown'))
        dst_ip = row.get(' Destination IP', row.get('Destination IP', 'unknown'))
        
        # Estimate threat probability based on features
        if 'Label' in df.columns and df.at[idx, 'Label'] == 'ATTACK':
            probability = 0.9  # Already labeled as attack
        else:
            # Use heuristics to estimate threat level
            flow_bytes_s = float(row.get('Flow Bytes/s', 0))
            flow_pkts_s = float(row.get('Flow Packets/s', 0))
            total_packets = float(row.get('Total Fwd Packets', 0))
            
            # High traffic patterns might be suspicious
            if flow_bytes_s > 1000000 or flow_pkts_s > 1000:
                probability = 0.7
            elif total_packets > 100:
                probability = 0.6
            else:
                probability = 0.3
        
        # Check whitelist
        whitelist_result = whitelist_checker.check_flow(
            src_ip=str(src_ip),
            dst_ip=str(dst_ip),
            dst_port=dst_port,
            probability=probability
        )
        
        # Refine label if whitelisted
        if whitelist_result['whitelisted']:
            if df.at[idx, 'Label'] == 'ATTACK':
                refined_count += 1
                whitelist_reasons.append(whitelist_result['reason'])
            df.at[idx, 'Label'] = 'Benign'
            df.at[idx, 'Whitelist_Confidence'] = whitelist_result['confidence']
            df.at[idx, 'Whitelist_Reason'] = whitelist_result['reason']
    
    # Get statistics after refinement
    final_attacks = (df['Label'] == 'ATTACK').sum()
    final_benign = (df['Label'] == 'Benign').sum()
    
    print(f"\nRefinement Results:")
    print(f"  Flows re-labeled: {refined_count}")
    print(f"  Final labels: {final_attacks} attacks, {final_benign} benign")
    print(f"  False positives corrected: {refined_count}")
    
    if refined_count > 0:
        print(f"\n  Top whitelist reasons:")
        from collections import Counter
        for reason, count in Counter(whitelist_reasons).most_common(5):
            print(f"    - {reason}: {count} flows")
    
    # Save refined dataset
    if output_csv:
        try:
            df.to_csv(output_csv, index=False)
            print(f"\n✓ Saved refined dataset to: {output_csv}")
        except Exception as e:
            print(f"\n✗ Error saving dataset: {e}")
    
    print(f"\n{'='*80}\n")
    return df

def process_all_datasets(dataset_dirs, output_dir=None):
    """
    Process all CSV files in given directories
    
    Args:
        dataset_dirs: List of directories containing datasets
        output_dir: Directory to save refined datasets
    """
    if output_dir is None:
        output_dir = Path('SecIDS-CNN/datasets')
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize whitelist checker once
    whitelist_checker = WhitelistChecker()
    
    print(f"\n{'='*80}")
    print("DATASET REFINEMENT PIPELINE")
    print(f"{'='*80}")
    print(f"Whitelist Statistics:")
    stats = whitelist_checker.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print(f"{'='*80}\n")
    
    # Find all CSV files
    all_csvs = []
    for dataset_dir in dataset_dirs:
        dataset_path = Path(dataset_dir)
        if dataset_path.exists():
            csvs = list(dataset_path.glob('*.csv'))
            all_csvs.extend(csvs)
    
    print(f"Found {len(all_csvs)} CSV files to process\n")
    
    # Process each file
    refined_datasets = []
    for csv_file in all_csvs:
        # Skip result files and refined files
        if '_results' in csv_file.name or '_refined' in csv_file.name:
            print(f"Skipping {csv_file.name} (results/refined file)")
            continue
        
        # Generate output filename
        output_name = csv_file.stem + '_refined.csv'
        output_path = output_dir / output_name
        
        # Refine dataset
        refined_df = refine_dataset(csv_file, output_path, whitelist_checker)
        
        if refined_df is not None:
            refined_datasets.append({
                'original': csv_file,
                'refined': output_path,
                'flows': len(refined_df)
            })
    
    # Create combined refined dataset
    print(f"\n{'='*80}")
    print("CREATING COMBINED REFINED DATASET")
    print(f"{'='*80}\n")
    
    all_refined_data = []
    for item in refined_datasets:
        try:
            df = pd.read_csv(item['refined'])
            all_refined_data.append(df)
            print(f"✓ Added {item['refined'].name}: {len(df)} flows")
        except Exception as e:
            print(f"✗ Error loading {item['refined'].name}: {e}")
    
    if all_refined_data:
        combined_df = pd.concat(all_refined_data, ignore_index=True)
        
        # Drop whitelist columns for training
        training_df = combined_df.drop(columns=['Whitelist_Confidence', 'Whitelist_Reason'], errors='ignore')
        
        # Save combined dataset
        timestamp = datetime.now().strftime('%Y%m%d')
        combined_path = output_dir / f'combined_refined_dataset_{timestamp}.csv'
        training_df.to_csv(combined_path, index=False)
        
        print(f"\n✓ Created combined refined dataset: {combined_path.name}")
        print(f"  Total flows: {len(training_df)}")
        print(f"  Attacks: {(training_df['Label'] == 'ATTACK').sum()}")
        print(f"  Benign: {(training_df['Label'] == 'Benign').sum()}")
        print(f"\n{'='*80}\n")
        
        return combined_path
    
    return None

if __name__ == '__main__':
    # Process datasets from multiple locations
    dataset_directories = [
        'SecIDS-CNN/datasets',
        'Model_Tester/Code/datasets',
        'Threat_Detection_Model_1'
    ]
    
    # Process all datasets
    combined_dataset = process_all_datasets(dataset_directories)
    
    if combined_dataset:
        print(f"\n✓ Dataset refinement complete!")
        print(f"  New training dataset: {combined_dataset}")
    else:
        print(f"\n✗ No datasets were refined")

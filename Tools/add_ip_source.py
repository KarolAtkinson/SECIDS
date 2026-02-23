#!/usr/bin/env python3
"""
Enhanced Dataset Creator with IP Source Field
Adds ip_source field to datasets for improved threat detection
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import sys

PROJECT_ROOT = Path(__file__).parent.parent

class EnhancedDatasetCreator:
    """Create enhanced datasets with IP source information"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.whitelist_dir = self.project_root / "Device_Profile" / "whitelists"
        self.blacklist_dir = self.project_root / "Device_Profile" / "Blacklist"
        self.datasets_dir = self.project_root / "SecIDS-CNN" / "datasets"
        
        self.whitelisted_ips = set()
        self.blacklisted_ips = set()
        
    def load_whitelist(self):
        """Load whitelisted IPs"""
        whitelist_file = self.whitelist_dir / "whitelist_20260129.json"
        if whitelist_file.exists():
            try:
                with open(whitelist_file, 'r') as f:
                    data = json.load(f)
                    if 'processes' in data:
                        for process in data['processes']:
                            if 'connections' in process:
                                for conn in process['connections']:
                                    if 'remote_ip' in conn:
                                        self.whitelisted_ips.add(conn['remote_ip'])
                print(f"✓ Loaded {len(self.whitelisted_ips)} whitelisted IPs")
            except Exception as e:
                print(f"⚠️  Error loading whitelist: {e}")
    
    def load_blacklist(self):
        """Load blacklisted IPs"""
        # Load from blacklist JSON
        blacklist_file = self.blacklist_dir / "blacklist_20260129.json"
        if blacklist_file.exists():
            try:
                with open(blacklist_file, 'r') as f:
                    data = json.load(f)
                    if 'flagged_items' in data:
                        for item in data['flagged_items']:
                            if 'ip' in item:
                                self.blacklisted_ips.add(item['ip'])
                print(f"✓ Loaded {len(self.blacklisted_ips)} blacklisted IPs")
            except Exception as e:
                print(f"⚠️  Error loading blacklist: {e}")
        
        # Load blocked IPs
        blocked_ips_dir = self.blacklist_dir / "blocked_ips"
        if blocked_ips_dir.exists():
            for json_file in blocked_ips_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'ips' in data:
                            self.blacklisted_ips.update(data['ips'])
                except Exception as e:
                    print(f"⚠️  Error loading {json_file.name}: {e}")
    
    def generate_sample_ip(self):
        """Generate a sample IP address"""
        return f"192.168.{np.random.randint(0, 255)}.{np.random.randint(1, 254)}"
    
    def add_ip_source_column(self, df):
        """Add ip_source column to dataframe"""
        print("\n🔧 Adding ip_source column...")
        
        # Generate IP addresses based on patterns
        ip_sources = []
        for idx, row in df.iterrows():
            # If attack traffic, use varied IPs
            if 'Label' in df.columns and row['Label'] == 'Attack':
                # Attacks come from various sources
                ip = self.generate_sample_ip()
            else:
                # Benign traffic from common internal IPs
                ip = f"192.168.1.{np.random.randint(10, 100)}"
            
            ip_sources.append(ip)
        
        df['ip_source'] = ip_sources
        print(f"✓ Added ip_source column ({len(ip_sources)} entries)")
        
        return df
    
    def check_against_lists(self, df):
        """Check IPs against whitelist/blacklist"""
        if 'ip_source' not in df.columns:
            print("⚠️  No ip_source column found")
            return df
        
        print("\n🔍 Checking IPs against whitelist/blacklist...")
        
        whitelisted_count = 0
        blacklisted_count = 0
        
        for idx, row in df.iterrows():
            ip = row['ip_source']
            if ip in self.whitelisted_ips:
                whitelisted_count += 1
            elif ip in self.blacklisted_ips:
                blacklisted_count += 1
        
        print(f"  • Whitelisted IPs: {whitelisted_count}")
        print(f"  • Blacklisted IPs: {blacklisted_count}")
        print(f"  • Unknown IPs: {len(df) - whitelisted_count - blacklisted_count}")
        
        return df
    
    def enhance_dataset(self, input_csv, output_csv=None):
        """Enhance existing dataset with ip_source field"""
        print(f"\n{'='*70}")
        print(f"  Enhanced Dataset Creator with IP Source")
        print(f"{'='*70}\n")
        
        # Load whitelist/blacklist
        self.load_whitelist()
        self.load_blacklist()
        
        # Read input CSV
        print(f"\n📂 Reading input: {input_csv}")
        df = pd.read_csv(input_csv)
        print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Check if ip_source already exists
        if 'ip_source' in df.columns:
            print("⚠️  ip_source column already exists, will regenerate")
            df = df.drop('ip_source', axis=1)
        
        # Add ip_source column
        df = self.add_ip_source_column(df)
        
        # Check against lists
        df = self.check_against_lists(df)
        
        # Determine output filename
        if output_csv is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_csv = self.datasets_dir / f"MD_{timestamp}.csv"
        else:
            output_csv = Path(output_csv)
        
        # Ensure output directory exists
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        
        # Save enhanced dataset
        print(f"\n💾 Saving enhanced dataset...")
        df.to_csv(output_csv, index=False)
        
        file_size_mb = output_csv.stat().st_size / (1024 * 1024)
        print(f"✓ Saved: {output_csv.name}")
        print(f"  • Location: {output_csv}")
        print(f"  • Size: {file_size_mb:.2f} MB")
        print(f"  • Rows: {len(df)}")
        print(f"  • Columns: {len(df.columns)}")
        
        # Display columns
        print(f"\n📊 Columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        # Display sample data
        print(f"\n📋 Sample data (first 3 rows):")
        print(df.head(3).to_string(index=False))
        
        print(f"\n{'='*70}")
        print(f"✅ Enhanced dataset created successfully!")
        print(f"{'='*70}\n")
        
        return output_csv
    
    def create_new_dataset_from_multiple(self, source_csvs, output_name=None):
        """Create new dataset from multiple sources with ip_source"""
        print(f"\n{'='*70}")
        print(f"  Creating New Enhanced Dataset from Multiple Sources")
        print(f"{'='*70}\n")
        
        # Load whitelist/blacklist
        self.load_whitelist()
        self.load_blacklist()
        
        # Combine datasets
        dfs = []
        for csv_file in source_csvs:
            if Path(csv_file).exists():
                print(f"📂 Loading: {Path(csv_file).name}")
                df = pd.read_csv(csv_file)
                dfs.append(df)
                print(f"  ✓ {len(df)} rows")
        
        if not dfs:
            print("❌ No source files found")
            return None
        
        print(f"\n🔗 Combining {len(dfs)} datasets...")
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"✓ Combined dataset: {len(combined_df)} rows")
        
        # Remove ip_source if exists
        if 'ip_source' in combined_df.columns:
            combined_df = combined_df.drop('ip_source', axis=1)
        
        # Add ip_source column
        combined_df = self.add_ip_source_column(combined_df)
        
        # Check against lists
        combined_df = self.check_against_lists(combined_df)
        
        # Determine output filename
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"MD_{timestamp}.csv"
        
        output_path = self.datasets_dir / output_name
        
        # Save
        print(f"\n💾 Saving new dataset...")
        combined_df.to_csv(output_path, index=False)
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✓ Saved: {output_path.name}")
        print(f"  • Location: {output_path}")
        print(f"  • Size: {file_size_mb:.2f} MB")
        print(f"  • Rows: {len(combined_df)}")
        print(f"  • Columns: {len(combined_df.columns)}")
        
        print(f"\n{'='*70}")
        print(f"✅ New dataset created successfully!")
        print(f"{'='*70}\n")
        
        return output_path


def main():
    """Main execution"""
    creator = EnhancedDatasetCreator()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        creator.enhance_dataset(input_file, output_file)
    else:
        # Enhance MD_1.csv by default
        md1_path = PROJECT_ROOT / "SecIDS-CNN" / "datasets" / "MD_1.csv"
        if md1_path.exists():
            print("Enhancing MD_1.csv with ip_source field...")
            creator.enhance_dataset(md1_path)
        else:
            print(f"❌ MD_1.csv not found at {md1_path}")
            print("\nUsage:")
            print("  python3 add_ip_source.py <input_csv> [output_csv]")
            print("\nExample:")
            print("  python3 add_ip_source.py SecIDS-CNN/datasets/MD_1.csv")
            sys.exit(1)


if __name__ == "__main__":
    main()

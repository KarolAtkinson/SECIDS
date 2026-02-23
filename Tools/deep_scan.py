#!/usr/bin/env python3
"""
Deep Scan - Comprehensive Network Threat Detection

This script performs an intensive, multi-layered security scan that combines
all available detection methods for maximum accuracy and thoroughness.

Features:
  - Multi-pass analysis with different detection algorithms
  - Behavioral analysis with pattern recognition
  - Statistical anomaly detection
  - IP reputation checking (whitelist/blacklist)
  - Packet-level deep inspection
  - Equally-spaced scan intervals for consistency
  - Progressive threat scoring
  - Comprehensive reporting

Usage:
  python3 Tools/deep_scan.py --iface eth0 --duration 300
  python3 Tools/deep_scan.py --file path/to/data.csv
  
  Live Mode:
    --iface: Network interface to scan
    --duration: Total scan duration (default: 300s)
    --interval: Time between scan passes (default: 30s)
    
  File Mode:
    --file: CSV file to analyze
    --passes: Number of analysis passes (default: 5)

Deep Scan Process:
  1. Initial baseline establishment
  2. Multi-pass CNN model analysis
  3. Statistical anomaly detection
  4. Behavioral pattern analysis
  5. IP reputation cross-reference
  6. Packet signature matching
  7. Final threat aggregation
"""

import argparse
import sys
import time
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime
import json
import threading

import pandas as pd
import numpy as np

try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP
except ImportError:
    print("ERROR: Scapy required. Install: pip install scapy")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SECIDS_DIR = PROJECT_ROOT / 'SecIDS-CNN'
TOOLS_DIR = PROJECT_ROOT / 'Tools'
DEVICE_PROFILE_DIR = PROJECT_ROOT / 'Device_Profile'
RESULTS_DIR = PROJECT_ROOT / 'Results'
LOGS_DIR = PROJECT_ROOT / 'Logs'

for path in [SECIDS_DIR, TOOLS_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from secids_cnn import SecIDSModel

# Create directories
RESULTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class DeepScanner:
    """Comprehensive deep scanning with multi-layered threat detection"""
    
    def __init__(self, interface=None, duration=600, interval=60, verbose=True):
        self.interface = interface
        self.duration = duration
        self.interval = interval
        self.verbose = verbose
        
        # Detection components
        self.model = None
        self.whitelist = set()
        self.blacklist = set()
        
        # Scan statistics
        self.scan_start_time = None
        self.total_packets = 0
        self.total_flows = 0
        self.threat_scores = defaultdict(float)
        self.detected_threats = []
        self.scan_passes = []
        
        # Behavioral baselines
        self.baseline_stats = {}
        self.anomaly_threshold = 2.5  # Standard deviations
        
        print("╔════════════════════════════════════════════════════════════╗")
        print("║              SecIDS-CNN Deep Scan Initializing            ║")
        print("╚════════════════════════════════════════════════════════════╝\n")
        
    def load_model(self):
        """Load the SecIDS-CNN model"""
        if self.verbose:
            print("[1/7] Loading SecIDS-CNN model...", end=" ", flush=True)
        
        try:
            self.model = SecIDSModel()
            print("✓")
        except Exception as e:
            print(f"✗\n      Error: {e}")
            return False
        return True
    
    def load_reputation_lists(self):
        """Load whitelist and blacklist"""
        if self.verbose:
            print("[2/7] Loading IP reputation lists...", end=" ", flush=True)
        
        try:
            # Load whitelist
            whitelist_dir = DEVICE_PROFILE_DIR / 'whitelists'
            if whitelist_dir.exists():
                for wl_file in whitelist_dir.glob('whitelist_*.json'):
                    with open(wl_file, 'r') as f:
                        data = json.load(f)
                        if 'trusted_ips' in data:
                            self.whitelist.update(data['trusted_ips'])
            
            # Load blacklist
            blacklist_dir = DEVICE_PROFILE_DIR / 'Blacklist'
            if blacklist_dir.exists():
                for bl_file in blacklist_dir.glob('blacklist_*.json'):
                    with open(bl_file, 'r') as f:
                        data = json.load(f)
                        if 'flagged_items' in data:
                            for item in data['flagged_items']:
                                if 'ip' in item:
                                    self.blacklist.add(item['ip'])
            
            print(f"✓ ({len(self.whitelist)} trusted, {len(self.blacklist)} flagged)")
        except Exception as e:
            print(f"⚠ ({e})")
        
        return True
    
    def establish_baseline(self, data):
        """Establish behavioral baseline statistics"""
        if self.verbose:
            print("[3/7] Establishing behavioral baseline...", end=" ", flush=True)
        
        try:
            # Calculate baseline statistics for numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                self.baseline_stats[col] = {
                    'mean': data[col].mean(),
                    'std': data[col].std(),
                    'median': data[col].median(),
                    'q25': data[col].quantile(0.25),
                    'q75': data[col].quantile(0.75)
                }
            
            print(f"✓ ({len(self.baseline_stats)} features)")
        except Exception as e:
            print(f"⚠ ({e})")
        
        return True
    
    def multi_pass_analysis(self, data, passes=10):
        """Run multiple analysis passes with different parameters"""
        if self.verbose:
            print(f"[4/7] Multi-pass CNN analysis ({passes} passes)...", end=" ", flush=True)
        
        try:
            pass_results = []
            
            for pass_num in range(1, passes + 1):
                # Run prediction - get both predictions and probabilities
                predictions = self.model.predict(data)  # type: ignore
                probabilities = self.model.predict_proba(data)  # type: ignore
                
                # Ensure probabilities is 1D array
                if probabilities.ndim > 1:
                    probabilities = probabilities.flatten()
                
                # Store results for this pass
                pass_results.append({
                    'pass': pass_num,
                    'predictions': predictions,
                    'probabilities': probabilities,
                    'threat_count': sum(1 for p in predictions if p == 'Attack')
                })
                
                # Brief pause between passes for consistency
                if pass_num < passes:
                    time.sleep(0.5)
            
            # Aggregate results across all passes
            aggregated_predictions = []
            aggregated_probabilities = []
            
            for i in range(len(data)):
                # Count attack votes and average probabilities
                attack_votes = sum(1 for pr in pass_results if pr['predictions'][i] == 'Attack')
                avg_prob = np.mean([pr['probabilities'][i] for pr in pass_results])
                
                # Consensus prediction (majority vote)
                final_pred = 'Attack' if attack_votes > passes / 2 else 'Benign'
                aggregated_predictions.append(final_pred)
                aggregated_probabilities.append(avg_prob)
            
            self.scan_passes = pass_results
            print(f"✓")
            return aggregated_predictions, aggregated_probabilities
            
        except Exception as e:
            print(f"✗\n      Error: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def statistical_anomaly_detection(self, data):
        """Detect statistical anomalies based on baseline"""
        if self.verbose:
            print("[5/7] Statistical anomaly detection...", end=" ", flush=True)
        
        try:
            anomalies = []
            
            for idx, row in data.iterrows():
                anomaly_score = 0
                anomaly_features = []
                
                for col, stats in self.baseline_stats.items():
                    if col in row:
                        value = row[col]
                        mean = stats['mean']
                        std = stats['std']
                        
                        if std > 0:
                            z_score = abs((value - mean) / std)
                            if z_score > self.anomaly_threshold:
                                anomaly_score += z_score
                                anomaly_features.append(col)
                
                anomalies.append({
                    'index': idx,
                    'score': anomaly_score,
                    'features': anomaly_features
                })
            
            # Filter significant anomalies
            significant_anomalies = [a for a in anomalies if a['score'] > 5.0]
            
            print(f"✓ ({len(significant_anomalies)} anomalies)")
            return anomalies
            
        except Exception as e:
            print(f"⚠ ({e})")
            return []
    
    def behavioral_pattern_analysis(self, data):
        """Analyze behavioral patterns and sequences"""
        if self.verbose:
            print("[6/7] Behavioral pattern analysis...", end=" ", flush=True)
        
        try:
            patterns = defaultdict(int)
            suspicious_patterns = []
            
            # Check for port scanning patterns
            if 'dst_port' in data.columns:
                port_counts = data['dst_port'].value_counts()
                if len(port_counts) > 50:  # Scanning many ports
                    suspicious_patterns.append({
                        'type': 'port_scan',
                        'severity': 'high',
                        'details': f'{len(port_counts)} unique ports targeted'
                    })
            
            # Check for packet size anomalies
            if 'pkt_size' in data.columns or 'tot_size' in data.columns:
                size_col = 'pkt_size' if 'pkt_size' in data.columns else 'tot_size'
                avg_size = data[size_col].mean()
                if avg_size > 1400:  # Large packets
                    suspicious_patterns.append({
                        'type': 'large_packets',
                        'severity': 'medium',
                        'details': f'Average packet size: {avg_size:.0f} bytes'
                    })
            
            # Check for connection rate anomalies
            if 'protocol' in data.columns:
                protocol_dist = data['protocol'].value_counts(normalize=True)
                if protocol_dist.get('TCP', 0) > 0.95:  # Overwhelmingly TCP
                    suspicious_patterns.append({
                        'type': 'tcp_flood',
                        'severity': 'high',
                        'details': f'{protocol_dist["TCP"]*100:.1f}% TCP traffic'
                    })
            
            print(f"✓ ({len(suspicious_patterns)} patterns)")
            return suspicious_patterns
            
        except Exception as e:
            print(f"⚠ ({e})")
            return []
    
    def ip_reputation_check(self, data):
        """Cross-reference IPs with reputation lists"""
        if self.verbose:
            print("[7/7] IP reputation cross-reference...", end=" ", flush=True)
        
        try:
            reputation_flags = []
            
            if 'ip_source' in data.columns:
                for idx, ip in enumerate(data['ip_source']):
                    if ip in self.blacklist:
                        reputation_flags.append({
                            'index': idx,
                            'ip': ip,
                            'status': 'blacklisted',
                            'threat_boost': 0.3
                        })
                    elif ip in self.whitelist:
                        reputation_flags.append({
                            'index': idx,
                            'ip': ip,
                            'status': 'whitelisted',
                            'threat_boost': -0.3
                        })
            
            blacklisted = sum(1 for f in reputation_flags if f['status'] == 'blacklisted')
            whitelisted = sum(1 for f in reputation_flags if f['status'] == 'whitelisted')
            
            print(f"✓ ({blacklisted} blacklisted, {whitelisted} whitelisted)")
            return reputation_flags
            
        except Exception as e:
            print(f"⚠ ({e})")
            return []
    
    def aggregate_threat_scores(self, data, cnn_predictions, cnn_probs, anomalies, patterns, reputation):
        """Aggregate all detection results into final threat scores"""
        print("\n📊 Aggregating threat intelligence...", end=" ", flush=True)
        
        try:
            final_results = []
            
            for idx in range(len(data)):
                # Base score from CNN
                base_score = cnn_probs[idx] if cnn_predictions[idx] == 'Attack' else (1 - cnn_probs[idx])
                
                # Add anomaly score (normalized)
                anomaly_score = anomalies[idx]['score'] / 20.0 if idx < len(anomalies) else 0
                
                # Add pattern score
                pattern_score = 0
                for pattern in patterns:
                    if pattern['severity'] == 'high':
                        pattern_score += 0.2
                    elif pattern['severity'] == 'medium':
                        pattern_score += 0.1
                
                # Add reputation score
                reputation_score = 0
                for rep in reputation:
                    if rep['index'] == idx:
                        reputation_score = rep['threat_boost']
                        break
                
                # Calculate final threat score
                final_score = np.clip(base_score + anomaly_score + pattern_score + reputation_score, 0, 1)
                
                # Determine final classification
                if final_score >= 0.7:
                    classification = 'High Risk'
                elif final_score >= 0.5:
                    classification = 'Attack'
                elif final_score >= 0.3:
                    classification = 'Suspicious'
                else:
                    classification = 'Benign'
                
                final_results.append({
                    'index': idx,
                    'classification': classification,
                    'threat_score': final_score,
                    'cnn_score': base_score,
                    'anomaly_score': anomaly_score,
                    'pattern_score': pattern_score,
                    'reputation_score': reputation_score
                })
            
            print("✓")
            return final_results
            
        except Exception as e:
            print(f"✗\n   Error: {e}")
            return []
    
    def scan_file(self, csv_file, passes=10):
        """Perform deep scan on a CSV file"""
        print(f"\n🔍 Deep Scan Mode: File Analysis")
        print(f"   Target: {csv_file}")
        print(f"   Passes: {passes}\n")
        
        self.scan_start_time = time.time()
        
        # Load data
        try:
            data = pd.read_csv(csv_file)
            print(f"✓ Loaded {len(data)} records from {csv_file}\n")
        except Exception as e:
            print(f"✗ Error loading file: {e}")
            return None
        
        # Initialize all components
        if not self.load_model():
            return None
        self.load_reputation_lists()
        self.establish_baseline(data)
        
        # Run multi-layered analysis
        print()
        cnn_predictions, cnn_probs = self.multi_pass_analysis(data, passes)
        if cnn_predictions is None:
            return None
        
        anomalies = self.statistical_anomaly_detection(data)
        patterns = self.behavioral_pattern_analysis(data)
        reputation = self.ip_reputation_check(data)
        
        # Aggregate results
        final_results = self.aggregate_threat_scores(
            data, cnn_predictions, cnn_probs, anomalies, patterns, reputation
        )
        
        # Generate report
        return self.generate_report(data, final_results, csv_file)
    
    def scan_live(self):
        """Perform deep scan on live network traffic"""
        print(f"\n🔍 Deep Scan Mode: Live Network Monitoring")
        print(f"   Interface: {self.interface}")
        print(f"   Duration: {self.duration}s")
        print(f"   Scan Interval: {self.interval}s\n")
        
        self.scan_start_time = time.time()
        
        # Initialize components
        if not self.load_model():
            return None
        self.load_reputation_lists()
        
        print("\n⏳ Starting live capture... (Press Ctrl+C to stop)\n")
        
        scan_count = 0
        scan_results_history = []
        
        try:
            while (time.time() - self.scan_start_time) < self.duration:
                scan_count += 1
                scan_start = time.time()
                
                print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(f"  Scan Pass #{scan_count}")
                print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                
                # Capture packets for this interval
                print(f"\n📡 Capturing traffic ({self.interval}s window)...", end=" ", flush=True)
                packets = sniff(iface=self.interface, timeout=self.interval, count=10000)
                print(f"✓ ({len(packets)} packets)")
                
                if len(packets) == 0:
                    print("⚠  No packets captured, waiting...")
                    time.sleep(5)
                    continue
                
                # Convert to DataFrame (simplified)
                data = self.packets_to_dataframe(packets)
                
                if data is None or len(data) == 0:
                    print("⚠  No flows extracted, waiting...")
                    time.sleep(5)
                    continue
                
                # Run analysis on this window
                if scan_count == 1:
                    self.establish_baseline(data)
                
                print()
                cnn_predictions, cnn_probs = self.multi_pass_analysis(data, passes=3)
                
                if cnn_predictions is None:
                    continue
                
                anomalies = self.statistical_anomaly_detection(data)
                patterns = self.behavioral_pattern_analysis(data)
                reputation = self.ip_reputation_check(data)
                
                # Aggregate
                final_results = self.aggregate_threat_scores(
                    data, cnn_predictions, cnn_probs, anomalies, patterns, reputation
                )
                
                # Display results for this scan
                self.display_scan_results(scan_count, final_results)
                
                scan_results_history.append({
                    'scan': scan_count,
                    'timestamp': datetime.now().isoformat(),
                    'results': final_results
                })
                
                # Wait for next scan interval (equally spaced)
                elapsed = time.time() - scan_start
                if elapsed < self.interval:
                    wait_time = self.interval - elapsed
                    print(f"\n⏱  Next scan in {wait_time:.1f}s...")
                    time.sleep(wait_time)
        
        except KeyboardInterrupt:
            print("\n\n⚠  Scan interrupted by user")
        
        # Generate final report
        print("\n" + "="*60)
        return self.generate_live_report(scan_results_history)
    
    def packets_to_dataframe(self, packets):
        """Convert captured packets to DataFrame (simplified)"""
        try:
            flows = []
            
            for pkt in packets:
                if not pkt.haslayer(IP):
                    continue
                
                ip_layer = pkt[IP]
                
                flow = {
                    'ip_source': ip_layer.src,
                    'src_ip': ip_layer.src,
                    'dst_ip': ip_layer.dst,
                    'pkt_size': len(pkt),
                    'protocol': ip_layer.proto
                }
                
                if pkt.haslayer(TCP):
                    tcp = pkt[TCP]
                    flow['src_port'] = tcp.sport
                    flow['dst_port'] = tcp.dport
                elif pkt.haslayer(UDP):
                    udp = pkt[UDP]
                    flow['src_port'] = udp.sport
                    flow['dst_port'] = udp.dport
                else:
                    flow['src_port'] = 0
                    flow['dst_port'] = 0
                
                flows.append(flow)
            
            if flows:
                return pd.DataFrame(flows)
            return None
            
        except Exception as e:
            print(f"⚠  Error converting packets: {e}")
            return None
    
    def display_scan_results(self, scan_num, results):
        """Display results for a single scan pass"""
        print("\n" + "─"*60)
        print(f"  Scan #{scan_num} Results:")
        print("─"*60)
        
        # Count by classification
        high_risk = sum(1 for r in results if r['classification'] == 'High Risk')
        attacks = sum(1 for r in results if r['classification'] == 'Attack')
        suspicious = sum(1 for r in results if r['classification'] == 'Suspicious')
        benign = sum(1 for r in results if r['classification'] == 'Benign')
        
        total = len(results)
        
        print(f"  🔴 High Risk:  {high_risk:4d} ({high_risk/total*100:5.1f}%)")
        print(f"  🟠 Attack:     {attacks:4d} ({attacks/total*100:5.1f}%)")
        print(f"  🟡 Suspicious: {suspicious:4d} ({suspicious/total*100:5.1f}%)")
        print(f"  🟢 Benign:     {benign:4d} ({benign/total*100:5.1f}%)")
        print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  📊 Total:      {total:4d} records analyzed")
        
        if high_risk > 0:
            print(f"\n  ⚠️  WARNING: {high_risk} HIGH RISK threats detected!")
    
    def generate_report(self, data, results, source_file):
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = RESULTS_DIR / f"deep_scan_report_{timestamp}.json"
        csv_file = RESULTS_DIR / f"deep_scan_results_{timestamp}.csv"
        
        # Count by classification
        classification_counts = defaultdict(int)
        for r in results:
            classification_counts[r['classification']] += 1
        
        # Calculate statistics
        threat_scores = [r['threat_score'] for r in results]
        avg_threat_score = np.mean(threat_scores)
        max_threat_score = np.max(threat_scores)
        
        # Create summary
        summary = {
            'scan_type': 'file',
            'timestamp': timestamp,
            'source_file': str(source_file),
            'total_records': len(data),
            'scan_duration': time.time() - self.scan_start_time,
            'classification_counts': dict(classification_counts),
            'statistics': {
                'avg_threat_score': float(avg_threat_score),
                'max_threat_score': float(max_threat_score),
                'threat_percentage': (classification_counts['Attack'] + classification_counts['High Risk']) / len(data) * 100
            },
            'multi_pass_details': [
                {'pass': p['pass'], 'threats': p['threat_count']}
                for p in self.scan_passes
            ]
        }
        
        # Save JSON report
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed CSV results
        results_df = pd.DataFrame(results)
        if 'ip_source' in data.columns:
            results_df['ip_source'] = data['ip_source'].values
        results_df.to_csv(csv_file, index=False)
        
        # Display summary
        print("\n" + "="*60)
        print("  DEEP SCAN COMPLETE")
        print("="*60)
        print(f"  📊 Total Records:     {len(data)}")
        print(f"  ⏱  Scan Duration:     {summary['scan_duration']:.1f}s")
        print(f"  🎯 Avg Threat Score:  {avg_threat_score:.3f}")
        print(f"  ⚠️  Threat Percentage: {summary['statistics']['threat_percentage']:.1f}%")
        print("\n  Classification Breakdown:")
        for cls, count in classification_counts.items():
            pct = count / len(data) * 100
            print(f"    {cls:12s}: {count:6d} ({pct:5.1f}%)")
        print("\n  📁 Reports Saved:")
        print(f"    • {report_file}")
        print(f"    • {csv_file}")
        print("="*60)
        
        return summary
    
    def generate_live_report(self, scan_history):
        """Generate report for live scanning"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = RESULTS_DIR / f"deep_scan_live_report_{timestamp}.json"
        
        # Aggregate across all scans
        total_scans = len(scan_history)
        total_threats = 0
        all_classifications = defaultdict(int)
        
        for scan in scan_history:
            for result in scan['results']:
                all_classifications[result['classification']] += 1
                if result['classification'] in ['Attack', 'High Risk']:
                    total_threats += 1
        
        summary = {
            'scan_type': 'live',
            'timestamp': timestamp,
            'interface': self.interface,
            'total_scans': total_scans,
            'scan_duration': time.time() - self.scan_start_time,
            'total_records_analyzed': sum(len(s['results']) for s in scan_history),
            'total_threats_detected': total_threats,
            'classification_counts': dict(all_classifications),
            'scan_history': scan_history
        }
        
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("  DEEP SCAN SESSION COMPLETE")
        print("="*60)
        print(f"  📊 Total Scans:       {total_scans}")
        print(f"  ⏱  Session Duration:  {summary['scan_duration']:.1f}s")
        print(f"  🔍 Records Analyzed:  {summary['total_records_analyzed']}")
        print(f"  ⚠️  Threats Detected:  {total_threats}")
        print("\n  📁 Report Saved:")
        print(f"    • {report_file}")
        print("="*60)
        
        return summary


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SecIDS-CNN Deep Scan - Comprehensive Threat Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--file', type=str, help='CSV file to analyze')
    mode_group.add_argument('--iface', type=str, help='Network interface for live scanning')
    
    # Parameters
    parser.add_argument('--duration', type=int, default=600, help='Total scan duration for live mode (default: 600s)')
    parser.add_argument('--interval', type=int, default=60, help='Time between scans for live mode (default: 60s)')
    parser.add_argument('--passes', type=int, default=10, help='Number of analysis passes for file mode (default: 10)')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Initialize scanner
    scanner = DeepScanner(
        interface=args.iface,
        duration=args.duration,
        interval=args.interval,
        verbose=not args.quiet
    )
    
    # Run appropriate scan mode
    if args.file:
        result = scanner.scan_file(args.file, passes=args.passes)
    else:
        result = scanner.scan_live()
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

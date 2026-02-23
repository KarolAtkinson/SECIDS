#!/usr/bin/env python3
import pandas as pd
import numpy as np
from secids_cnn import SecIDSModel
from sklearn.preprocessing import StandardScaler
import os
import argparse
import sys
import threading
import time
from pathlib import Path
from collections import deque
from datetime import datetime
import glob

# Add Tools and Countermeasures to path
tools_path = Path(__file__).parent.parent / 'Tools'
countermeasures_path = Path(__file__).parent.parent / 'Countermeasures'
sys.path.insert(0, str(tools_path))
sys.path.insert(0, str(countermeasures_path))

# Import progress utilities and Wireshark manager
try:
    from progress_utils import (DataLoadingProgress, PreprocessingProgress, 
                                 PredictionProgress, simple_progress_bar)
    PROGRESS_AVAILABLE = True
except ImportError as e:
    PROGRESS_AVAILABLE = False
    print(f"⚠️  Progress utilities not available: {e}")

try:
    from wireshark_manager import WiresharkManager
    WIRESHARK_AVAILABLE = True
except ImportError as e:
    WIRESHARK_AVAILABLE = False
    print(f"⚠️  Wireshark manager not available: {e}")

try:
    from system_checker import SystemChecker
    CHECKER_AVAILABLE = True
except ImportError:
    CHECKER_AVAILABLE = False

# Import countermeasure system
try:
    from ddos_countermeasure import DDoSCountermeasure
    COUNTERMEASURE_AVAILABLE = True
except ImportError as e:
    COUNTERMEASURE_AVAILABLE = False
    print(f"⚠️  Countermeasure system not available: {e}")

# Import report generator
try:
    from report_generator import ThreatReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError as e:
    REPORT_GENERATOR_AVAILABLE = False
    print(f"⚠️  Report generator not available: {e}")

# Use workspace-relative path: change working directory to this script's directory
script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)

def estimate_processing_time(num_records, rows_per_second=5000):
    """Estimate time to process records"""
    seconds = num_records / rows_per_second
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def print_progress_bar(iteration, total, prefix='', suffix='', length=50):
    """Print a progress bar to console"""
    percent = 100 * (iteration / float(total))
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent:.1f}% {suffix}', end='\r')
    if iteration == total:
        print()

def run_file_based_detection(data_paths, model, scaler):
    """Process static CSV files with threat detection."""
    print("="*80)
    print("FILE-BASED THREAT DETECTION")
    print("="*80)
    
    start_time = time.time()
    
    try:
        # Handle both single string and list of paths
        if isinstance(data_paths, str):
            data_paths = [data_paths]
        
        # Load and combine datasets
        dfs = []
        print("\n📂 Loading datasets...")
        if PROGRESS_AVAILABLE:
            with DataLoadingProgress.create(len(data_paths)) as pbar:
                for i, path in enumerate(data_paths, 1):
                    print_progress_bar(i, len(data_paths), prefix='Loading', suffix=f'{Path(path).name}')
                    df_temp = pd.read_csv(path)
                    print(f"\n  ✓ Loaded: {Path(path).name} - Shape: {df_temp.shape}")
                    dfs.append(df_temp)
                    pbar.update()
        else:
            for i, path in enumerate(data_paths, 1):
                print_progress_bar(i, len(data_paths), prefix='Loading', suffix=f'{Path(path).name}')
                df_temp = pd.read_csv(path)
                print(f"\n  ✓ Loaded: {Path(path).name} - Shape: {df_temp.shape}")
                dfs.append(df_temp)
        
        df = pd.concat(dfs, ignore_index=True)
        print(f"\n✓ Combined data shape: {df.shape}")
        
        # Estimate processing time
        est_time = estimate_processing_time(len(df))
        print(f"⏱️  Estimated processing time: {est_time}")
        print()
        
        # Step 3: Preprocess data
        print("🔧 Preprocessing network traffic data...")
        
        # Drop the is_ddos label column if it exists (for prediction purposes)
        X = df.drop(columns=["is_ddos"], errors="ignore")
        print(f"  Features shape: {X.shape}")
        
        # Fill missing values
        print("  Filling missing values...")
        X = X.fillna(X.mean(numeric_only=True))
        
        # Select only numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_cols]
        print(f"  Selected {len(numeric_cols)} numeric features")
        
        # Normalize/Scale the features
        print("  Scaling features...")
        X = scaler.fit_transform(X)
        print("  ✓ Preprocessing complete\n")

        # Step 4: Make predictions (use probability threshold >0.5 => DDoS)
        print("🔍 Making threat predictions (threshold: 0.5)...")
        prediction_start = time.time()
        
        # Process in batches for progress tracking
        batch_size = 10000
        total_batches = (len(X) + batch_size - 1) // batch_size
        all_probs = []
        
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(X))
            batch_X = pd.DataFrame(X[start_idx:end_idx], columns=numeric_cols)
            
            try:
                batch_probs = model.predict_proba(batch_X)
                all_probs.append(batch_probs)
            except Exception:
                # Fallback if predict_proba not available
                raw = model.predict(batch_X)
                if hasattr(raw, '__iter__'):
                    all_probs.append(np.array([float(r) if not isinstance(r, str) else (1.0 if r == 'Attack' else 0.0) for r in raw]))
                else:
                    all_probs.append(raw)
            
            # Show progress
            print_progress_bar(i + 1, total_batches, prefix='Predicting', suffix=f'Batch {i+1}/{total_batches}')
        
        print()  # New line after progress bar
        
        # Combine batch results
        if all_probs:
            if isinstance(all_probs[0], np.ndarray):
                probs = np.concatenate(all_probs)
            else:
                probs = all_probs[0]  # Single batch
        else:
            probs = None

        predictions = []
        probabilities = []
        
        if probs is None:
            predictions = ['Benign'] * len(X)
            probabilities = [0.0] * len(X)
        else:
            if hasattr(probs, 'ndim') and probs.ndim == 1:
                positive = probs
            elif hasattr(probs, 'ndim') and probs.ndim == 2 and probs.shape[1] == 2:
                positive = probs[:, 1]
            elif hasattr(probs, 'ndim') and probs.ndim == 2 and probs.shape[1] == 1:
                positive = probs.flatten()
            else:
                positive = (probs.argmax(axis=1) == 1).astype(float)

            for p in positive:
                prob_val = float(p)
                probabilities.append(prob_val)
                predictions.append('Attack' if prob_val > 0.5 else 'Benign')
        
        prediction_time = time.time() - prediction_start
        
        # Output results
        print("\n" + "="*80)
        print("THREAT DETECTION RESULTS")
        print("="*80)
        print(f"Total records analyzed: {len(predictions):,}")
        attack_count = predictions.count('Attack') if isinstance(predictions, list) else np.sum(predictions == 'Attack')
        benign_count = predictions.count('Benign') if isinstance(predictions, list) else np.sum(predictions == 'Benign')
        print(f"Threats detected: {attack_count:,}")
        print(f"Benign connections: {benign_count:,}")
        print(f"\nProcessing time: {prediction_time:.2f}s")
        print(f"Records per second: {len(predictions)/prediction_time:,.0f}")
        
        # Add predictions to original dataframe
        df['prediction'] = predictions
        if probabilities:
            df['probability'] = probabilities
        
        # Show threat details
        if attack_count > 0:
            print(f"\n⚠️  THREAT ALERT - {attack_count:,} malicious connections detected!")
            threat_data = df[df['prediction'] == 'Attack']
            print("\n📊 Top 10 Threats by Probability:")
            if 'probability' in threat_data.columns:
                top_threats = threat_data.nlargest(10, 'probability')
            else:
                top_threats = threat_data.head(10)
            
            # Display key columns
            display_cols = [col for col in ['Destination Port', 'Total Fwd Packets', 'Flow Bytes/s', 'prediction', 'probability'] if col in top_threats.columns]
            print(top_threats[display_cols].to_string(index=False))
        else:
            print("\n✅ No threats detected. Network traffic is clean.")
        
        # Save results to Results folder
        results_dir = script_dir.parent / 'Results'
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_path = results_dir / f'detection_results_{timestamp}.csv'
        df.to_csv(results_path, index=False)
        print(f"\n💾 Results saved to: {results_path}")
        
        # Generate comprehensive report
        if REPORT_GENERATOR_AVAILABLE and attack_count > 0:
            print("\n📄 Generating threat report...")
            try:
                report_gen = ThreatReportGenerator(results_path)
                report_gen.load_results()
                report_gen.analyze_results()
                report_gen.generate_markdown_report()
                report_gen.generate_json_report()
                print("✓ Threat reports generated successfully")
            except Exception as e:
                print(f"⚠️  Could not generate report: {e}")
        
        # Show elapsed time
        total_time = time.time() - start_time
        print(f"\n⏱️  Total elapsed time: {total_time:.2f}s")
        print("="*80)
        
    except FileNotFoundError as e:
        print(f"ERROR: File not found - {e}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def run_continuous_detection(iface, window_size=5.0, interval=2.0, model=None):
    """Stream continuous network traffic from interface with real-time detection."""
    print("="*80)
    print("CONTINUOUS LIVE TRAFFIC DETECTION")
    print("="*80)
    print(f"Interface: {iface}")
    print(f"Window size: {window_size}s")
    print(f"Processing interval: {interval}s")
    print("="*80)
    
    # Start Wireshark with auto-management
    wireshark_mgr = None
    if WIRESHARK_AVAILABLE:
        try:
            print("\n🦈 Starting Wireshark for live capture...")
            # Determine if we should use 'any' interface
            use_any = iface.lower() == 'any'
            wireshark_mgr = WiresharkManager(interface=iface, use_any=use_any)
            success = wireshark_mgr.start(background=True)
            if success:
                print("✓ Wireshark started successfully\n")
            else:
                print("⚠️  Wireshark failed to start")
                print("Continuing without Wireshark GUI...\n")
        except Exception as e:
            print(f"⚠️  Could not start Wireshark: {e}")
            print("Continuing without Wireshark GUI...\n")
    else:
        print("\n⚠️  Wireshark manager not available - continuing without GUI\n")
    
    print("Starting capture... (Press Ctrl+C to stop)\n")
    
    try:
        from scapy.all import sniff, IP, TCP, UDP  # type: ignore
    except ImportError:
        print("ERROR: Scapy is required for live capture: pip install scapy")
        if wireshark_mgr:
            wireshark_mgr.stop()
        sys.exit(1)
    
    # Initialize countermeasure system
    countermeasure = None
    if COUNTERMEASURE_AVAILABLE:
        try:
            countermeasure = DDoSCountermeasure()
            print("✓ Countermeasure system initialized\n")
        except Exception as e:
            print(f"⚠️  Could not initialize countermeasure: {e}\n")
    else:
        print("⚠️  Countermeasure system not available\n")
    
    packets = deque()
    lock = threading.Lock()
    is_running = True
    
    def packet_callback(pkt):
        if not pkt.haslayer(IP):
            return
        with lock:
            packets.append((time.time(), pkt))
    
    def sniff_thread():
        nonlocal is_running
        try:
            sniff(
                iface=iface,
                prn=packet_callback,
                store=False,
                stop_filter=lambda x: not is_running
            )
        except PermissionError:
            print(f"ERROR: Need elevated permissions to capture on {iface}")
            print("Run with sudo or configure: setcap cap_net_raw=ep $(which python3)")
            is_running = False
        except Exception as e:
            print(f"Capture error: {e}")
            is_running = False
    
    # Start capture thread
    capture_t = threading.Thread(target=sniff_thread, daemon=True)
    capture_t.start()
    time.sleep(1)  # Let capture initialize
    
    # Processing loop
    from collections import defaultdict
    window_count = 0
    total_flows = 0
    total_threats = 0
    
    try:
        while is_running:
            time.sleep(interval)
            
            # Get packets from window
            current_time = time.time()
            cutoff = current_time - window_size
            
            with lock:
                while packets and packets[0][0] < cutoff:
                    packets.popleft()
                packet_tuples = list(packets)
            
            if not packet_tuples:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No packets in window")
                continue
            
            window_count += 1
            
            # Convert packets to flows
            flows = defaultdict(lambda: {
                'fwd_pkts': [],
                'bwd_pkts': [],
                'dst_port': 0,
            })
            
            for ts, pkt in packet_tuples:
                if not pkt.haslayer(IP):
                    continue
                
                ip_layer = pkt[IP]
                sport = None
                dport = None
                proto = None
                flags = None
                
                if pkt.haslayer(TCP):
                    proto = 'TCP'
                    tcp_layer = pkt[TCP]
                    sport = tcp_layer.sport
                    dport = tcp_layer.dport
                    flags = tcp_layer.flags
                elif pkt.haslayer(UDP):
                    proto = 'UDP'
                    udp_layer = pkt[UDP]
                    sport = udp_layer.sport
                    dport = udp_layer.dport
                else:
                    continue
                
                flow_key = (ip_layer.src, ip_layer.dst, sport, dport, proto)
                pkt_len = len(pkt)
                
                if flow_key not in flows:
                    flows[flow_key] = {  # type: ignore
                        'first_ts': ts,
                        'last_ts': ts,
                        'fwd_pkts': [],
                        'bwd_pkts': [],
                        'dst_port': dport,
                        'fwd_id': (ip_layer.src, sport),
                        'src_ip': ip_layer.src,  # Store for countermeasures
                        'dst_ip': ip_layer.dst,
                    }
                
                flow = flows[flow_key]
                flow['last_ts'] = max(flow['last_ts'], ts)
                
                if (ip_layer.src, sport) == flow['fwd_id']:
                    flow['fwd_pkts'].append((ts, pkt_len, flags if pkt.haslayer(TCP) else None))
                else:
                    flow['bwd_pkts'].append((ts, pkt_len, flags if pkt.haslayer(TCP) else None))
            
            # Convert flows to features
            rows = []
            for flow_key, flow in flows.items():
                first_ts = flow['first_ts']
                last_ts = flow['last_ts']
                duration_s = max(1e-6, last_ts - first_ts)
                duration_us = int((last_ts - first_ts) * 1e6) if last_ts > first_ts else 0
                
                fwd_pkts = flow['fwd_pkts']  # type: ignore
                total_fwd_packets = len(fwd_pkts)
                total_length_fwd = sum(p[1] for p in fwd_pkts)  # type: ignore
                
                flow_bytes_per_s = total_length_fwd / duration_s if duration_s > 0 else 0
                flow_pkts_per_s = total_fwd_packets / duration_s if duration_s > 0 else 0
                
                avg_pkt_size = (total_length_fwd / total_fwd_packets) if total_fwd_packets > 0 else 0
                pkt_lengths = [p[1] for p in fwd_pkts] if fwd_pkts else [0]  # type: ignore
                pkt_len_std = float(np.std(pkt_lengths)) if len(pkt_lengths) > 1 else 0.0
                
                fin_count = 0
                ack_count = 0
                for (_, _, pkt_flags) in fwd_pkts:  # type: ignore
                    if pkt_flags is None:
                        continue
                    try:
                        flag_str = str(pkt_flags)
                        if 'F' in flag_str:
                            fin_count += 1
                        if 'A' in flag_str:
                            ack_count += 1
                    except Exception as e:
                        pass  # Skip on error
                rows.append({
                    'Destination Port': int(flow['dst_port']),
                    'Flow Duration': int(duration_us),
                    'Total Fwd Packets': int(total_fwd_packets),
                    'Total Length of Fwd Packets': int(total_length_fwd),
                    'Flow Bytes/s': float(flow_bytes_per_s),
                    'Flow Packets/s': float(flow_pkts_per_s),
                    'Average Packet Size': float(avg_pkt_size),
                    'Packet Length Std': float(pkt_len_std),
                    'FIN Flag Count': int(fin_count),
                    'ACK Flag Count': int(ack_count),
                    # Store IP info for countermeasures
                    '_src_ip': flow.get('src_ip', 'unknown'),
                    '_dst_ip': flow.get('dst_ip', 'unknown'),
                })
            
            # Create DataFrame from flows
            df = pd.DataFrame(rows)
            
            if df.empty or len(df) == 0:
                continue
            
            # Extract IP info before prediction (remove from features)
            ip_info = df[['_src_ip', '_dst_ip']].copy()
            prediction_df = df.drop(columns=['_src_ip', '_dst_ip'], errors='ignore')
            
            # Make predictions
            result = prediction_df.copy()
            try:
                probs = model.predict_proba(prediction_df)  # type: ignore
                if isinstance(probs, np.ndarray):
                    if probs.ndim == 1:
                        result['probability'] = probs
                    elif probs.ndim == 2:
                        if probs.shape[1] == 2:
                            result['probability'] = probs[:, 1]
                        elif probs.shape[1] == 1:
                            result['probability'] = probs.flatten()
                        else:
                            result['probability'] = (probs.argmax(axis=1) == 1).astype(float)
                    else:
                        result['probability'] = 0.0
                else:
                    result['probability'] = 0.0
            except Exception as e:
                print(f"  Warning: Prediction error: {e}")
                result['probability'] = 0.0
            
            result['prediction'] = result['probability'].apply(
                lambda p: 'ATTACK' if float(p) > 0.5 else 'Benign'
            )
            
            # Add IP info back for countermeasures
            result['_src_ip'] = ip_info['_src_ip'].values
            result['_dst_ip'] = ip_info['_dst_ip'].values
            
            # Print summary
            total_flows += len(result)
            attack_count = (result['prediction'] == 'ATTACK').sum()
            total_threats += attack_count
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Window #{window_count}: {len(result)} flows | "
                  f"Threats: {attack_count} | Total: {total_flows} flows, {total_threats} threats")
            
            if attack_count > 0:
                print("\n🚨 THREATS DETECTED:")
                for idx, row in result[result['prediction'] == 'ATTACK'].iterrows():
                    print(f"  ⚠️  Flow {idx}: Port {row['Destination Port']:5.0f} | "
                          f"Fwd Packets: {row['Total Fwd Packets']:3.0f} | "
                          f"Risk: {row['probability']*100:5.1f}%")
                    
                    # Send threat to countermeasure system
                    if countermeasure:
                        # Extract flow info (we need to map back to original flow)
                        # For now, use generic threat data
                        threat_data = {
                            'src_ip': 'unknown',  # Would need to track from flow_key
                            'dst_ip': 'unknown',
                            'dst_port': int(row['Destination Port']),
                            'protocol': 'TCP',
                            'probability': float(row['probability']),
                            'flow_packets': int(row['Total Fwd Packets']),
                            'flow_bytes': int(row['Total Length of Fwd Packets'])
                        }
                        countermeasure.process_threat(threat_data)
                print()
    
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("CAPTURE STOPPED")
        print("="*80)
        is_running = False
        
        # Stop Wireshark
        if wireshark_mgr:
            wireshark_mgr.stop()
        
        print(f"Windows analyzed: {window_count}")
        print(f"Total flows: {total_flows}")
        print(f"Total threats: {total_threats}")
        
        # Stop countermeasure system and show statistics
        if countermeasure:
            print()
            countermeasure.stop()
            countermeasure.print_statistics()
            
            # Ask user if they want to clear blocks
            try:
                response = input("\nClear all IP/port blocks? (y/n): ")
                if response.lower() == 'y':
                    countermeasure.clear_all_blocks()
            except Exception as e:
                pass  # Skip on error
        print("="*80)


def main():
    # Run system check first
    if CHECKER_AVAILABLE:
        checker = SystemChecker(verbose=True)
        all_passed = checker.check_all()
        if not all_passed:
            print("\n⚠️  WARNING: Some system checks failed. Continue anyway? (y/n): ", end='')
            try:
                response = input().strip().lower()
                if response != 'y':
                    print("Exiting...")
                    sys.exit(1)
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description='SecIDS-CNN Threat Detection: File-based or Continuous Live Capture'
    )
    
    # Mode selection
    subparsers = parser.add_subparsers(dest='mode', help='Detection mode')
    
    # File-based mode - now auto-uses datasets folder
    file_parser = subparsers.add_parser('file', help='Analyze CSV file(s) from datasets folder')
    file_parser.add_argument('csv_files', nargs='*', help='CSV file(s) to analyze (default: all CSVs in datasets folder)')
    file_parser.add_argument('--all', action='store_true', help='Process all CSV files in datasets folder')
    
    # Live capture mode
    live_parser = subparsers.add_parser('live', help='Continuous live traffic capture')
    live_parser.add_argument('--iface', required=True, help='Network interface (e.g., eth0, wlan0, any)')
    live_parser.add_argument('--window', type=float, default=120.0, help='Window size in seconds')
    live_parser.add_argument('--interval', type=float, default=120.0, help='Processing interval in seconds')
    live_parser.add_argument('--backend', choices=['tf', 'unified'], default='tf', help='Model backend to use (tf: SecIDS-CNN.h5, unified: Model_Tester unified model)')
    live_parser.add_argument('--model', default=str(script_dir / 'SecIDS-CNN.h5'), help='Model path')
    live_parser.add_argument('--no-countermeasure', action='store_true', help='Disable automatic countermeasures')
    
    args = parser.parse_args()
    
    # Check if mode was provided
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    # Initialize model
    print("Initializing the model...")
    backend = getattr(args, 'backend', 'tf') if hasattr(args, 'backend') else 'tf'
    model = None
    scaler = StandardScaler()

    if backend == 'tf':
        model = SecIDSModel()
        print("✓ TensorFlow SecIDS model loaded successfully\n")
    else:
        # Try to load unified model wrapper from Model_Tester
        try:
            master_code = script_dir.parent / 'Model_Tester' / 'Code'
            unified_wrapper_path = script_dir / 'unified_wrapper.py'
            # Add Model_Tester code dir to sys.path so wrapper can import if needed
            if str(master_code) not in sys.path:
                sys.path.insert(0, str(master_code))

            # Import wrapper from local SecIDS-CNN folder if present
            try:
                from unified_wrapper import UnifiedModelWrapper  # type: ignore
            except Exception:
                # Fallback: try to import from Model_Tester/Code
                from importlib import util
                wrapper_file = master_code / 'unified_threat_model.py'
                # If wrapper isn't present locally, we'll use unified_threat_model directly via a small loader
                from unified_threat_model import UnifiedThreatModel  # type: ignore
                class UnifiedModelWrapper:
                    def __init__(self, model_dir=None):
                        # If model_dir not provided, use Model_Tester Code/models
                        self.model_dir = model_dir or (master_code / 'models')
                        # load latest saved model components if available
                        self.unified = UnifiedThreatModel(model_dir=self.model_dir)
                        # Note: UnifiedThreatModel expects to be trained; predictions require scaler and models
                        # We'll attempt to load last saved scaler and models by scanning model_dir
                        # If not available, user should run training pipeline separately
                        pass

            # Instantiate wrapper and load latest model files
            wrapper = UnifiedModelWrapper(model_dir=str(master_code / 'models'))
            # wrapper should provide predict_proba and predict methods
            model = wrapper
            print("✓ Unified model backend selected (Model_Tester). Ensure models exist in Model_Tester/Code/models\n")
        except Exception as e:
            print(f"ERROR: Failed to initialize unified model backend: {e}")
            print("Falling back to TensorFlow SecIDS model")
            model = SecIDSModel()
    
    if args.mode == 'file':
        # Auto-detect CSV files from datasets folder if none specified
        datasets_dir = script_dir / 'datasets'
        
        if args.all or not args.csv_files:
            # Use all CSV files in datasets folder (excluding results files)
            csv_pattern = str(datasets_dir / '*.csv')
            all_csvs = glob.glob(csv_pattern)
            
            # Filter out result files
            csv_files = [f for f in all_csvs if 'detection_results' not in Path(f).name and 'file_detection' not in Path(f).name]
            
            if not csv_files:
                print(f"❌ No CSV files found in {datasets_dir}")
                print(f"\nPlease add dataset CSV files to: {datasets_dir}")
                sys.exit(1)
            
            print(f"📂 Auto-detected {len(csv_files)} CSV file(s) in datasets folder:")
            for csv_file in csv_files:
                print(f"   • {Path(csv_file).name}")
            print()
        else:
            # Use specified files (handle paths correctly)
            csv_files = []
            for csv_file in args.csv_files:
                csv_path = Path(csv_file)
                
                # If already absolute path, use as-is
                if csv_path.is_absolute():
                    if not csv_path.exists():
                        print(f"❌ File not found: {csv_path}")
                        sys.exit(1)
                    csv_files.append(str(csv_path))
                # If path starts with datasets/, use from script_dir
                elif str(csv_path).startswith('datasets/'):
                    full_path = script_dir / csv_path
                    if not full_path.exists():
                        print(f"❌ File not found: {full_path}")
                        sys.exit(1)
                    csv_files.append(str(full_path))
                # Otherwise, assume it's just a filename in datasets folder
                else:
                    full_path = datasets_dir / csv_path.name
                    if not full_path.exists():
                        print(f"❌ File not found: {full_path}")
                        sys.exit(1)
                    csv_files.append(str(full_path))
        
        run_file_based_detection(csv_files, model, scaler)
    elif args.mode == 'live':
        run_continuous_detection(args.iface, args.window, args.interval, model)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
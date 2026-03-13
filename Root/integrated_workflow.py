#!/usr/bin/env python3
"""
SecIDS-CNN Integrated Workflow System
======================================
Automatic end-to-end threat detection and response workflow:
1. Gather Data from live-traffic
2. Analyze the data for threats
3. Deploy Countermeasures
4. Create/Update model for future threat detection

This script provides systematic and reliable integration of all components.

Usage:
    # Full automatic workflow (60-second live capture)
    sudo python3 integrated_workflow.py --mode full --interface eth0 --duration 60
    
    # Continuous monitoring mode (runs indefinitely)
    sudo python3 integrated_workflow.py --mode continuous --interface eth0
    
    # Analyze existing capture
    python3 integrated_workflow.py --mode analyze --pcap-file Captures/capture_*.pcap
    
    # Train/retrain models from collected data
    python3 integrated_workflow.py --mode train
"""

import sys
import os
import time
import argparse
import threading
import queue
from pathlib import Path
from datetime import datetime
from collections import deque
import signal
import json
import subprocess

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECIDS_DIR = PROJECT_ROOT / 'SecIDS-CNN'
TOOLS_DIR = PROJECT_ROOT / 'Tools'
COUNTERMEASURES_DIR = PROJECT_ROOT / 'Countermeasures'
CAPTURES_DIR = PROJECT_ROOT / 'Captures'
RESULTS_DIR = PROJECT_ROOT / 'Results'
LOGS_DIR = PROJECT_ROOT / 'Logs'
FEEDBACK_DIR = RESULTS_DIR / 'Feedback'

# Add to Python path
sys.path.insert(0, str(SECIDS_DIR))
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(COUNTERMEASURES_DIR))
sys.path.insert(0, str(PROJECT_ROOT / 'Device_Profile'))

# Create directories
CAPTURES_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


class IntegratedWorkflow:
    """
    Integrated workflow manager that connects:
    - Live traffic capture
    - Threat detection
    - Automated countermeasures
    - Model retraining
    """
    
    def __init__(self, interface='eth0', duration=60, continuous=False):
        """
        Initialize integrated workflow
        
        Args:
            interface: Network interface to monitor
            duration: Capture duration in seconds (for single-run mode)
            continuous: If True, runs indefinitely
        """
        self.interface = interface
        self.duration = duration
        self.continuous = continuous
        self.running = False
        
        # Components
        self.model = None
        self.countermeasure = None
        self.greylist_manager = None
        self.capture_thread = None
        self.detection_thread = None
        self.improvement_thread = None
        
        # Data queues
        self.packet_queue = deque(maxlen=10000)
        self.threat_queue = queue.Queue()
        self.feedback_queue = queue.Queue()

        # Bottleneck controls
        self.max_flow_signature_cache = 5000
        self.recent_flow_signatures = deque()
        self.recent_flow_signature_set = set()
        self.last_countermeasure_backlog_log = 0.0

        # Improvement and progress tracking
        self.last_retrain_time = time.time()
        self.retrain_interval_hours = 24
        self.feedback_retrain_threshold = 40
        self.progress_file = RESULTS_DIR / 'workflow_stage_progress.json'
        self.feedback_file = FEEDBACK_DIR / 'countermeasure_feedback.csv'
        
        # Statistics
        self.stats = {
            'start_time': None,
            'packets_captured': 0,
            'flows_analyzed': 0,
            'threats_detected': 0,
            'threats_greylisted': 0,
            'threats_auto_blocked': 0,
            'countermeasures_deployed': 0,
            'captures_saved': [],
            'duplicate_flows_skipped': 0,
            'countermeasure_backlog_events': 0,
            'feedback_samples_ingested': 0,
            'feedback_samples_persisted': 0,
            'feedback_samples_used_for_training': 0,
            'improvement_cycles_completed': 0,
            'model_retrain_runs': 0,
            'model_retrain_success': 0
        }
        
        # Logging
        log_file = LOGS_DIR / f'integrated_workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        self.log_file = log_file
        
        # Handle signals
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.log("Integrated Workflow System Initialized")
        self.log(f"Interface: {interface}")
        self.log(f"Duration: {'Continuous' if continuous else f'{duration}s'}")

    def _write_progress(self, stage, status, details=None):
        """Persist stage progress for UI polling and log-driven notifications."""
        payload = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'status': status,
            'details': details or {}
        }
        try:
            with open(self.progress_file, 'w') as handle:
                json.dump(payload, handle, indent=2)
        except Exception as exc:
            self.log(f"Progress file write warning: {exc}", "WARNING")

    def _mark_stage(self, stage_code, stage_name, status="RUNNING", details=None):
        message = f"STAGE {stage_code}: {stage_name} [{status}]"
        level = "SUCCESS" if status == "COMPLETE" else "INFO"
        self.log(message, level)
        self._write_progress(f"{stage_code}-{stage_name}", status, details)

    def _is_duplicate_flow_signature(self, signature):
        if signature in self.recent_flow_signature_set:
            self.stats['duplicate_flows_skipped'] += 1
            return True

        self.recent_flow_signatures.append(signature)
        self.recent_flow_signature_set.add(signature)

        while len(self.recent_flow_signatures) > self.max_flow_signature_cache:
            stale = self.recent_flow_signatures.popleft()
            self.recent_flow_signature_set.discard(stale)

        return False

    def _queue_feedback_sample(self, threat_data, policy_decision, response_action, label):
        """Queue policy/response outcomes so model improvement can consume them."""
        feature_snapshot = threat_data.get('feature_snapshot', {})
        if not feature_snapshot:
            return

        sample = {
            **feature_snapshot,
            'is_attack': int(label),
            'src_ip': threat_data.get('src_ip', ''),
            'dst_ip': threat_data.get('dst_ip', ''),
            'probability': float(threat_data.get('probability', 0.0)),
            'policy_decision': policy_decision,
            'response_action': response_action,
            'feedback_timestamp': datetime.now().isoformat()
        }
        self.feedback_queue.put(sample)
        self.stats['feedback_samples_ingested'] += 1

    def _persist_feedback_batch(self):
        """Drain queued feedback samples and append them to durable CSV."""
        import pandas as pd

        batch = []
        while True:
            try:
                batch.append(self.feedback_queue.get_nowait())
            except queue.Empty:
                break

        if not batch:
            return 0

        df_new = pd.DataFrame(batch)
        if self.feedback_file.exists():
            df_old = pd.read_csv(self.feedback_file)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_all = df_new

        df_all.to_csv(self.feedback_file, index=False)
        self.stats['feedback_samples_persisted'] += len(batch)
        return len(batch)

    def _resolve_training_dataset(self):
        """Create a blended dataset containing existing data + policy/response feedback."""
        import pandas as pd

        if not self.feedback_file.exists():
            return None, 0

        df_feedback = pd.read_csv(self.feedback_file)
        if len(df_feedback) < self.feedback_retrain_threshold:
            return None, len(df_feedback)

        df_feedback = df_feedback[df_feedback['is_attack'].isin([0, 1])]
        if df_feedback.empty:
            return None, 0

        blend_path = SECIDS_DIR / 'datasets' / 'MD_feedback_blend.csv'
        master_dataset_path = SECIDS_DIR / 'datasets' / 'MD_1.csv'

        if not master_dataset_path.exists():
            metadata_columns = {'src_ip', 'dst_ip', 'policy_decision', 'response_action', 'feedback_timestamp'}
            feature_cols = [c for c in df_feedback.columns if c not in metadata_columns and c != 'is_attack']
            blend = df_feedback[feature_cols + ['is_attack']].copy()
            blend.to_csv(blend_path, index=False)
            return blend_path, len(blend)

        df_master = pd.read_csv(master_dataset_path)
        target_candidates = ['is_attack', 'Attack', 'attack', 'Label', 'Class', 'label', 'class']
        master_target = next((col for col in target_candidates if col in df_master.columns), 'is_attack')

        if master_target not in df_master.columns:
            df_master[master_target] = 0

        shared_features = [
            col for col in df_master.columns
            if col in df_feedback.columns and col != master_target and col != 'is_attack'
        ]

        if len(shared_features) < 5:
            return None, len(df_feedback)

        feedback_aligned = df_feedback[shared_features + ['is_attack']].copy()
        feedback_aligned = feedback_aligned.rename(columns={'is_attack': master_target})
        master_aligned = df_master[shared_features + [master_target]].copy()

        blend = pd.concat([master_aligned, feedback_aligned], ignore_index=True)
        blend.to_csv(blend_path, index=False)
        return blend_path, len(feedback_aligned)

    def _run_improvement_training(self, dataset_path, feedback_samples):
        """Run retraining using blended dataset and reload live model if successful."""
        self.stats['model_retrain_runs'] += 1
        self.log(f"🔄 Improvement retraining started using {dataset_path}", "INFO")

        env = os.environ.copy()
        env['SECIDS_DATASET_PATH'] = str(dataset_path)

        result = subprocess.run(
            [sys.executable, str(SECIDS_DIR / 'train_and_test.py')],
            capture_output=True,
            text=True,
            timeout=1800,
            env=env
        )

        if result.returncode != 0:
            self.log(f"⚠️ Improvement retraining failed: {result.stderr[:240]}", "WARNING")
            return False

        self.log("✓ Improvement retraining completed", "SUCCESS")
        self.stats['model_retrain_success'] += 1
        self.stats['feedback_samples_used_for_training'] += int(feedback_samples)

        try:
            unified_train = PROJECT_ROOT / 'Model_Tester' / 'Code' / 'train_unified_model.py'
            if unified_train.exists():
                unified_result = subprocess.run(
                    [sys.executable, str(unified_train)],
                    capture_output=True,
                    text=True,
                    timeout=1500
                )
                if unified_result.returncode == 0:
                    self.log("✓ Model Tester unified model refreshed with new threat patterns", "SUCCESS")
                else:
                    self.log(f"⚠️ Unified model refresh failed: {unified_result.stderr[:200]}", "WARNING")
        except Exception as exc:
            self.log(f"⚠️ Unified model refresh skipped: {exc}", "WARNING")

        try:
            from secids_cnn import SecIDSModel
            self.model = SecIDSModel()
            self.log("✓ Updated detection model hot-reloaded", "SUCCESS")
        except Exception as exc:
            self.log(f"⚠️ Model reload warning: {exc}", "WARNING")

        return True

    def process_improvement_stage(self):
        """
        STAGE D: Continuous improvement loop.
        - Persists policy/response feedback
        - Triggers retraining when enough new signals are collected
        """
        self.log("\n" + "="*80)
        self.log("STAGE D: IMPROVEMENT LOOP")
        self.log("="*80)
        self._mark_stage('D', 'Improvement', 'RUNNING')

        while self.running:
            try:
                persisted = self._persist_feedback_batch()
                if persisted > 0:
                    self.log(f"✓ Persisted {persisted} policy/response feedback samples", "INFO")

                elapsed_hours = (time.time() - self.last_retrain_time) / 3600
                if elapsed_hours >= self.retrain_interval_hours or persisted >= self.feedback_retrain_threshold:
                    dataset_path, feedback_samples = self._resolve_training_dataset()
                    if dataset_path is not None:
                        self._mark_stage('D', 'Improvement', 'RUNNING', {
                            'operation': 'model_retraining',
                            'dataset': str(dataset_path)
                        })
                        if self._run_improvement_training(dataset_path, feedback_samples):
                            self.last_retrain_time = time.time()

                self.stats['improvement_cycles_completed'] += 1
                time.sleep(30)
            except Exception as exc:
                self.log(f"Improvement loop error: {exc}", "ERROR")
                time.sleep(5)
    
    def log(self, message, level="INFO"):
        """Write to log file and print"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            # Log file write failed - print to stderr
            import sys
            print(f"Warning: Could not write to log file: {e}", file=sys.stderr)
    
    def _signal_handler(self, sig, frame):
        """Handle SIGINT and SIGTERM"""
        self.log("\nReceived shutdown signal", "INFO")
        self.stop()
    
    def initialize_components(self):
        """Initialize all system components"""
        self.log("\n" + "="*80)
        self.log("STAGE 1: COMPONENT INITIALIZATION")
        self.log("="*80)
        
        # 1. Load detection model
        try:
            from secids_cnn import SecIDSModel
            self.model = SecIDSModel()
            self.log("✓ SecIDS-CNN model loaded", "SUCCESS")
        except Exception as e:
            self.log(f"✗ Failed to load model: {e}", "ERROR")
            return False
        
        # 2. Initialize countermeasure system
        try:
            from ddos_countermeasure import DDoSCountermeasure
            self.countermeasure = DDoSCountermeasure(
                block_threshold=5,
                auto_block=True
            )
            self.countermeasure.start()
            self.log("✓ Countermeasure system initialized", "SUCCESS")
        except Exception as e:
            self.log(f"⚠️  Countermeasure system not available: {e}", "WARNING")
            self.countermeasure = None
        
        # 3. Initialize greylist manager
        try:
            from greylist_manager import GreylistManager
            self.greylist_manager = GreylistManager()
            self.log("✓ Greylist manager initialized", "SUCCESS")
        except Exception as e:
            self.log(f"⚠️  Greylist manager not available: {e}", "WARNING")
            self.greylist_manager = None
        
        return True
    
    def start_live_capture(self):
        """
        STAGE A: Gathering intelligence via live traffic capture
        Continuously captures packets from network interface
        """
        self.log("\n" + "="*80)
        self.log("STAGE A: GATHERING INTELLIGENCE")
        self.log("="*80)
        self._mark_stage('A', 'Gathering Intelligence', 'RUNNING')
        
        try:
            from scapy.all import sniff, IP, wrpcap
        except ImportError:
            self.log("✗ Scapy not available. Install: pip install scapy", "ERROR")
            return False
        
        # Start packet capture in background
        def capture_packets():
            timestamp = int(time.time())
            pcap_file = CAPTURES_DIR / f'capture_{timestamp}.pcap'
            self.stats['captures_saved'].append(str(pcap_file))
            
            self.log(f"Starting capture on {self.interface}...")
            self.log(f"Output: {pcap_file}")
            
            packets = []
            
            def packet_callback(pkt):
                if not self.running:
                    return
                
                if pkt.haslayer(IP):
                    packets.append(pkt)
                    self.packet_queue.append((time.time(), pkt))
                    self.stats['packets_captured'] += 1
            
            try:
                # Capture for specified duration or until stopped
                if self.continuous:
                    sniff(
                        iface=self.interface,
                        prn=packet_callback,
                        store=False,
                        stop_filter=lambda x: not self.running
                    )
                else:
                    sniff(
                        iface=self.interface,
                        prn=packet_callback,
                        store=False,
                        timeout=self.duration,
                        stop_filter=lambda x: not self.running
                    )
                
                # Save captured packets
                if packets:
                    wrpcap(str(pcap_file), packets)
                    self.log(f"✓ Saved {len(packets)} packets to {pcap_file}", "SUCCESS")
                    self._mark_stage('A', 'Gathering Intelligence', 'COMPLETE', {
                        'packets_saved': len(packets),
                        'capture_file': str(pcap_file)
                    })
            
            except PermissionError:
                self.log(f"✗ Permission denied. Run with sudo", "ERROR")
                self.running = False
            except Exception as e:
                self.log(f"✗ Capture error: {e}", "ERROR")
                self.running = False
        
        self.capture_thread = threading.Thread(target=capture_packets, daemon=True)
        self.capture_thread.start()
        self.log("✓ Capture thread started", "SUCCESS")
        
        return True
    
    def start_threat_detection(self):
        """
        STAGE B: Detect threats in real-time
        Processes captured packets and detects threats
        """
        self.log("\n" + "="*80)
        self.log("STAGE B: DETECTING THREAT")
        self.log("="*80)
        self._mark_stage('B', 'Detecting Threat', 'RUNNING')
        
        from scapy.all import IP, TCP, UDP
        import pandas as pd
        import numpy as np
        from collections import defaultdict
        
        def detect_threats():
            window_size = 60.0  # 60-second windows
            base_interval = 30.0
            
            while self.running:
                # Adaptive interval helps prevent bottlenecks when response queue grows.
                backlog = self.threat_queue.qsize()
                interval = base_interval + min(30.0, backlog * 0.15)
                time.sleep(interval)
                
                # Get packets from current window
                current_time = time.time()
                cutoff = current_time - window_size
                
                # Extract packets within window
                packet_list = []
                while self.packet_queue and self.packet_queue[0][0] < cutoff:
                    self.packet_queue.popleft()
                
                packet_list = list(self.packet_queue)
                
                if not packet_list:
                    continue
                
                # Convert packets to flows
                flows = {}
                
                for ts, pkt in packet_list:
                    if not pkt.haslayer(IP):
                        continue
                    
                    ip_layer = pkt[IP]
                    sport, dport, proto = None, None, None
                    
                    if pkt.haslayer(TCP):
                        proto = 'TCP'
                        sport = pkt[TCP].sport
                        dport = pkt[TCP].dport
                    elif pkt.haslayer(UDP):
                        proto = 'UDP'
                        sport = pkt[UDP].sport
                        dport = pkt[UDP].dport
                    else:
                        continue
                    
                    flow_key = (ip_layer.src, ip_layer.dst, sport, dport, proto)
                    
                    if flow_key not in flows:
                        flows[flow_key] = {
                            'first_ts': ts,
                            'last_ts': ts,
                            'fwd_pkts': [],
                            'bwd_pkts': [],
                            'dst_port': dport,
                            'src_ip': ip_layer.src,
                            'dst_ip': ip_layer.dst,
                            'fwd_id': (ip_layer.src, sport)
                        }
                    
                    flow = flows[flow_key]
                    if not isinstance(flow['fwd_pkts'], list):
                        flow['fwd_pkts'] = []
                    if not isinstance(flow['bwd_pkts'], list):
                        flow['bwd_pkts'] = []
                    flow['last_ts'] = max(flow['last_ts'], ts)
                    
                    pkt_len = len(pkt)
                    flags = pkt[TCP].flags if pkt.haslayer(TCP) else None
                    
                    if (ip_layer.src, sport) == flow['fwd_id']:
                        flow['fwd_pkts'].append((ts, pkt_len, flags))
                    else:
                        flow['bwd_pkts'].append((ts, pkt_len, flags))
                
                # Extract features and predict
                rows = []
                for flow_key, flow in flows.items():
                    duration_s = max(1e-6, flow['last_ts'] - flow['first_ts'])
                    fwd_pkts = flow.get('fwd_pkts', [])
                    if not isinstance(fwd_pkts, list):
                        fwd_pkts = []
                    
                    total_fwd_packets = len(fwd_pkts)
                    total_length_fwd = sum(p[1] for p in fwd_pkts) if fwd_pkts else 0
                    
                    flow_bytes_per_s = total_length_fwd / duration_s
                    flow_pkts_per_s = total_fwd_packets / duration_s
                    avg_pkt_size = (total_length_fwd / total_fwd_packets) if total_fwd_packets > 0 else 0
                    
                    pkt_lengths = [p[1] for p in fwd_pkts] if fwd_pkts else [0]
                    pkt_len_std = float(np.std(pkt_lengths)) if len(pkt_lengths) > 1 else 0.0
                    
                    fin_count = sum(1 for (_, _, f) in fwd_pkts if f and 'F' in str(f))
                    ack_count = sum(1 for (_, _, f) in fwd_pkts if f and 'A' in str(f))

                    flow_signature = (
                        flow['src_ip'],
                        flow['dst_ip'],
                        int(flow['dst_port']),
                        int(total_fwd_packets),
                        int(total_length_fwd),
                        int(fin_count),
                        int(ack_count)
                    )
                    if self._is_duplicate_flow_signature(flow_signature):
                        continue
                    
                    rows.append({
                        'Destination Port': int(flow['dst_port']),
                        'Flow Duration': int((flow['last_ts'] - flow['first_ts']) * 1e6),
                        'Total Fwd Packets': int(total_fwd_packets),
                        'Total Length of Fwd Packets': int(total_length_fwd),
                        'Flow Bytes/s': float(flow_bytes_per_s),
                        'Flow Packets/s': float(flow_pkts_per_s),
                        'Average Packet Size': float(avg_pkt_size),
                        'Packet Length Std': float(pkt_len_std),
                        'FIN Flag Count': int(fin_count),
                        'ACK Flag Count': int(ack_count),
                        '_src_ip': flow['src_ip'],
                        '_dst_ip': flow['dst_ip']
                    })
                
                if not rows:
                    continue
                
                df = pd.DataFrame(rows)
                self.stats['flows_analyzed'] += len(df)
                
                # Extract IP info
                ip_info = df[['_src_ip', '_dst_ip']].copy()
                prediction_df = df.drop(columns=['_src_ip', '_dst_ip'])
                
                # Make predictions
                try:
                    if self.model is None:
                        self.log("Model not loaded, skipping predictions", "WARNING")
                        continue
                    probs = self.model.predict_proba(prediction_df)
                    if isinstance(probs, np.ndarray) and probs.ndim == 2 and probs.shape[1] == 2:
                        prediction_df['probability'] = probs[:, 1]
                    else:
                        prediction_df['probability'] = probs
                except Exception as e:
                    self.log(f"Prediction error: {e}", "WARNING")
                    continue
                
                prediction_df['prediction'] = prediction_df['probability'].apply(
                    lambda p: 'ATTACK' if float(p) > 0.5 else 'Benign'
                )
                
                # Add IP info back
                prediction_df['_src_ip'] = ip_info['_src_ip'].values
                prediction_df['_dst_ip'] = ip_info['_dst_ip'].values
                
                # Process threats
                attacks = prediction_df[prediction_df['prediction'] == 'ATTACK']
                
                if len(attacks) > 0:
                    self.stats['threats_detected'] += len(attacks)
                    self.log(f"🚨 THREATS DETECTED: {len(attacks)} malicious flows", "ALERT")
                    
                    # Process each threat through greylist system
                    for idx, row in attacks.iterrows():
                        threat_data = {
                            'timestamp': datetime.now().isoformat(),
                            'src_ip': row['_src_ip'],
                            'dst_ip': row['_dst_ip'],
                            'dst_port': int(row['Destination Port']),
                            'probability': float(row['probability']),
                            'flow_packets': int(row['Total Fwd Packets']),
                            'flow_bytes': int(row['Total Length of Fwd Packets']),
                            'policy_decision': 'unknown',
                            'feature_snapshot': {
                                'Destination Port': int(row['Destination Port']),
                                'Flow Duration': int(row['Flow Duration']),
                                'Total Fwd Packets': int(row['Total Fwd Packets']),
                                'Total Length of Fwd Packets': int(row['Total Length of Fwd Packets']),
                                'Flow Bytes/s': float(row['Flow Bytes/s']),
                                'Flow Packets/s': float(row['Flow Packets/s']),
                                'Average Packet Size': float(row['Average Packet Size']),
                                'Packet Length Std': float(row['Packet Length Std']),
                                'FIN Flag Count': int(row['FIN Flag Count']),
                                'ACK Flag Count': int(row['ACK Flag Count'])
                            }
                        }
                        
                        # Use greylist classification if available
                        if self.greylist_manager:
                            classification, needs_decision = self.greylist_manager.process_threat(threat_data)
                            
                            if classification == 'greylist':
                                threat_data['policy_decision'] = 'greylist_pending'
                                self.stats['threats_greylisted'] += 1
                                self.log(f"  ⚠️  GREYLIST: {row['_src_ip']} → Port {row['Destination Port']} (Risk: {row['probability']*100:.1f}%) - User decision required", "WARNING")
                                # Don't add to countermeasure queue - will be handled by user decision
                            elif classification == 'blacklist':
                                threat_data['policy_decision'] = 'blacklist_auto'
                                self.stats['threats_auto_blocked'] += 1
                                self.threat_queue.put(threat_data)
                                self.log(f"  🚫 BLACKLIST: {row['_src_ip']} → Port {row['Destination Port']} (Risk: {row['probability']*100:.1f}%) - Auto-blocking", "ALERT")
                            else:  # whitelist
                                threat_data['policy_decision'] = 'whitelist'
                                self._queue_feedback_sample(
                                    threat_data,
                                    policy_decision='whitelist',
                                    response_action='monitor_only',
                                    label=0
                                )
                                self.log(f"  ✓ WHITELIST: {row['_src_ip']} → Port {row['Destination Port']} (Risk: {row['probability']*100:.1f}%) - Benign", "INFO")
                        else:
                            # No greylist manager - send all threats to countermeasures
                            threat_data['policy_decision'] = 'countermeasure_direct'
                            self.threat_queue.put(threat_data)
                            self.log(f"  ⚠️  Threat from {row['_src_ip']} → Port {row['Destination Port']} (Risk: {row['probability']*100:.1f}%)", "ALERT")
        
        self.detection_thread = threading.Thread(target=detect_threats, daemon=True)
        self.detection_thread.start()
        self.log("✓ Detection thread started", "SUCCESS")
        
        return True
    
    def process_countermeasures(self):
        """
        STAGE C: Deploy countermeasures against detected threats
        Automatically blocks malicious IPs and ports (blacklist only)
        """
        self.log("\n" + "="*80)
        self.log("STAGE C: COUNTERMEASURES")
        self.log("="*80)
        self._mark_stage('C', 'Countermeasures', 'RUNNING')
        
        if not self.countermeasure:
            self.log("⚠️  Countermeasures disabled", "WARNING")
            return
        
        while self.running:
            try:
                # Batch process improves throughput when threat queue spikes.
                first_threat = self.threat_queue.get(timeout=1)
                batch = [first_threat]
                while len(batch) < 25:
                    try:
                        batch.append(self.threat_queue.get_nowait())
                    except queue.Empty:
                        break

                if self.threat_queue.qsize() > 50 and (time.time() - self.last_countermeasure_backlog_log) > 15:
                    self.last_countermeasure_backlog_log = time.time()
                    self.stats['countermeasure_backlog_events'] += 1
                    self.log(f"⚙️ Countermeasure backlog detected (queue={self.threat_queue.qsize()}) - batch mode active", "WARNING")

                for threat_data in batch:
                    src_ip = threat_data.get('src_ip', 'unknown')
                    if self.greylist_manager and self.greylist_manager.is_greylisted(src_ip):
                        self.log(f"⚠️  Skipping countermeasure for greylisted IP: {src_ip}", "WARNING")
                        self.threat_queue.task_done()
                        continue

                    self.countermeasure.process_threat(threat_data)
                    self.stats['countermeasures_deployed'] += 1
                    self._queue_feedback_sample(
                        threat_data,
                        policy_decision=threat_data.get('policy_decision', 'countermeasure_applied'),
                        response_action='countermeasure_deployed',
                        label=1
                    )

                    self.log(f"✓ Countermeasure deployed for {threat_data['src_ip']}", "ACTION")
                    self.threat_queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                self.log(f"Countermeasure error: {e}", "ERROR")
    
    def process_greylist_decisions(self):
        """
        STAGE C2: Handle greylist decisions interactively
        Prompts user for action on potential threats
        """
        self.log("\n" + "="*80)
        self.log("STAGE C2: GREYLIST DECISION PROCESSOR")
        self.log("="*80)
        
        if not self.greylist_manager:
            self.log("⚠️  Greylist manager not available", "WARNING")
            return
        
        from greylist_manager import prompt_user_decision
        
        while self.running:
            try:
                # Check for pending decisions
                pending = self.greylist_manager.get_pending_decision(timeout=5)
                
                if pending:
                    # Prompt user for decision
                    action = prompt_user_decision(self.greylist_manager, pending)
                    
                    self.log(f"✓ Decision recorded: {action['message']}", "INFO")
                    
                    # If user chose to blacklist, deploy countermeasures
                    if action.get('decision') == 'blacklist':
                        threat_data = pending['threat_data']
                        threat_data['policy_decision'] = 'blacklist_manual'
                        self.threat_queue.put(threat_data)
                        self.log(f"→ Queued for countermeasures: {action['ip']}", "ACTION")
                    elif action.get('decision') == 'whitelist':
                        threat_data = pending['threat_data']
                        threat_data['policy_decision'] = 'whitelist_manual'
                        self._queue_feedback_sample(
                            threat_data,
                            policy_decision='whitelist_manual',
                            response_action='monitor_only',
                            label=0
                        )
            
            except Exception as e:
                self.log(f"Greylist decision error: {e}", "ERROR")
                time.sleep(1)
    
    def run(self):
        """Run integrated workflow"""
        self.running = True
        self.stats['start_time'] = datetime.now().isoformat()
        
        print("\n" + "="*80)
        print("  SecIDS-CNN INTEGRATED WORKFLOW SYSTEM")
        print("="*80)
        print(f"  Mode: {'Continuous Monitoring' if self.continuous else f'Single Run ({self.duration}s)'}")
        print(f"  Interface: {self.interface}")
        print("="*80 + "\n")
        
        # Initialize all components
        if not self.initialize_components():
            self.log("✗ Initialization failed", "ERROR")
            return False
        
        # Start all stages
        if not self.start_live_capture():
            self.log("✗ Capture failed", "ERROR")
            return False
        
        if not self.start_threat_detection():
            self.log("✗ Detection failed", "ERROR")
            return False
        
        # Start countermeasure processor
        countermeasure_thread = threading.Thread(target=self.process_countermeasures, daemon=True)
        countermeasure_thread.start()
        
        # Start greylist decision processor
        if self.greylist_manager:
            greylist_thread = threading.Thread(target=self.process_greylist_decisions, daemon=True)
            greylist_thread.start()
            self.log("✓ Greylist decision processor started", "SUCCESS")
        
        # Start stage D improvement loop
        self.improvement_thread = threading.Thread(target=self.process_improvement_stage, daemon=True)
        self.improvement_thread.start()
        
        # Monitor status
        try:
            if self.continuous:
                self.log("\n✓ All systems operational - Running continuously (Ctrl+C to stop)\n")
                
                # Print status every minute
                while self.running:
                    time.sleep(60)
                    self.print_status()
            else:
                self.log(f"\n✓ All systems operational - Running for {self.duration} seconds\n")
                
                # Wait for duration
                for i in range(self.duration):
                    if not self.running:
                        break
                    time.sleep(1)
                
                self.stop()
        
        except KeyboardInterrupt:
            self.log("\nShutdown requested", "INFO")
            self.stop()
        
        return True
    
    def print_status(self):
        """Print current system status"""
        print("\n" + "="*80)
        print("  SYSTEM STATUS")
        print("="*80)
        print(f"  Packets Captured: {self.stats['packets_captured']:,}")
        print(f"  Flows Analyzed: {self.stats['flows_analyzed']:,}")
        print(f"  Threats Detected: {self.stats['threats_detected']}")
        print(f"    ├─ Auto-blocked (Blacklist): {self.stats['threats_auto_blocked']}")
        print(f"    ├─ Pending Decision (Greylist): {self.stats['threats_greylisted']}")
        print(f"    └─ False Positives (Whitelist): {self.stats['threats_detected'] - self.stats['threats_auto_blocked'] - self.stats['threats_greylisted']}")
        print(f"  Countermeasures Deployed: {self.stats['countermeasures_deployed']}")
        
        if self.greylist_manager:
            greylist_stats = self.greylist_manager.get_statistics()
            print(f"  Greylist Status:")
            print(f"    ├─ Current size: {greylist_stats['current_greylist_size']}")
            print(f"    ├─ Pending decisions: {greylist_stats['pending_decisions']}")
            print(f"    ├─ Moved to blacklist: {greylist_stats['moved_to_blacklist']}")
            print(f"    ├─ Moved to whitelist: {greylist_stats['moved_to_whitelist']}")
            print(f"    └─ Kept monitoring: {greylist_stats['kept_on_greylist']}")
        
        print("="*80 + "\n")
    
    def stop(self):
        """Stop integrated workflow"""
        self.log("\n" + "="*80)
        self.log("SHUTTING DOWN INTEGRATED WORKFLOW")
        self.log("="*80)
        
        self.running = False
        
        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.log("Stopping capture thread...")
            self.capture_thread.join(timeout=5)
        
        if self.detection_thread and self.detection_thread.is_alive():
            self.log("Stopping detection thread...")
            self.detection_thread.join(timeout=5)

        if self.improvement_thread and self.improvement_thread.is_alive():
            self.log("Stopping improvement thread...")
            self.improvement_thread.join(timeout=5)
        
        # Stop countermeasure system
        if self.countermeasure:
            self.countermeasure.stop()
            self.countermeasure.print_statistics()
            
            # Ask to clear blocks
            try:
                response = input("\nClear all IP/port blocks? (y/n): ")
                if response.lower() == 'y':
                    self.countermeasure.clear_all_blocks()
            except (KeyboardInterrupt, EOFError):
                self.log("Skipping block-clear prompt due to interrupted input", "WARNING")
        
        # Show greylist statistics and export report
        if self.greylist_manager:
            self.greylist_manager.print_statistics()
            self.greylist_manager.export_report()
        
        # Save final statistics
        try:
            persisted = self._persist_feedback_batch()
            if persisted > 0:
                self.log(f"✓ Final feedback flush persisted {persisted} samples", "SUCCESS")
        except Exception as exc:
            self.log(f"Final feedback flush warning: {exc}", "WARNING")

        self._mark_stage('D', 'Improvement', 'COMPLETE', {
            'feedback_samples_persisted': self.stats['feedback_samples_persisted'],
            'model_retrain_success': self.stats['model_retrain_success']
        })

        self.save_statistics()
        
        self.log("✓ Shutdown complete", "SUCCESS")
    
    def save_statistics(self):
        """Save workflow statistics"""
        stats_file = RESULTS_DIR / f'workflow_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        self.log(f"✓ Statistics saved to {stats_file}", "SUCCESS")
        
        # Print summary
        print("\n" + "="*80)
        print("  WORKFLOW SUMMARY")
        print("="*80)
        print(f"  Start Time: {self.stats['start_time']}")
        print(f"  Packets Captured: {self.stats['packets_captured']:,}")
        print(f"  Flows Analyzed: {self.stats['flows_analyzed']:,}")
        print(f"  Threats Detected: {self.stats['threats_detected']}")
        print(f"  Countermeasures Deployed: {self.stats['countermeasures_deployed']}")
        print(f"  Duplicate Flows Skipped: {self.stats['duplicate_flows_skipped']}")
        print(f"  Countermeasure Backlog Events: {self.stats['countermeasure_backlog_events']}")
        print(f"  Feedback Samples Persisted: {self.stats['feedback_samples_persisted']}")
        print(f"  Feedback Samples Used for Training: {self.stats['feedback_samples_used_for_training']}")
        print(f"  Model Retrain Successes: {self.stats['model_retrain_success']}")
        print(f"  Captures Saved: {len(self.stats['captures_saved'])}")
        print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='SecIDS-CNN Integrated Workflow System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full automatic workflow (60-second capture)
  sudo python3 integrated_workflow.py --mode full --interface eth0 --duration 60
  
  # Continuous monitoring mode
  sudo python3 integrated_workflow.py --mode continuous --interface eth0
  
  # Quick test (30 seconds)
  sudo python3 integrated_workflow.py --mode full --interface eth0 --duration 30
        """
    )
    
    parser.add_argument('--mode', choices=['full', 'continuous'], required=True,
                       help='Workflow mode: full (single run) or continuous (runs indefinitely)')
    parser.add_argument('--interface', '-i', required=True,
                       help='Network interface to monitor (e.g., eth0, wlan0)')
    parser.add_argument('--duration', '-d', type=int, default=60,
                       help='Capture duration in seconds (for full mode, default: 60)')
    
    args = parser.parse_args()
    
    # Check for root privileges
    if os.geteuid() != 0:
        print("⚠️  WARNING: Root privileges required for packet capture")
        print("Please run with: sudo python3 integrated_workflow.py ...")
        sys.exit(1)
    
    # Create workflow
    workflow = IntegratedWorkflow(
        interface=args.interface,
        duration=args.duration,
        continuous=(args.mode == 'continuous')
    )
    
    # Run workflow
    success = workflow.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

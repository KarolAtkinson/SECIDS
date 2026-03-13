#!/usr/bin/env python3
"""
Continuous live traffic capture from Wireshark with real-time threat detection.

This script continuously captures network traffic from a specified interface,
processes it in sliding time windows, and runs the SecIDS-CNN model to detect
threats in real-time.

Usage:
  python3 tools/continuous_live_capture.py --iface eth0 --window 5 --interval 2
  
  - Capture 5-second windows of traffic
  - Process every 2 seconds (overlapping windows for continuous detection)
  - Display real-time threat alerts
  - Auto-start/stop Wireshark for the session

Requirements:
  - Scapy: pip install scapy
  - Wireshark/tshark or dumpcap (auto-managed by wireshark_manager)
  - All dependencies from SecIDS-CNN
"""

import argparse
import sys
import time
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime
import threading

import pandas as pd
import numpy as np

try:
    from scapy.all import sniff, IP, TCP, UDP  # type: ignore
except ImportError:
    print("ERROR: Scapy is required. Install it with: pip install scapy")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SECIDS_DIR = PROJECT_ROOT / 'SecIDS-CNN'
COUNTERMEASURES_DIR = PROJECT_ROOT / 'Countermeasures'
DEVICE_PROFILE_DIR = PROJECT_ROOT / 'Device_Profile' / 'device_info'
TOOLS_DIR = PROJECT_ROOT / 'Tools'

if str(SECIDS_DIR) not in sys.path:
    sys.path.insert(0, str(SECIDS_DIR))
if str(COUNTERMEASURES_DIR) not in sys.path:
    sys.path.insert(0, str(COUNTERMEASURES_DIR))
if str(DEVICE_PROFILE_DIR) not in sys.path:
    sys.path.insert(0, str(DEVICE_PROFILE_DIR))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from secids_cnn import SecIDSModel  # type: ignore
from ddos_countermeasure import DDoSCountermeasure  # type: ignore
from whitelist_checker import WhitelistChecker  # type: ignore
from blacklist_manager import BlacklistManager  # type: ignore

# Import Wireshark manager and progress utilities
try:
    from wireshark_manager import WiresharkManager
    from progress_utils import CaptureProgress
    WIRESHARK_AVAILABLE = True
except ImportError:
    WIRESHARK_AVAILABLE = False
    print("⚠️  Wireshark manager not available")


class LivePacketCapture:
    """Captures packets from the network interface in real-time."""
    
    def __init__(self, interface, window_size=120.0, interval=120.0):
        self.interface = interface
        self.window_size = window_size
        self.interval = interval
        self.packets = deque()
        self.lock = threading.Lock()
        self.is_running = False
        self.start_time = None
        
    def packet_callback(self, packet):
        """Called for each captured packet."""
        if not packet.haslayer(IP):
            return
            
        with self.lock:
            self.packets.append((time.time(), packet))
            
    def get_window_packets(self):
        """Get all packets from the current window."""
        current_time = time.time()
        cutoff = current_time - self.window_size
        
        with self.lock:
            # Remove old packets
            while self.packets and self.packets[0][0] < cutoff:
                self.packets.popleft()
            
            # Return packets in current window
            return list(self.packets)
    
    def start_capture(self):
        """Start capturing packets in a background thread."""
        self.is_running = True
        self.start_time = time.time()
        
        capture_thread = threading.Thread(
            target=self._sniff_thread,
            daemon=True
        )
        capture_thread.start()
        return capture_thread
    
    def _sniff_thread(self):
        """Background thread for packet capture."""
        try:
            sniff(
                iface=self.interface,
                prn=self.packet_callback,
                store=False,
                stop_filter=lambda x: not self.is_running
            )
        except PermissionError:
            print(f"ERROR: Insufficient permissions to capture on {self.interface}")
            print("Try running with sudo or use: setcap cap_net_raw=ep $(which python3)")
            self.is_running = False
        except Exception as e:
            print(f"Capture error: {e}")
            self.is_running = False
    
    def stop_capture(self):
        """Stop the packet capture."""
        self.is_running = False


def packets_to_dataframe(packet_tuples):
    """Convert captured packet tuples to SecIDS-CNN format DataFrame."""
    
    flows = defaultdict(lambda: {
        'fwd_pkts': [],
        'bwd_pkts': [],
        'dst_port': 0,
    })
    
    for ts, pkt in packet_tuples:
        if not pkt.haslayer(IP):
            continue
            
        ip_layer = pkt[IP]
        proto = None
        sport = None
        dport = None
        
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
            flags = None
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
            }
        
        flow = flows[flow_key]
        flow['last_ts'] = max(flow['last_ts'], ts)
        
        # Classify packet direction
        if (ip_layer.src, sport) == flow['fwd_id']:
            flow['fwd_pkts'].append((ts, pkt_len, flags if pkt.haslayer(TCP) else None))
        else:
            flow['bwd_pkts'].append((ts, pkt_len, flags if pkt.haslayer(TCP) else None))
    
    # Convert flows to DataFrame
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
        for (_, _, flags) in fwd_pkts:  # type: ignore
            if flags is None:
                continue
            try:
                flag_str = str(flags)
                if 'F' in flag_str:
                    fin_count += 1
                if 'A' in flag_str:
                    ack_count += 1
            except (ValueError, TypeError):
                # Cannot convert flags to string
                continue
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
        })
    
    if not rows:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=[
            'Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Length of Fwd Packets',
            'Flow Bytes/s', 'Flow Packets/s', 'Average Packet Size', 'Packet Length Std',
            'FIN Flag Count', 'ACK Flag Count'
        ])
    
    df = pd.DataFrame(rows)
    desired_cols = [
        'Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Length of Fwd Packets',
        'Flow Bytes/s', 'Flow Packets/s', 'Average Packet Size', 'Packet Length Std',
        'FIN Flag Count', 'ACK Flag Count'
    ]
    
    for col in desired_cols:
        if col not in df.columns:
            df[col] = 0
    
    return df[desired_cols]


def assess_traffic(df, model):
    """Run threat detection on captured traffic."""
    if df.empty or len(df) == 0:
        return pd.DataFrame()
    
    try:
        probs = model.predict_proba(df)
    except Exception as e:
        print(f"Prediction error: {e}")
        return df
    
    # Process predictions
    result = df.copy()
    
    if probs is None:
        result['probability'] = 0.0
    elif isinstance(probs, np.ndarray):
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
    
    result['prediction'] = result['probability'].apply(
        lambda p: 'ATTACK' if float(p) > 0.5 else 'Benign'
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Continuous live network traffic capture with real-time threat detection'
    )
    parser.add_argument('--iface', required=True, help='Network interface to capture from (e.g., eth0, wlan0)')
    parser.add_argument('--window', type=float, default=120.0, help='Capture window size in seconds')
    parser.add_argument('--interval', type=float, default=120.0, help='Processing interval in seconds')
    parser.add_argument('--model', default=str(SECIDS_DIR / 'SecIDS-CNN.h5'), help='Path to SecIDS model')
    parser.add_argument('--enable-countermeasure', action='store_true', help='Enable automatic countermeasures')
    parser.add_argument('--block-threshold', type=int, default=5, help='Threats before blocking IP (default: 5)')
    parser.add_argument('--auto-block', action='store_true', help='Automatically block threats')
    parser.add_argument('--enable-whitelist', action='store_true', help='Enable whitelist filtering (reduces false positives)')
    parser.add_argument('--enable-blacklist', action='store_true', help='Enable blacklist tracking (remember threats)')
    args = parser.parse_args()
    
    print("="*80)
    print("CONTINUOUS LIVE NETWORK THREAT DETECTION (Wireshark/Scapy Based)")
    print("="*80)
    print(f"Interface: {args.iface}")
    print(f"Window size: {args.window}s")
    print(f"Processing interval: {args.interval}s")
    print(f"Model: {args.model}")
    print(f"Countermeasures: {'ENABLED' if args.enable_countermeasure else 'DISABLED'}")
    if args.enable_countermeasure:
        print(f"Block threshold: {args.block_threshold} threats")
        print(f"Auto-block: {'YES' if args.auto_block else 'NO'}")
    print(f"Whitelist Filter: {'ENABLED' if args.enable_whitelist else 'DISABLED'}")
    print(f"Blacklist Tracking: {'ENABLED' if args.enable_blacklist else 'DISABLED'}")
    print("="*80)
    
    # Start Wireshark with auto-management
    wireshark_mgr = None
    if WIRESHARK_AVAILABLE:
        try:
            print("\n🦈 Starting Wireshark for live capture...")
            use_any = args.iface.lower() == 'any'
            wireshark_mgr = WiresharkManager(interface=args.iface, use_any=use_any)
            wireshark_mgr.start(background=True)
            print("✓ Wireshark started successfully\n")
        except Exception as e:
            print(f"⚠️  Could not start Wireshark: {e}")
            print("Continuing without Wireshark GUI...\n")
    
    print("Starting capture... (Press Ctrl+C to stop)\n")
    
    # Load model
    try:
        model = SecIDSModel(args.model)
        print("✓ Model loaded successfully\n")
    except Exception as e:
        print(f"ERROR: Failed to load model: {e}")
        if wireshark_mgr:
            wireshark_mgr.stop()
        sys.exit(1)
    
    # Initialize countermeasure system if enabled
    countermeasure = None
    if args.enable_countermeasure:
        try:
            countermeasure = DDoSCountermeasure(
                block_threshold=args.block_threshold,
                time_window=int(args.window),
                auto_block=args.auto_block
            )
            print("✓ Countermeasure system initialized\n")
        except Exception as e:
            print(f"WARNING: Failed to initialize countermeasures: {e}")
            print("Continuing without countermeasures\n")
    
    # Initialize whitelist checker if enabled
    whitelist_checker = None
    if args.enable_whitelist:
        try:
            whitelist_checker = WhitelistChecker()
            stats = whitelist_checker.get_statistics()
            print("✓ Whitelist checker initialized")
            print(f"  - Local IPs: {stats['local_ips']}")
            print(f"  - Trusted orgs: {stats['trusted_organizations']}")
            print(f"  - Trusted IP ranges: {stats['trusted_ip_ranges']}\n")
        except Exception as e:
            print(f"WARNING: Failed to initialize whitelist: {e}")
            print("Continuing without whitelist filtering\n")
    
    # Initialize blacklist manager if enabled
    blacklist_manager = None
    if args.enable_blacklist:
        try:
            blacklist_manager = BlacklistManager()
            stats = blacklist_manager.get_statistics()
            print("✓ Blacklist manager initialized")
            print(f"  - Blocked IPs: {stats['blocked_ips']}")
            print(f"  - Total threats: {stats['total_threats']}")
            print(f"  - Attack patterns: {stats['attack_patterns']}\n")
        except Exception as e:
            print(f"WARNING: Failed to initialize blacklist: {e}")
            print("Continuing without blacklist tracking\n")
    
    # Start packet capture
    capturer = LivePacketCapture(args.iface, args.window, args.interval)
    try:
        capturer.start_capture()
    except PermissionError:
        print(f"ERROR: Need elevated permissions to capture on {args.iface}")
        print("Try running with sudo")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to start capture: {e}")
        sys.exit(1)
    
    # Wait for capture to initialize
    time.sleep(1)
    
    # Main monitoring loop
    window_count = 0
    total_flows = 0
    total_threats = 0
    last_threat_time = None
    
    try:
        while True:
            time.sleep(args.interval)
            
            # Get packets from current window
            packet_tuples = capturer.get_window_packets()
            
            if not packet_tuples:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No packets captured in window")
                continue
            
            window_count += 1
            
            # Convert to DataFrame and assess
            df = packets_to_dataframe(packet_tuples)
            
            if df.empty:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(packet_tuples)} packets, 0 flows extracted")
                continue
            
            results = assess_traffic(df, model)
            
            # Print summary
            total_flows += len(results)
            attack_count = (results['prediction'] == 'ATTACK').sum()
            total_threats += attack_count
            
            status_icon = "⚠️ " if attack_count > 0 else "✓"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Window #{window_count}: {len(results)} flows | "
                  f"Threats: {attack_count} | Total: {total_flows} flows, {total_threats} threats detected")
            
            # Show threat details and send to countermeasure system
            if attack_count > 0:
                threat_rows = results[results['prediction'] == 'ATTACK']
                
                # Apply whitelist filtering if enabled
                if whitelist_checker:
                    filtered_threats = []
                    whitelisted_count = 0
                    
                    for idx, row in threat_rows.iterrows():
                        whitelist_result = whitelist_checker.check_flow(
                            dst_port=int(row['Destination Port']),
                            probability=float(row['probability'])
                        )
                        
                        if not whitelist_result['whitelisted']:
                            filtered_threats.append(row)
                        else:
                            whitelisted_count += 1
                    
                    if whitelisted_count > 0:
                        print(f"\n  ✓ Filtered {whitelisted_count} false positive(s) via whitelist")
                    
                    if not filtered_threats:
                        print(f"  ✓ All {attack_count} threats were false positives (whitelisted)\n")
                        continue
                    
                    threat_rows = filtered_threats
                    attack_count = len(filtered_threats)
                
                print(f"\n  ⚠️  THREAT ALERT - {attack_count} confirmed malicious flow(s)!")
                for row in (threat_rows if isinstance(threat_rows, list) else threat_rows.itertuples()):
                    if isinstance(row, tuple):
                        port = row._asdict()['Destination Port']
                        packets = row._asdict()['Total Fwd Packets']
                        bytes_val = row._asdict()['Total Length of Fwd Packets']
                        prob = row._asdict()['probability']
                    else:
                        port = row['Destination Port']
                        packets = row['Total Fwd Packets']
                        bytes_val = row['Total Length of Fwd Packets']
                        prob = row['probability']
                    
                    print(f"     Port: {port:5d} | "
                          f"Packets: {packets:3.0f} | "
                          f"Bytes: {bytes_val:7.0f} | "
                          f"Threat Level: {prob*100:5.1f}%")
                    
                    # Build threat data
                    threat_data = {
                        'src_ip': 'unknown',
                        'dst_ip': 'local',
                        'dst_port': int(port),
                        'protocol': 'TCP/UDP',
                        'probability': float(prob),
                        'flow_packets': int(packets),
                        'flow_bytes': int(bytes_val)
                    }
                    
                    # Add to blacklist if enabled
                    if blacklist_manager:
                        threat_id = blacklist_manager.add_threat(threat_data)
                        print(f"       → Blacklisted: {threat_id}")
                    
                    # Send to countermeasure system
                    if countermeasure:
                        countermeasure.process_threat(threat_data)
                print()
                last_threat_time = datetime.now()
    
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("CAPTURE STOPPED BY USER")
        print("="*80)
        capturer.stop_capture()
        
        # Stop Wireshark
        if wireshark_mgr:
            wireshark_mgr.stop()
        
        # Stop countermeasure system and show stats
        if countermeasure:
            print("\nStopping countermeasure system...")
            countermeasure.stop()
            print()
            countermeasure.print_statistics()
        
        # Show blacklist statistics
        if blacklist_manager:
            print("\nBlacklist Statistics:")
            stats = blacklist_manager.get_statistics()
            print(f"  Blocked IPs: {stats['blocked_ips']}")
            print(f"  Total threats tracked: {stats['total_threats']}")
            print(f"  Attack patterns recorded: {stats['attack_patterns']}")
            print(f"  Severity breakdown: {stats['severity_breakdown']}")
        
        # Print final statistics
        print(f"\nCapture Statistics:")
        print(f"Total monitoring windows: {window_count}")
        print(f"Total flows analyzed: {total_flows}")
        print(f"Total threats detected: {total_threats}")
        if last_threat_time:
            print(f"Last threat detected: {last_threat_time.strftime('%H:%M:%S')}")
        print("="*80)


if __name__ == '__main__':
    main()

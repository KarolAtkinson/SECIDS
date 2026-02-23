#!/usr/bin/env python3
"""
Enhanced dataset creator with legitimacy detection features
Adds parameters to identify known cloud providers and private networks
"""
import pandas as pd
from scapy.all import PcapReader, IP, TCP, UDP
import numpy as np
from collections import defaultdict
import ipaddress

# Known legitimate cloud provider IP ranges (simplified)
KNOWN_PROVIDERS = {
    'github': ['140.82.112.0/20', '192.30.252.0/22', '185.199.108.0/22'],
    'microsoft': ['13.64.0.0/11', '20.0.0.0/8', '40.64.0.0/10', '52.96.0.0/12'],
    'aws': ['3.0.0.0/8', '52.0.0.0/8', '54.0.0.0/8'],
    'google': ['8.8.8.0/24', '34.64.0.0/10', '35.184.0.0/13'],
}

LEGITIMATE_PORTS = {
    80: 'HTTP',
    443: 'HTTPS',
    53: 'DNS',
    22: 'SSH',
    21: 'FTP',
    25: 'SMTP',
    110: 'POP3',
    143: 'IMAP',
    3306: 'MySQL',
    5432: 'PostgreSQL',
}

def is_private_ip(ip_str):
    """Check if IP is in private range (RFC 1918)"""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private
    except Exception:
        return False

def is_known_provider(ip_str):
    """Check if IP belongs to known cloud provider"""
    try:
        ip = ipaddress.ip_address(ip_str)
        for provider, ranges in KNOWN_PROVIDERS.items():
            for cidr in ranges:
                if ip in ipaddress.ip_network(cidr):
                    return provider
    except Exception as e:
            pass  # Skip on error
    return None

def is_legitimate_port(port):
    """Check if port is commonly used legitimate service"""
    return 1 if port in LEGITIMATE_PORTS else 0

def analyze_flow_bidirectionality(flows_dict):
    """Check if flows have bidirectional communication (sign of legitimate traffic)"""
    bidirectional_flows = {}
    
    for flow_key, flow_data in flows_dict.items():
        src_ip, dst_ip, src_port, dst_port, proto = flow_key
        # Check for reverse flow
        reverse_key = (dst_ip, src_ip, dst_port, src_port, proto)
        
        if reverse_key in flows_dict:
            bidirectional_flows[flow_key] = True
        else:
            bidirectional_flows[flow_key] = False
    
    return bidirectional_flows

def extract_enhanced_features(pcap_path):
    """Extract flows with enhanced legitimacy features"""
    flows = {}
    packet_times = {}
    
    print(f"Processing: {pcap_path}")
    reader = PcapReader(str(pcap_path))
    
    for pkt in reader:
        if not pkt.haslayer(IP):
            continue
        
        ip_layer = pkt[IP]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        pkt_len = len(pkt)
        timestamp = float(pkt.time)
        
        proto = None
        sport = None
        dport = None
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
        
        flow_key = (src_ip, dst_ip, sport, dport, proto)
        
        if flow_key not in flows:
            flows[flow_key] = {
                'first_ts': timestamp,
                'last_ts': timestamp,
                'fwd_pkts': [],
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'src_port': sport,
                'dst_port': dport,
                'protocol': proto,
            }
            packet_times[flow_key] = []
        
        flow = flows[flow_key]
        flow['last_ts'] = max(flow['last_ts'], timestamp)
        flow['fwd_pkts'].append((timestamp, pkt_len, flags))
        packet_times[flow_key].append(timestamp)
    
    reader.close()
    
    # Analyze bidirectionality
    bidirectional = analyze_flow_bidirectionality(flows)
    
    # Build dataset
    rows = []
    for flow_key, flow in flows.items():
        src_ip = flow['src_ip']
        dst_ip = flow['dst_ip']
        dst_port = flow['dst_port']
        
        # Original features
        first_ts = flow['first_ts']
        last_ts = flow['last_ts']
        duration_s = max(1e-6, last_ts - first_ts)
        duration_us = int((last_ts - first_ts) * 1e6) if last_ts > first_ts else 0
        
        fwd_pkts = flow['fwd_pkts']
        total_fwd_packets = len(fwd_pkts)
        total_length_fwd = sum(p[1] for p in fwd_pkts)
        
        flow_bytes_per_s = total_length_fwd / duration_s if duration_s > 0 else 0
        flow_pkts_per_s = total_fwd_packets / duration_s if duration_s > 0 else 0
        
        avg_pkt_size = (total_length_fwd / total_fwd_packets) if total_fwd_packets > 0 else 0
        pkt_lengths = [p[1] for p in fwd_pkts] if fwd_pkts else [0]
        pkt_len_std = float(np.std(pkt_lengths)) if len(pkt_lengths) > 1 else 0.0
        
        fin_count = 0
        ack_count = 0
        for (_, _, pkt_flags) in fwd_pkts:
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
        # NEW ENHANCED FEATURES
        src_is_private = 1 if is_private_ip(src_ip) else 0
        dst_is_private = 1 if is_private_ip(dst_ip) else 0
        src_provider = is_known_provider(src_ip)
        dst_provider = is_known_provider(dst_ip)
        src_is_known_provider = 1 if src_provider else 0
        dst_is_known_provider = 1 if dst_provider else 0
        is_bidirectional = 1 if bidirectional.get(flow_key, False) else 0
        dst_port_is_legitimate = is_legitimate_port(dst_port)
        
        # Calculate inter-packet arrival time variance (NEW)
        if len(packet_times[flow_key]) > 1:
            iats = np.diff(packet_times[flow_key])
            iat_mean = float(np.mean(iats))
            iat_std = float(np.std(iats))
        else:
            iat_mean = 0.0
            iat_std = 0.0
        
        # Connection legitimacy score (NEW COMPOSITE FEATURE)
        legitimacy_score = (
            dst_is_known_provider * 0.3 +
            dst_port_is_legitimate * 0.3 +
            is_bidirectional * 0.2 +
            (1 - src_is_private) * 0.1 +  # External sources slightly more legitimate for servers
            (dst_port == 443) * 0.1  # HTTPS bonus
        )
        
        row = {
            # Original 10 features
            'Destination Port': int(dst_port),
            'Flow Duration': int(duration_us),
            'Total Fwd Packets': int(total_fwd_packets),
            'Total Length of Fwd Packets': int(total_length_fwd),
            'Flow Bytes/s': float(flow_bytes_per_s),
            'Flow Packets/s': float(flow_pkts_per_s),
            'Average Packet Size': float(avg_pkt_size),
            'Packet Length Std': float(pkt_len_std),
            'FIN Flag Count': int(fin_count),
            'ACK Flag Count': int(ack_count),
            
            # NEW ENHANCED FEATURES (8 new features)
            'Source Is Private': src_is_private,
            'Destination Is Private': dst_is_private,
            'Source Is Known Provider': src_is_known_provider,
            'Destination Is Known Provider': dst_is_known_provider,
            'Is Bidirectional Flow': is_bidirectional,
            'Destination Port Is Legitimate': dst_port_is_legitimate,
            'IAT Mean': iat_mean,
            'IAT Std': iat_std,
            'Legitimacy Score': legitimacy_score,
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    print(f"✓ Extracted {len(df)} flows with {len(df.columns)} features")
    return df

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python create_enhanced_dataset.py <input.pcap> <output.csv>")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    output_file = sys.argv[2]
    
    df = extract_enhanced_features(pcap_file)
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Enhanced dataset saved to: {output_file}")
    print(f"  Total flows: {len(df)}")
    print(f"  Total features: {len(df.columns)}")
    print(f"\nNew features added:")
    print("  - Source Is Private")
    print("  - Destination Is Private")
    print("  - Source Is Known Provider")
    print("  - Destination Is Known Provider")
    print("  - Is Bidirectional Flow")
    print("  - Destination Port Is Legitimate")
    print("  - IAT Mean (Inter-arrival time)")
    print("  - IAT Std (Inter-arrival time variance)")
    print("  - Legitimacy Score (composite)")

if __name__ == '__main__':
    main()

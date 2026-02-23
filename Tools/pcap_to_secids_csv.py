#!/usr/bin/env python3
"""
Scapy-based pcap -> SecIDS CSV converter.

This script reads packets from a pcap using Scapy and aggregates them
into bidirectional flows based on 5-tuple (src,dst,sport,dport,proto).
It computes a small set of features compatible with the project's
`ddos_training_dataset.csv` so the `SecIDSModel` can consume live
captures without external Java tools.

Output columns:
  Destination Port,Flow Duration,Total Fwd Packets,Total Length of Fwd Packets,
  Flow Bytes/s,Flow Packets/s,Average Packet Size,Packet Length Std,FIN Flag Count,ACK Flag Count

Usage:
  python3 tools/pcap_to_secids_csv.py -i capture.pcap -o live_test.csv

Dependencies:
  pip install scapy pandas numpy tqdm
"""

import argparse
import sys
from pathlib import Path
import math

import pandas as pd
import numpy as np

try:
    from scapy.all import PcapReader, TCP, UDP, Raw, IP
except Exception as e:
    print("scapy is required: pip install scapy")
    raise

try:
    from tqdm import tqdm
    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False


def process_pcap(pcap_path: Path):
    # flow_key: (src, dst, sport, dport, proto)
    flows = {}

    def make_key(pkt):
        ip = pkt.getlayer(IP)
        proto = None
        sport = None
        dport = None
        if pkt.haslayer(TCP):
            proto = 'TCP'
            sport = pkt[TCP].sport
            dport = pkt[TCP].dport
        elif pkt.haslayer(UDP):
            proto = 'UDP'
            sport = pkt[UDP].sport
            dport = pkt[UDP].dport
        else:
            return None
        return (ip.src, ip.dst, int(sport), int(dport), proto)

    print(f"Reading packets from {pcap_path}...")
    reader = PcapReader(str(pcap_path))
    count = 0
    
    # Wrap reader with progress bar if available
    if PROGRESS_AVAILABLE:
        pbar = tqdm(desc="Processing packets", unit=" pkts", colour="blue")
    
    for pkt in reader:
        count += 1
        if PROGRESS_AVAILABLE:
            pbar.update(1)
            pbar.set_postfix(flows=len(flows))
        
        if not pkt.haslayer(IP):
            continue
        key = make_key(pkt)
        if key is None:
            continue

        ts = float(pkt.time)
        length = len(pkt)

        # Determine whether packet is forward or backward relative to first packet in flow
        if key not in flows:
            flows[key] = {
                'first_ts': ts,
                'last_ts': ts,
                'fwd_pkts': [],
                'bwd_pkts': [],
                'dst_port': key[3],
            }
            # mark first direction as forward
            flows[key]['fwd_id'] = (key[0], key[2])  # (src_ip, src_port)

        f = flows[key]
        f['last_ts'] = max(f['last_ts'], ts)

        # classify forward vs backward: if pkt src matches fwd_id
        pkt_src = pkt[IP].src
        pkt_sport = None
        if pkt.haslayer(TCP):
            pkt_sport = pkt[TCP].sport
            flags = pkt[TCP].flags
        elif pkt.haslayer(UDP):
            pkt_sport = pkt[UDP].sport
            flags = None
        else:
            pkt_sport = None
            flags = None

        if (pkt_src, pkt_sport) == f['fwd_id']:
            f['fwd_pkts'].append((ts, length, flags))
        else:
            f['bwd_pkts'].append((ts, length, flags))

    reader.close()
    if PROGRESS_AVAILABLE:
        pbar.close()
    
    print(f"✓ Processed {count} packets into {len(flows)} flows")
    
    # Now compute features per flow
    print("Computing flow features...")
    rows = []
    flow_items = list(flows.items())
    
    if PROGRESS_AVAILABLE:
        flow_items = tqdm(flow_items, desc="Computing features", unit=" flows", colour="green")
    
    for key, f in flow_items:
        dst_port = f.get('dst_port', 0)
        first = f['first_ts']
        last = f['last_ts']
        duration_s = max(1e-6, last - first)
        duration_us = int((last - first) * 1e6) if last > first else 0

        fwd_pkts = f['fwd_pkts']
        total_fwd_packets = len(fwd_pkts)
        total_length_fwd = sum(p[1] for p in fwd_pkts)

        flow_bytes_per_s = total_length_fwd / duration_s if duration_s > 0 else 0
        flow_pkts_per_s = total_fwd_packets / duration_s if duration_s > 0 else 0

        avg_pkt_size = (total_length_fwd / total_fwd_packets) if total_fwd_packets > 0 else 0
        pkt_lengths = [p[1] for p in fwd_pkts]
        pkt_len_std = float(np.std(pkt_lengths)) if pkt_lengths else 0.0

        fin_count = 0
        ack_count = 0
        for (_, _, flags) in fwd_pkts:
            if flags is None:
                continue
            # flags may be integer or scapy Flags object
            try:
                s = str(flags)
            except Exception:
                s = ''
            if 'F' in s:
                fin_count += 1
            if 'A' in s:
                ack_count += 1

        # Extract source IP from key (src_ip, dst_ip, sport, dport, proto)
        src_ip = key[0]
        
        rows.append({
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
            'ip_source': str(src_ip),
        })

    df = pd.DataFrame(rows)
    # if empty, create empty frame with desired columns
    desired = [
        'Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Length of Fwd Packets',
        'Flow Bytes/s', 'Flow Packets/s', 'Average Packet Size', 'Packet Length Std',
        'FIN Flag Count', 'ACK Flag Count', 'ip_source'
    ]
    for c in desired:
        if c not in df.columns:
            df[c] = 0

    return df[desired]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input pcap file')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file (SecIDS format)')
    args = parser.parse_args()

    pcap = Path(args.input)
    out = Path(args.output)

    if not pcap.exists():
        print('PCAP not found:', pcap)
        sys.exit(2)

    df = process_pcap(pcap)
    df.to_csv(out, index=False)
    print('Wrote SecIDS-formatted CSV to', out)


if __name__ == '__main__':
    main()

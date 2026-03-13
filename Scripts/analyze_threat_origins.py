#!/usr/bin/env python3
"""
Analyze threat origins from pcap file
Correlates detected threats with source IPs and performs geolocation
"""
import pandas as pd
import socket
from collections import defaultdict
from pathlib import Path
from scapy.all import PcapReader, IP, TCP, UDP  # type: ignore

def get_ip_info(ip_address):
    """Get hostname and attempt basic IP classification"""
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
    except (socket.herror, socket.gaierror, OSError):
        # Reverse DNS lookup failed
        hostname = "Unknown"
    
    # Basic IP classification
    octets = ip_address.split('.')
    first_octet = int(octets[0])
    
    if first_octet == 10:
        location = "Private Network (RFC 1918)"
    elif first_octet == 172 and 16 <= int(octets[1]) <= 31:
        location = "Private Network (RFC 1918)"
    elif first_octet == 192 and int(octets[1]) == 168:
        location = "Private Network (RFC 1918)"
    elif first_octet == 127:
        location = "Localhost"
    elif first_octet == 169 and int(octets[1]) == 254:
        location = "Link-Local"
    else:
        location = "Public Internet"
    
    return hostname, location

def extract_flows_with_ips(pcap_path):
    """Extract flow data with source/destination IPs"""
    flows = {}
    
    print(f"Reading pcap: {pcap_path}")
    reader = PcapReader(str(pcap_path))
    
    for pkt in reader:
        if not pkt.haslayer(IP):
            continue
        
        ip_layer = pkt[IP]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        proto = None
        sport = None
        dport = None
        
        if pkt.haslayer(TCP):
            proto = 'TCP'
            tcp_layer = pkt[TCP]
            sport = tcp_layer.sport
            dport = tcp_layer.dport
        elif pkt.haslayer(UDP):
            proto = 'UDP'
            udp_layer = pkt[UDP]
            sport = udp_layer.sport
            dport = udp_layer.dport
        else:
            continue
        
        # Create flow key (matching the CSV generation logic)
        flow_key = (src_ip, dst_ip, sport, dport, proto)
        
        if flow_key not in flows:
            flows[flow_key] = {
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'src_port': sport,
                'dst_port': dport,
                'protocol': proto,
                'packet_count': 0
            }
        
        flows[flow_key]['packet_count'] += 1
    
    reader.close()
    return flows

def main():
    pcap_file = "captures/capture_test2.pcap"
    csv_file = "SecIDS-CNN/datasets/Test2.csv"
    # Find latest results file
    results_dir = Path("Results")
    if results_dir.exists():
        result_files = sorted(results_dir.glob("detection_results_*.csv"), reverse=True)
        if result_files:
            results_file = str(result_files[0])
        else:
            results_file = "Results/detection_results_latest.csv"
    else:
        results_file = "Results/detection_results_latest.csv"
    
    # Load the threat detection results
    print("Loading threat detection results...")
    results_df = pd.read_csv(results_file)
    
    # Extract flows with IP information
    flows = extract_flows_with_ips(pcap_file)
    
    # Create mapping: destination port -> flow info
    port_to_flows = defaultdict(list)
    for flow_key, flow_info in flows.items():
        port_to_flows[flow_info['dst_port']].append(flow_info)
    
    # Filter for threats only
    threats = results_df[results_df['prediction'] == 'Attack'].copy()
    
    print(f"\n{'='*80}")
    print(f"THREAT ORIGIN ANALYSIS")
    print(f"{'='*80}")
    print(f"Total threats detected: {len(threats)}\n")
    
    threat_sources = []
    
    for idx, threat in threats.iterrows():
        dst_port = int(threat['Destination Port'])
        
        # Find matching flows
        matching_flows = port_to_flows.get(dst_port, [])
        
        if matching_flows:
            for flow in matching_flows:
                hostname, location = get_ip_info(flow['src_ip'])
                
                threat_info = {
                    'Source IP': flow['src_ip'],
                    'Destination IP': flow['dst_ip'],
                    'Source Port': flow['src_port'],
                    'Destination Port': dst_port,
                    'Protocol': flow['protocol'],
                    'Hostname': hostname,
                    'Location Type': location,
                    'Packets': flow['packet_count'],
                    'Threat Probability': threat.get('probability', 'N/A')
                }
                threat_sources.append(threat_info)
                
                print(f"Threat Connection #{len(threat_sources)}:")
                print(f"  Source:      {flow['src_ip']}:{flow['src_port']} ({location})")
                print(f"  Destination: {flow['dst_ip']}:{dst_port}")
                print(f"  Protocol:    {flow['protocol']}")
                print(f"  Hostname:    {hostname}")
                print(f"  Packets:     {flow['packet_count']}")
                print()
    
    # Create summary
    print(f"{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")
    
    if threat_sources:
        threat_df = pd.DataFrame(threat_sources)
        
        # Count unique source IPs
        unique_sources = threat_df['Source IP'].nunique()
        print(f"Unique threat source IPs: {unique_sources}")
        
        # Group by location type
        location_counts = threat_df['Location Type'].value_counts()
        print(f"\nThreats by Origin:")
        for location, count in location_counts.items():
            print(f"  {location}: {count}")
        
        # Save to CSV
        output_file = "threat_origins_analysis.csv"
        threat_df.to_csv(output_file, index=False)
        print(f"\n✓ Full analysis saved to: {output_file}")
        
        # List unique threat IPs
        print(f"\n{'='*80}")
        print(f"UNIQUE THREAT SOURCE IPs")
        print(f"{'='*80}")
        for ip in threat_df['Source IP'].unique():
            hostname, location = get_ip_info(ip)
            count = len(threat_df[threat_df['Source IP'] == ip])
            print(f"  {ip:15s} - {location:30s} ({count} threat connections)")
    else:
        print("No matching flows found for detected threats")

if __name__ == '__main__':
    main()

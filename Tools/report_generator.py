#!/usr/bin/env python3
"""
Threat Detection Report Generator
Creates comprehensive reports after threat detection scans
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import sys


class ThreatReportGenerator:
    """Generate comprehensive threat detection reports"""
    
    def __init__(self, results_csv):
        """
        Initialize report generator
        
        Args:
            results_csv: Path to detection results CSV file
        """
        self.results_csv = Path(results_csv)
        self.df = None
        self.report_data = {}
        
    def load_results(self):
        """Load detection results from CSV"""
        if not self.results_csv.exists():
            raise FileNotFoundError(f"Results file not found: {self.results_csv}")
        
        self.df = pd.read_csv(self.results_csv)
        print(f"✓ Loaded {len(self.df)} detection results from {self.results_csv.name}")
        
    def analyze_results(self):
        """Analyze detection results and generate statistics"""
        if self.df is None:
            raise ValueError("No results loaded. Call load_results() first.")
        
        total_records = int(len(self.df))
        
        # Count predictions
        if 'prediction' in self.df.columns:
            attack_count = int((self.df['prediction'] == 'Attack').sum())
            benign_count = int((self.df['prediction'] == 'Benign').sum())
        else:
            attack_count = 0
            benign_count = total_records
        
        # Calculate percentages
        attack_pct = (attack_count / total_records * 100) if total_records > 0 else 0
        benign_pct = (benign_count / total_records * 100) if total_records > 0 else 0
        
        # Get probability statistics if available
        prob_stats = {}
        if 'probability' in self.df.columns:
            prob_stats = {
                'mean': float(self.df['probability'].mean()),
                'median': float(self.df['probability'].median()),
                'std': float(self.df['probability'].std()),
                'min': float(self.df['probability'].min()),
                'max': float(self.df['probability'].max()),
            }
        
        # Analyze attack details
        attack_details = []
        if attack_count > 0 and 'prediction' in self.df.columns:
            attack_df = self.df[self.df['prediction'] == 'Attack']
            
            # Get top threats by probability
            if 'probability' in attack_df.columns:
                top_threats = attack_df.nlargest(10, 'probability')
                for idx, row in top_threats.iterrows():
                    threat = {
                        'index': int(idx),
                        'probability': float(row.get('probability', 0)),
                    }
                    # Add key features
                    for col in ['Destination Port', 'Total Fwd Packets', 'Flow Bytes/s', 
                               'Flow Packets/s', 'src_ip', 'dst_ip']:
                        if col in row:
                            threat[col] = str(row[col])
                    attack_details.append(threat)
        
        # Port analysis
        port_analysis = {}
        if 'Destination Port' in self.df.columns and attack_count > 0:
            attack_df = self.df[self.df['prediction'] == 'Attack']
            port_counts = attack_df['Destination Port'].value_counts().head(10)
            port_analysis = {int(port): int(count) for port, count in port_counts.items()}
        
        self.report_data = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'results_file': str(self.results_csv.name),
                'total_records': total_records,
            },
            'summary': {
                'total_analyzed': total_records,
                'threats_detected': attack_count,
                'benign_traffic': benign_count,
                'threat_percentage': round(attack_pct, 2),
                'benign_percentage': round(benign_pct, 2),
            },
            'probability_statistics': prob_stats,
            'top_threats': attack_details,
            'port_analysis': port_analysis,
        }
        
    def generate_markdown_report(self, output_path=None):
        """Generate a markdown report"""
        if not self.report_data:
            raise ValueError("No analysis data. Call analyze_results() first.")
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.results_csv.parent / f"threat_report_{timestamp}.md"
        else:
            output_path = Path(output_path)
        
        scan_info = self.report_data['scan_info']
        summary = self.report_data['summary']
        prob_stats = self.report_data['probability_statistics']
        top_threats = self.report_data['top_threats']
        port_analysis = self.report_data['port_analysis']
        
        report = []
        report.append("# Threat Detection Report")
        report.append("")
        report.append(f"**Generated**: {scan_info['timestamp']}")
        report.append(f"**Results File**: {scan_info['results_file']}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        report.append(f"- **Total Records Analyzed**: {summary['total_analyzed']:,}")
        report.append(f"- **Threats Detected**: {summary['threats_detected']:,} ({summary['threat_percentage']}%)")
        report.append(f"- **Benign Traffic**: {summary['benign_traffic']:,} ({summary['benign_percentage']}%)")
        report.append("")
        
        # Threat Level
        threat_pct = summary['threat_percentage']
        if threat_pct > 50:
            threat_level = "🔴 CRITICAL"
        elif threat_pct > 20:
            threat_level = "🟠 HIGH"
        elif threat_pct > 5:
            threat_level = "🟡 MEDIUM"
        elif threat_pct > 0:
            threat_level = "🟢 LOW"
        else:
            threat_level = "✅ CLEAN"
        
        report.append(f"**Threat Level**: {threat_level}")
        report.append("")
        
        # Probability Statistics
        if prob_stats:
            report.append("## Probability Statistics")
            report.append("")
            report.append("| Metric | Value |")
            report.append("|--------|-------|")
            report.append(f"| Mean | {prob_stats['mean']:.4f} |")
            report.append(f"| Median | {prob_stats['median']:.4f} |")
            report.append(f"| Std Dev | {prob_stats['std']:.4f} |")
            report.append(f"| Min | {prob_stats['min']:.4f} |")
            report.append(f"| Max | {prob_stats['max']:.4f} |")
            report.append("")
        
        # Top Threats
        if top_threats:
            report.append("## Top 10 Threats")
            report.append("")
            report.append("| Rank | Index | Probability | Details |")
            report.append("|------|-------|-------------|---------|")
            for rank, threat in enumerate(top_threats, 1):
                prob = threat['probability']
                details = []
                if 'Destination Port' in threat:
                    details.append(f"Port: {threat['Destination Port']}")
                if 'Total Fwd Packets' in threat:
                    details.append(f"Packets: {threat['Total Fwd Packets']}")
                if 'src_ip' in threat:
                    details.append(f"From: {threat['src_ip']}")
                
                detail_str = ", ".join(details) if details else "N/A"
                report.append(f"| {rank} | {threat['index']} | {prob:.2%} | {detail_str} |")
            report.append("")
        
        # Port Analysis
        if port_analysis:
            report.append("## Targeted Ports")
            report.append("")
            report.append("Most frequently targeted destination ports:")
            report.append("")
            report.append("| Port | Attack Count |")
            report.append("|------|--------------|")
            for port, count in sorted(port_analysis.items(), key=lambda x: x[1], reverse=True):
                report.append(f"| {port} | {count} |")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        if summary['threats_detected'] > 0:
            report.append("### Immediate Actions")
            report.append("")
            report.append("1. **Review Top Threats**: Investigate high-probability detections")
            report.append("2. **Block Malicious IPs**: Add confirmed threat sources to blacklist")
            report.append("3. **Monitor Targeted Ports**: Increase monitoring on frequently attacked ports")
            report.append("4. **Update Firewall Rules**: Block or rate-limit suspicious traffic")
            report.append("")
            report.append("### Long-term Actions")
            report.append("")
            report.append("1. Review and update security policies")
            report.append("2. Conduct security awareness training")
            report.append("3. Regular security audits and penetration testing")
            report.append("4. Keep all systems and software updated")
        else:
            report.append("✅ No threats detected in this scan.")
            report.append("")
            report.append("**Continue to**:")
            report.append("- Maintain regular security monitoring")
            report.append("- Keep systems updated")
            report.append("- Review security logs periodically")
        report.append("")
        
        # Footer
        report.append("---")
        report.append(f"*Report generated by SecIDS-CNN Threat Detection System*")
        report.append("")
        
        # Write report
        output_path.write_text("\n".join(report))
        print(f"✓ Markdown report saved to: {output_path}")
        return output_path
    
    def generate_json_report(self, output_path=None):
        """Generate a JSON report"""
        if not self.report_data:
            raise ValueError("No analysis data. Call analyze_results() first.")
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.results_csv.parent / f"threat_report_{timestamp}.json"
        else:
            output_path = Path(output_path)
        
        with open(output_path, 'w') as f:
            json.dump(self.report_data, f, indent=2)
        
        print(f"✓ JSON report saved to: {output_path}")
        return output_path
    
    def print_summary(self):
        """Print a quick summary to console"""
        if not self.report_data:
            raise ValueError("No analysis data. Call analyze_results() first.")
        
        summary = self.report_data['summary']
        
        print("\n" + "="*80)
        print("THREAT DETECTION SUMMARY")
        print("="*80)
        print(f"Total Analyzed:     {summary['total_analyzed']:,}")
        print(f"Threats Detected:   {summary['threats_detected']:,} ({summary['threat_percentage']}%)")
        print(f"Benign Traffic:     {summary['benign_traffic']:,} ({summary['benign_percentage']}%)")
        
        # Threat level indicator
        threat_pct = summary['threat_percentage']
        if threat_pct > 50:
            print("\n🔴 THREAT LEVEL: CRITICAL")
        elif threat_pct > 20:
            print("\n🟠 THREAT LEVEL: HIGH")
        elif threat_pct > 5:
            print("\n🟡 THREAT LEVEL: MEDIUM")
        elif threat_pct > 0:
            print("\n🟢 THREAT LEVEL: LOW")
        else:
            print("\n✅ THREAT LEVEL: CLEAN")
        
        print("="*80 + "\n")


def main():
    """Command-line interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 report_generator.py <results_csv> [output_dir]")
        print("\nExample:")
        print("  python3 report_generator.py Results/detection_results.csv")
        print("  python3 report_generator.py Results/detection_results.csv Results/")
        sys.exit(1)
    
    results_csv = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Create report generator
        generator = ThreatReportGenerator(results_csv)
        
        # Load and analyze results
        print("Loading detection results...")
        generator.load_results()
        
        print("Analyzing results...")
        generator.analyze_results()
        
        # Print summary
        generator.print_summary()
        
        # Generate reports
        print("Generating reports...")
        
        if output_dir:
            output_dir = Path(output_dir)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            md_path = output_dir / f"threat_report_{timestamp}.md"
            json_path = output_dir / f"threat_report_{timestamp}.json"
        else:
            md_path = None
            json_path = None
        
        generator.generate_markdown_report(md_path)
        generator.generate_json_report(json_path)
        
        print("\n✅ Report generation complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

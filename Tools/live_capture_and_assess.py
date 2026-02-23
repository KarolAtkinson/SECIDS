#!/usr/bin/env python3
"""Live capture -> CICFlowMeter -> SecIDS model assessment

Usage example:
  # capture 10-second windows on eth0 and assess each window
  python3 tools/live_capture_and_assess.py --iface eth0 --window 10

Requirements:
  - dumpcap or tshark (dumpcap recommended for raw capture): `dumpcap -i <iface> -a duration:<s> -w file.pcap`
  - Java + CICFlowMeter available (script uses tools/pcap_to_secids_csv.py which calls cicflowmeter)
  - Run inside the project's venv so Python deps are available
  - Wireshark auto-management for live capture visualization

This script captures short pcap windows, converts them to the SecIDS CSV
format using `pcap_to_secids_csv.py`, and then runs the loaded model to
produce per-flow attack probabilities. Probabilities > 0.5 are labeled
as `Attack`.
"""

import argparse
import subprocess
import time
from pathlib import Path
import sys
import os
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / 'tools'

# Import Wireshark manager
try:
    sys.path.insert(0, str(TOOLS_DIR))
    from wireshark_manager import WiresharkManager
    WIRESHARK_AVAILABLE = True
except ImportError:
    WIRESHARK_AVAILABLE = False
    print("⚠️  Wireshark manager not available")


def capture_window(iface: str, out_pcap: Path, window_seconds: int) -> bool:
    # prefer dumpcap for efficient capture
    dumpcap_cmd = ['dumpcap', '-i', iface, '-a', f'duration:{window_seconds}', '-w', str(out_pcap)]
    tshark_cmd = ['tshark', '-i', iface, '-a', f'duration:{window_seconds}', '-w', str(out_pcap)]
    for cmd in (dumpcap_cmd, tshark_cmd):
        try:
            print('Running capture:', ' '.join(cmd))
            subprocess.check_call(cmd)
            return True
        except FileNotFoundError:
            continue
        except subprocess.CalledProcessError as e:
            print('Capture failed:', e)
            return False
    print('Neither dumpcap nor tshark found in PATH. Install Wireshark/tshark or use another capture method.')
    return False


def convert_pcap_to_secids(pcap_path: Path, out_csv: Path) -> bool:
    # Call the conversion helper we added earlier
    script = TOOLS_DIR / 'pcap_to_secids_csv.py'
    if not script.exists():
        print('Conversion script not found:', script)
        return False
    cmd = [sys.executable, str(script), '-i', str(pcap_path), '-o', str(out_csv)]
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print('Conversion failed:', e)
        return False


def assess_csv(csv_path: Path, model_path: str = None):
    # Lazy import to avoid heavy deps unless this routine runs
    import pandas as pd
    # Ensure we can import the local secids module. repo layout has
    # the model code under PROJECT_ROOT/SecIDS-CNN, so prefer that.
    secids_dir = PROJECT_ROOT / 'SecIDS-CNN'
    if secids_dir.exists():
        secids_path = str(secids_dir)
        if secids_path not in sys.path:
            sys.path.insert(0, secids_path)
    else:
        # fall back to PROJECT_ROOT itself
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

    from secids_cnn import SecIDSModel
    # load model
    if model_path is None:
        model = SecIDSModel()
    else:
        model = SecIDSModel(model_path)

    df = pd.read_csv(csv_path)
    # Use predict_proba if available
    try:
        probs = model.predict_proba(df)
    except Exception:
        # fallback: use predict
        labels = model.predict(df)
        probs = None

    # Build result DataFrame
    out = df.copy()
    if probs is None:
        out['prediction'] = labels
        out['probability'] = None
    else:
        import numpy as _np
        if getattr(probs, 'ndim', 1) == 1:
            out['probability'] = probs
        elif getattr(probs, 'ndim', 2) == 2 and probs.shape[1] == 2:
            out['probability'] = probs[:, 1]
        elif getattr(probs, 'ndim', 2) == 2 and probs.shape[1] == 1:
            out['probability'] = probs.flatten()
        else:
            # fallback: use argmax
            out['probability'] = (probs.argmax(axis=1) == 1).astype(float)

        out['prediction'] = out['probability'].apply(lambda p: 'Attack' if float(p) > 0.5 else 'Benign')

    # Print a brief summary
    total = len(out)
    attacks = (out['prediction'] == 'Attack').sum()
    print(f'Total flows: {total}  Attacks detected: {attacks}')

    # Save results next to CSV
    res_path = csv_path.with_name(csv_path.stem + '_results.csv')
    out.to_csv(res_path, index=False)
    print('Saved results to', res_path)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--iface', default='eth0', help='Capture interface (e.g., eth0, any)')
    p.add_argument('--window', type=int, default=120, help='Capture window (seconds)')
    p.add_argument('--outdir', default=str(PROJECT_ROOT / 'captures'), help='Directory for temporary pcaps/csvs')
    p.add_argument('--once', action='store_true', help='Capture only one window then exit')
    p.add_argument('--keep-pcap', action='store_true', help='Do not delete pcap after processing')
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # Where to keep live CSV datasets (the project's training dataset folder)
    datasets_dir = PROJECT_ROOT / 'SecIDS-CNN' / 'datasets'
    if not datasets_dir.exists():
        datasets_dir.mkdir(parents=True, exist_ok=True)

    def _next_live_csv_path(base_name: str = 'Live-Capture-Test') -> Path:
        i = 1
        while True:
            candidate = datasets_dir / f"{base_name}{i}.csv"
            if not candidate.exists():
                return candidate
            i += 1

    # Start Wireshark with auto-management
    wireshark_mgr = None
    if WIRESHARK_AVAILABLE:
        try:
            print("🦈 Starting Wireshark for live capture...")
            use_any = args.iface.lower() == 'any'
            wireshark_mgr = WiresharkManager(interface=args.iface, use_any=use_any)
            wireshark_mgr.start(background=True)
            print("✓ Wireshark started successfully\n")
        except Exception as e:
            print(f"⚠️  Could not start Wireshark: {e}")
            print("Continuing without Wireshark GUI...\n")

    print('Starting live capture assessor. Interface:', args.iface, 'window:', args.window)
    try:
        while True:
            ts = int(time.time())
            pcap = outdir / f'capture_{ts}.pcap'
            csv = outdir / f'capture_{ts}.csv'

            ok = capture_window(args.iface, pcap, args.window)
            if not ok:
                print('Capture failed, sleeping then retrying...')
                time.sleep(2)
                if args.once:
                    break
                continue

            ok2 = convert_pcap_to_secids(pcap, csv)
            if not ok2:
                print('Conversion failed for', pcap)
            else:
                # Move the generated CSV into the SecIDS dataset folder and rename
                try:
                    dest = _next_live_csv_path('Live-Capture-Test')
                    shutil.move(str(csv), str(dest))
                    print('Moved CSV to dataset folder as', dest)
                except Exception as e:
                    print('Failed to move CSV to datasets folder:', e)
                    dest = csv

                assess_csv(dest)

            if not args.keep_pcap:
                try:
                    pcap.unlink()
                except Exception as e:
                    pass  # Skip on error
            if args.once:
                break

            # small pause to avoid tight loop
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('\nStopped by user')
    finally:
        # Stop Wireshark
        if wireshark_mgr:
            wireshark_mgr.stop()


if __name__ == '__main__':
    main()

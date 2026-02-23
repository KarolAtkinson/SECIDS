"""
SecIDS-CNN: Security Intrusion Detection System using Convolutional Neural Networks
A comprehensive intrusion detection system with deep learning capabilities.
"""

__version__ = "2.0.0"
__author__ = "SecIDS-CNN Development Team"
__license__ = "MIT"

# Package-level imports for easy access
from pathlib import Path
import sys

# Add project directories to path
PROJECT_ROOT = Path(__file__).parent
SECIDS_CNN_DIR = PROJECT_ROOT / 'SecIDS-CNN'
TOOLS_DIR = PROJECT_ROOT / 'Tools'
COUNTERMEASURES_DIR = PROJECT_ROOT / 'Countermeasures'
UI_DIR = PROJECT_ROOT / 'UI'
MODEL_TESTER_DIR = PROJECT_ROOT / 'Model_Tester'

for directory in [SECIDS_CNN_DIR, TOOLS_DIR, COUNTERMEASURES_DIR, UI_DIR, MODEL_TESTER_DIR]:
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

__all__ = [
    '__version__',
    'PROJECT_ROOT',
    'SECIDS_CNN_DIR',
    'TOOLS_DIR',
    'COUNTERMEASURES_DIR',
    'UI_DIR',
    'MODEL_TESTER_DIR',
]

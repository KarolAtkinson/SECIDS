#!/usr/bin/env python3
"""
SecIDS-CNN System Integrator
Links all components and provides unified access
"""

import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
SECIDS_DIR = PROJECT_ROOT / 'SecIDS-CNN'
TOOLS_DIR = PROJECT_ROOT / 'Tools'
COUNTERMEASURES_DIR = PROJECT_ROOT / 'Countermeasures'
UI_DIR = PROJECT_ROOT / 'UI'
AUTO_UPDATE_DIR = PROJECT_ROOT / 'Auto_Update'
MODEL_TESTER_DIR = PROJECT_ROOT / 'Model_Tester' / 'Code'

# Add all paths
for path in [SECIDS_DIR, TOOLS_DIR, COUNTERMEASURES_DIR, UI_DIR, AUTO_UPDATE_DIR, MODEL_TESTER_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


class SystemIntegrator:
    """Central integration point for all system components"""
    
    def __init__(self):
        """Initialize system integrator"""
        self.model = None
        self.countermeasure = None
        self.scheduler = None
        self.ui = None
        
    def load_detection_model(self, model_path=None):
        """Load the SecIDS-CNN detection model"""
        try:
            from secids_cnn import SecIDSModel
            
            if model_path is None:
                model_path = PROJECT_ROOT / 'Models' / 'SecIDS-CNN.h5'
            
            self.model = SecIDSModel(str(model_path))
            print(f"✓ Detection model loaded from {model_path}")
            return self.model
        except Exception as e:
            print(f"✗ Failed to load detection model: {e}")
            return None
    
    def initialize_countermeasures(self, auto_block=True, threshold=5):
        """Initialize the countermeasure system"""
        try:
            from ddos_countermeasure import DDoSCountermeasure
            
            self.countermeasure = DDoSCountermeasure(
                block_threshold=threshold,
                auto_block=auto_block
            )
            self.countermeasure.start()
            print(f"✓ Countermeasure system initialized (threshold: {threshold})")
            return self.countermeasure
        except Exception as e:
            print(f"✗ Failed to initialize countermeasures: {e}")
            return None
    
    def start_scheduler(self):
        """Start the auto-update scheduler"""
        try:
            from task_scheduler import TaskScheduler
            
            self.scheduler = TaskScheduler()
            print("✓ Task scheduler initialized")
            return self.scheduler
        except Exception as e:
            print(f"✗ Failed to start scheduler: {e}")
            return None
    
    def launch_ui(self):
        """Launch the terminal UI"""
        try:
            import os
            ui_script = UI_DIR / 'terminal_ui_enhanced.py'
            os.execv(sys.executable, [sys.executable, str(ui_script)])
        except Exception as e:
            print(f"✗ Failed to launch UI: {e}")
            return None
    
    def run_system_check(self):
        """Run comprehensive system check"""
        try:
            from system_checker import SystemChecker
            
            print("\n" + "="*70)
            print("  SecIDS-CNN System Diagnostics")
            print("="*70 + "\n")
            
            checker = SystemChecker(verbose=True)
            all_passed = checker.check_all()
            
            print("\n" + "="*70)
            if all_passed:
                print("  ✅ All system checks passed!")
            else:
                print("  ⚠️  Some checks failed - review output above")
            print("="*70 + "\n")
            
            return all_passed
        except Exception as e:
            print(f"✗ Failed to run system check: {e}")
            return False
    
    def get_progress_utils(self):
        """Get progress bar utilities"""
        try:
            import progress_utils
            return progress_utils
        except Exception as e:
            print(f"✗ Failed to load progress utilities: {e}")
            return None
    
    def get_report_generator(self):
        """Get threat report generator"""
        try:
            from report_generator import ThreatReportGenerator
            return ThreatReportGenerator
        except Exception as e:
            print(f"✗ Failed to load report generator: {e}")
            return None
    
    def get_wireshark_manager(self):
        """Get Wireshark manager"""
        try:
            from wireshark_manager import WiresharkManager
            return WiresharkManager
        except Exception as e:
            print(f"✗ Failed to load Wireshark manager: {e}")
            return None
    
    def initialize_all(self):
        """Initialize all system components"""
        print("\n" + "="*70)
        print("  SecIDS-CNN System Initialization")
        print("="*70 + "\n")
        
        # Load model
        self.load_detection_model()
        
        # Initialize countermeasures
        self.initialize_countermeasures()
        
        # Start scheduler
        self.start_scheduler()
        
        print("\n" + "="*70)
        print("  ✓ System initialization complete")
        print("="*70 + "\n")
        
        return self
    
    def get_status(self):
        """Get system status"""
        status = {
            'model_loaded': self.model is not None,
            'countermeasure_active': self.countermeasure is not None,
            'scheduler_running': self.scheduler is not None,
        }
        return status


# Global integrator instance
_integrator = None


def get_integrator():
    """Get or create the global integrator instance"""
    global _integrator
    if _integrator is None:
        _integrator = SystemIntegrator()
    return _integrator


if __name__ == '__main__':
    # Quick test
    integrator = SystemIntegrator()
    integrator.run_system_check()

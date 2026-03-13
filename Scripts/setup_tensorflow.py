#!/usr/bin/env python3
"""
TensorFlow Setup & Configuration for SecIDS-CNN
================================================
Ensures TensorFlow is properly installed and configured.

This script:
1. Checks TensorFlow installation
2. Verifies GPU availability (if applicable)
3. Sets optimal environment variables
4. Tests TensorFlow functionality
5. Provides recommendations

Usage:
    python3 Scripts/setup_tensorflow.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Suppress TensorFlow warnings during import
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

PROJECT_ROOT = Path(__file__).parent.parent


class TensorFlowSetup:
    """Setup and verify TensorFlow installation"""
    
    def __init__(self):
        self.venv_path = PROJECT_ROOT / '.venv_test'
        self.in_venv = self.check_venv()
        
    def check_venv(self):
        """Check if running in virtual environment"""
        return (hasattr(sys, 'real_prefix') or 
                (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
    
    def print_header(self):
        """Print header"""
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║     TensorFlow Setup & Configuration                    ║")
        print("║     SecIDS-CNN Neural Network System                    ║")
        print("╚══════════════════════════════════════════════════════════╝\n")
    
    def check_installation(self):
        """Check if TensorFlow is installed"""
        print("🔍 Checking TensorFlow Installation...")
        print("=" * 60)
        
        try:
            import tensorflow as tf
            print(f"✅ TensorFlow {tf.__version__} is installed")
            
            # Check build info
            print(f"   Python version: {sys.version.split()[0]}")
            print(f"   Install location: {tf.__file__}")
            
            return True, tf
        except ImportError:
            print("❌ TensorFlow is not installed")
            return False, None
    
    def check_gpu(self, tf):
        """Check GPU availability"""
        print("\n🎮 Checking GPU Availability...")
        print("=" * 60)
        
        try:
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                print(f"✅ Found {len(gpus)} GPU(s):")
                for i, gpu in enumerate(gpus):
                    print(f"   GPU {i}: {gpu.name}")
                
                # Check if GPU is being used
                print("\n   Testing GPU computation...")
                with tf.device('/GPU:0'):
                    a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
                    b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
                    c = tf.matmul(a, b)
                print("   ✅ GPU computation successful!")
                return True
            else:
                print("ℹ️  No GPU detected - using CPU")
                print("   This is normal for systems without NVIDIA GPUs")
                return False
        except Exception as e:
            print(f"ℹ️  GPU check skipped: {e}")
            return False
    
    def test_functionality(self, tf):
        """Test basic TensorFlow functionality"""
        print("\n🧪 Testing TensorFlow Functionality...")
        print("=" * 60)
        
        try:
            # Test basic operations
            print("   Testing basic operations...")
            a = tf.constant([1, 2, 3])
            b = tf.constant([4, 5, 6])
            c = tf.add(a, b)
            print(f"   ✅ Tensor operations: {c.numpy()}")
            
            # Test model creation
            print("\n   Testing model creation...")
            keras = tf.keras
            model = keras.Sequential([
                keras.Input(shape=(5,)),
                keras.layers.Dense(10, activation='relu'),
                keras.layers.Dense(1, activation='sigmoid')
            ])
            print("   ✅ Model creation successful")
            
            # Test compilation
            print("\n   Testing model compilation...")
            model.compile(optimizer='adam', loss='binary_crossentropy')
            print("   ✅ Model compilation successful")
            
            return True
        except Exception as e:
            print(f"   ❌ Functionality test failed: {e}")
            return False
    
    def setup_environment(self):
        """Setup optimal TensorFlow environment variables"""
        print("\n⚙️  Setting Up TensorFlow Environment...")
        print("=" * 60)
        
        # Recommended environment variables
        env_vars = {
            'TF_CPP_MIN_LOG_LEVEL': '2',  # Suppress info/warning messages
            'TF_ENABLE_ONEDNN_OPTS': '1',  # Enable oneDNN optimizations
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            print(f"   ✅ Set {key}={value}")
        
        # Create .env file in Config folder for persistence
        config_dir = PROJECT_ROOT / 'Config'
        config_dir.mkdir(exist_ok=True)
        env_file = config_dir / '.env'
        
        with open(env_file, 'w') as f:
            f.write("# TensorFlow Environment Configuration\n")
            f.write("# Auto-generated by setup_tensorflow.py\n\n")
            for key, value in env_vars.items():
                f.write(f"export {key}={value}\n")
        
        print(f"\n   ✅ Saved configuration to {env_file}")
        print("   Configuration will be sourced automatically by launchers")
    
    def install_tensorflow(self):
        """Install TensorFlow in virtual environment"""
        print("\n📦 Installing TensorFlow...")
        print("=" * 60)
        
        if not self.in_venv:
            print("⚠️  Not in virtual environment!")
            print("\nPlease activate the virtual environment first:")
            print("   source .venv_test/bin/activate")
            print("   python3 Scripts/setup_tensorflow.py")
            return False
        
        try:
            # Install from requirements.txt
            requirements = PROJECT_ROOT / 'SecIDS-CNN' / 'requirements.txt'
            if requirements.exists():
                print(f"   Installing from {requirements}...")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', str(requirements)
                ], check=True)
                print("\n   ✅ TensorFlow installed successfully!")
                return True
            else:
                print(f"   ❌ Requirements file not found: {requirements}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Installation failed: {e}")
            return False
    
    def verify_model_files(self):
        """Verify model files exist"""
        print("\n🧠 Checking Model Files...")
        print("=" * 60)
        
        model_locations = [
            PROJECT_ROOT / 'Models' / 'SecIDS-CNN.h5',
            PROJECT_ROOT / 'SecIDS-CNN' / 'SecIDS-CNN.h5'
        ]
        
        found = False
        for model_path in model_locations:
            if model_path.exists():
                size_mb = model_path.stat().st_size / (1024 * 1024)
                print(f"   ✅ {model_path.relative_to(PROJECT_ROOT)} ({size_mb:.1f} MB)")
                found = True
            else:
                print(f"   ℹ️  {model_path.relative_to(PROJECT_ROOT)} (not found)")
        
        if not found:
            print("\n   ⚠️  No model files found - you'll need to train a model first")
            print("   Run: sudo SECIDS → 4 → 1 (Train SecIDS-CNN Model)")
        
        return found
    
    def provide_recommendations(self, has_gpu, tf_working):
        """Provide recommendations based on system"""
        print("\n💡 Recommendations")
        print("=" * 60)
        
        if not self.in_venv:
            print("   1. Always activate virtual environment before using SecIDS:")
            print("      source .venv_test/bin/activate")
            print()
        
        if has_gpu:
            print("   1. GPU detected - models will train faster")
            print("   2. For GPU optimization, ensure CUDA is properly configured")
        else:
            print("   1. Running on CPU - this is normal for most systems")
            print("   2. CPU performance is sufficient for SecIDS-CNN")
        
        if tf_working:
            print("   3. TensorFlow is properly configured")
            print("   4. You can now run live detection: sudo SECIDS")
        
        print("\n   5. To suppress TensorFlow warnings:")
        print("      Warnings are configured in Config/.env")
        print("      All launchers source this file automatically")
    
    def run(self):
        """Run complete TensorFlow setup"""
        self.print_header()
        
        # Check virtual environment
        if self.in_venv:
            print(f"✅ Running in virtual environment: {sys.prefix}\n")
        else:
            print(f"ℹ️  Running in system Python: {sys.executable}")
            if self.venv_path.exists():
                print(f"   Virtual environment available: {self.venv_path}\n")
        
        # Check installation
        installed, tf = self.check_installation()
        
        if not installed:
            # Try to install
            if self.install_tensorflow():
                installed, tf = self.check_installation()
        
        if not installed:
            print("\n❌ TensorFlow setup failed")
            print("\nManual installation:")
            print("   source .venv_test/bin/activate")
            print("   pip install -r SecIDS-CNN/requirements.txt")
            return False
        
        # Check GPU
        has_gpu = self.check_gpu(tf)
        
        # Test functionality
        tf_working = self.test_functionality(tf)
        
        # Setup environment
        self.setup_environment()
        
        # Verify models
        self.verify_model_files()
        
        # Provide recommendations
        self.provide_recommendations(has_gpu, tf_working)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SETUP SUMMARY")
        print("=" * 60)
        
        if tf_working:
            print("✅ TensorFlow is properly installed and configured")
            print("✅ SecIDS-CNN is ready to use")
            print("\nLaunch the UI: sudo SECIDS")
        else:
            print("⚠️  TensorFlow has some issues - see recommendations above")
        
        print("=" * 60 + "\n")
        return tf_working


def main():
    """Main entry point"""
    setup = TensorFlowSetup()
    success = setup.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

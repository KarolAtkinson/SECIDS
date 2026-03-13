#!/usr/bin/env python3
import sys

print("Verifying required packages...")
print("="*60)

packages = {
    'pandas': 'pd',
    'numpy': 'np',
    'sklearn': 'sklearn',
    'tensorflow': 'tf',
}

all_installed = True

for package_name, import_name in packages.items():
    try:
        if package_name == 'sklearn':
            __import__('sklearn')
            import sklearn
            print(f"✓ {package_name:20} {sklearn.__version__}")
        elif package_name == 'tensorflow':
            import tensorflow
            print(f"✓ {package_name:20} {tensorflow.__version__}")
        else:
            module = __import__(package_name)
            print(f"✓ {package_name:20} {module.__version__}")
    except Exception as e:
        print(f"✗ {package_name:20} NOT INSTALLED")
        all_installed = False

# Check specific imports
print("\n" + "="*60)
print("Checking specific imports...")
print("="*60)

# Use direct imports instead of exec() for security
try:
    from sklearn.model_selection import train_test_split
    print("✓ from sklearn.model_selection import train_test_split")
except Exception as e:
    print("✗ from sklearn.model_selection import train_test_split")
    print(f"  Error: {e}")
    all_installed = False

try:
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    print("✓ from sklearn.preprocessing import StandardScaler, LabelEncoder")
except Exception as e:
    print("✗ from sklearn.preprocessing import StandardScaler, LabelEncoder")
    print(f"  Error: {e}")
    all_installed = False

try:
    import tensorflow as tf
    _ = tf.keras
    print("✓ tensorflow.keras available")
except Exception as e:
    print("✗ tensorflow.keras available")
    print(f"  Error: {e}")
    all_installed = False

try:
    import tensorflow as tf
    _ = tf.keras.layers
    print("✓ tensorflow.keras.layers available")
except Exception as e:
    print("✗ tensorflow.keras.layers available")
    print(f"  Error: {e}")
    all_installed = False

print("\n" + "="*60)
if all_installed:
    print("✓ ALL PACKAGES INSTALLED AND READY!")
else:
    print("✗ Some packages are missing")
    sys.exit(1)

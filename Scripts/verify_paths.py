#!/usr/bin/env python3
"""
Path Verification Script for SecIDS-CNN
========================================
Verifies all paths in the project are correctly set up after UI addition.

Usage:
    python3 Scripts/verify_paths.py
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def verify_folder_structure() -> Tuple[List[str], List[str]]:
    """Verify expected folders exist"""
    expected_folders = [
        "UI",
        "Tools",
        "Scripts", 
        "Launchers",
        "SecIDS-CNN",
        "Models",
        "Captures",
        "Config",
        "Logs",
        "Reports",
        "Device_Profile",
        "Countermeasures",
        "Auto_Update",
        "TrashDump",
        "Model_Tester",
        "Stress_Test_Results"
    ]
    
    passed = []
    failed = []
    
    print("🔍 Verifying Folder Structure...")
    print("=" * 60)
    
    for folder in expected_folders:
        folder_path = PROJECT_ROOT / folder
        if folder_path.exists():
            passed.append(f"✅ {folder}/")
        else:
            failed.append(f"❌ {folder}/ (missing)")
    
    for item in passed:
        print(item)
    for item in failed:
        print(item)
    
    print()
    return passed, failed


def verify_ui_files() -> Tuple[List[str], List[str]]:
    """Verify UI files exist"""
    ui_files = [
        "UI/terminal_ui_enhanced.py",
        "UI/ui_config.json",
        "UI/README.md",
        "Launchers/secids-ui",
        "WebUI/app.py",
        "WebUI/menu_actions.py",
        "WebUI/templates/index.html",
        "WebUI/static/app.js",
        "WebUI/static/style.css"
    ]
    
    passed = []
    failed = []
    
    print("🎨 Verifying UI Files...")
    print("=" * 60)
    
    for file in ui_files:
        file_path = PROJECT_ROOT / file
        if file_path.exists():
            is_exec = os.access(file_path, os.X_OK)
            exec_mark = "🔧" if is_exec else "📄"
            passed.append(f"✅ {exec_mark} {file}")
        else:
            failed.append(f"❌ {file} (missing)")
    
    for item in passed:
        print(item)
    for item in failed:
        print(item)
    
    print()
    return passed, failed


def verify_launchers() -> Tuple[List[str], List[str]]:
    """Verify launcher scripts exist and are executable"""
    launchers = [
        "Launchers/secids.sh",
        "Launchers/secids-ui",
        "Launchers/QUICK_START.sh"
    ]
    
    passed = []
    failed = []
    
    print("🚀 Verifying Launcher Scripts...")
    print("=" * 60)
    
    for launcher in launchers:
        launcher_path = PROJECT_ROOT / launcher
        if launcher_path.exists():
            if os.access(launcher_path, os.X_OK):
                passed.append(f"✅ {launcher} (executable)")
            else:
                failed.append(f"⚠️  {launcher} (not executable)")
        else:
            failed.append(f"❌ {launcher} (missing)")
    
    for item in passed:
        print(item)
    for item in failed:
        print(item)
    
    print()
    return passed, failed


def verify_key_scripts() -> Tuple[List[str], List[str]]:
    """Verify key scripts exist"""
    scripts = [
        "Tools/command_library.py",
        "Tools/pcap_to_secids_csv.py",
        "Tools/live_capture_and_assess.py",
        "Tools/csv_workflow_manager.py",
        "Tools/threat_reviewer.py",
        "Scripts/stress_test.py",
        "Scripts/analyze_threat_origins.py",
        "Scripts/verify_packages.py",
        "SecIDS-CNN/run_model.py",
        "SecIDS-CNN/secids_cnn.py",
        "SecIDS-CNN/unified_wrapper.py",
        "Countermeasures/ddos_countermeasure.py"
    ]
    
    passed = []
    failed = []
    
    print("📜 Verifying Key Scripts...")
    print("=" * 60)
    
    for script in scripts:
        script_path = PROJECT_ROOT / script
        if script_path.exists():
            passed.append(f"✅ {script}")
        else:
            failed.append(f"❌ {script} (missing)")
    
    for item in passed:
        print(item)
    for item in failed:
        print(item)
    
    print()
    return passed, failed


def verify_config_files() -> Tuple[List[str], List[str]]:
    """Verify configuration files"""
    configs = [
        "Config/command_shortcuts.json",
        "Config/command_history.json",
        "UI/ui_config.json",
        "requirements.txt",
        "Master-Manual.md"
    ]
    
    passed = []
    failed = []
    
    print("⚙️  Verifying Configuration Files...")
    print("=" * 60)
    
    for config in configs:
        config_path = PROJECT_ROOT / config
        if config_path.exists():
            passed.append(f"✅ {config}")
        else:
            failed.append(f"⚠️  {config} (will be created on first use)" if "json" in config else f"❌ {config} (missing)")
    
    for item in passed:
        print(item)
    for item in failed:
        print(item)
    
    print()
    return passed, failed


def verify_model_files() -> Tuple[List[str], List[str]]:
    """Verify model files exist"""
    models = [
        "Models/SecIDS-CNN.h5",
        "SecIDS-CNN/SecIDS-CNN.h5"
    ]
    
    passed = []
    failed = []
    
    print("🧠 Verifying Model Files...")
    print("=" * 60)
    
    for model in models:
        model_path = PROJECT_ROOT / model
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            passed.append(f"✅ {model} ({size_mb:.1f} MB)")
        else:
            failed.append(f"⚠️  {model} (not found - will be created during training)")
    
    for item in passed:
        print(item)
    for item in failed:
        print(item)
    
    print()
    return passed, failed


def check_python_imports():
    """Check if critical Python imports work"""
    print("🐍 Checking Python Dependencies...")
    print("=" * 60)
    
    # Check if we're in a virtual environment
    import sys
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    venv_path = sys.prefix if in_venv else None
    
    if not in_venv:
        # Try to check in the project's virtual environment
        venv_test = PROJECT_ROOT / '.venv_test'
        if venv_test.exists():
            print(f"ℹ️  Note: Checking system Python. Virtual environment available at: {venv_test}")
            print(f"   Activate with: source .venv_test/bin/activate\n")
    
    imports_to_check = [
        ("rich", "Rich library for terminal UI"),
        ("scapy.all", "Scapy for packet processing"),
        ("pandas", "Pandas for data manipulation"),
        ("numpy", "NumPy for numerical operations"),
        ("tensorflow", "TensorFlow for ML models")
    ]
    
    passed = []
    failed = []
    
    for module, description in imports_to_check:
        try:
            # Suppress TensorFlow warnings during import
            import os
            old_env = os.environ.get('TF_CPP_MIN_LOG_LEVEL')
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            
            __import__(module.split('.')[0])
            
            # Restore environment
            if old_env is None:
                os.environ.pop('TF_CPP_MIN_LOG_LEVEL', None)
            else:
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = old_env
            
            passed.append(f"✅ {description}")
        except ImportError:
            failed.append(f"⚠️  {description} (not in current environment)")
    
    for item in passed:
        print(item)
    for item in failed:
        print(item)
    
    print()
    return passed, failed


def check_ui_integration():
    """Check UI integrates with existing tools"""
    print("🔗 Checking UI Integration Points...")
    print("=" * 60)
    
    ui_script = PROJECT_ROOT / "UI" / "terminal_ui_enhanced.py"
    webui_script = PROJECT_ROOT / "WebUI" / "app.py"
    
    if not ui_script.exists():
        print("❌ Enhanced terminal UI script not found")
        return [], ["Terminal UI not found"]
    if not webui_script.exists():
        print("❌ Web UI backend script not found")
        return [], ["Web UI not found"]
    
    # Read UI script and check for integration points
    with open(ui_script, 'r') as f:
        content = f.read()
    with open(webui_script, 'r') as f:
        web_content = f.read()
    
    integration_points = [
        ("command_library", "Command library integration"),
        ("command_library.py", "Command library integration"),
        ("run_model.py", "Model execution integration"),
        ("stress_test.py", "Testing integration"),
        ("analyze_threat_origins.py", "Analysis integration"),
        ("ui_config.json", "Configuration persistence")
    ]

    web_integration_points = [
        ("/api/menu", "Web API menu exposure"),
        ("/api/run", "Web command execution endpoint"),
        ("/api/settings", "Web settings persistence endpoint"),
        ("/api/history", "Web history endpoint"),
    ]
    
    passed = []
    failed = []
    
    for component, description in integration_points:
        if component in content:
            passed.append(f"✅ {description}")
        else:
            failed.append(f"❌ {description} (not found in UI)")

    for component, description in web_integration_points:
        if component in web_content:
            passed.append(f"✅ {description}")
        else:
            failed.append(f"❌ {description} (not found in Web UI)")
    
    for item in passed:
        print(item)
    for item in failed:
        print(item)
    
    print()
    return passed, failed


def generate_summary(all_results):
    """Generate summary report"""
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    for category, (passed, failed) in all_results.items():
        total_passed += len(passed)
        total_failed += len(failed)
        
        status = "✅ PASS" if len(failed) == 0 else "⚠️  WARNINGS" if len(passed) > len(failed) else "❌ FAIL"
        print(f"{status} {category}: {len(passed)} passed, {len(failed)} failed/warnings")
    
    print("\n" + "=" * 60)
    total = total_passed + total_failed
    success_rate = (total_passed / total * 100) if total > 0 else 0
    
    print(f"Overall: {total_passed}/{total} checks passed ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("\n✅ System paths are correctly configured!")
        if total_failed > 0:
            print("   Note: Some dependencies may require virtual environment activation:")
            print("   source .venv_test/bin/activate")
        print("\nYou can now launch the UI with: bash Launchers/secids-ui")
    elif success_rate >= 70:
        print("\n⚠️  System is mostly configured but has some warnings.")
        print("Review the warnings above. Most features should work.")
    else:
        print("\n❌ System has significant configuration issues.")
        print("Please review the failed checks above.")
    
    print("=" * 60)


def main():
    """Main verification function"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     SecIDS-CNN Path Verification Tool                   ║")
    print("║     Checking all paths after UI integration             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print()
    
    # Run all verification checks
    results = {
        "Folder Structure": verify_folder_structure(),
        "UI Files": verify_ui_files(),
        "Launcher Scripts": verify_launchers(),
        "Key Scripts": verify_key_scripts(),
        "Configuration Files": verify_config_files(),
        "Model Files": verify_model_files(),
        "Python Dependencies": check_python_imports(),
        "UI Integration": check_ui_integration()
    }
    
    # Generate summary
    generate_summary(results)


if __name__ == "__main__":
    main()

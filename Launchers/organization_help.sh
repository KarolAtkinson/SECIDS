#!/bin/bash
# Quick Reference: File Organization Commands
# SecIDS-CNN Project
# Updated: 2026-01-31

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          File Organization - Quick Reference               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

echo "📂 AVAILABLE COMMANDS"
echo "===================="
echo

echo "1️⃣  Full Project Cleanup (Recommended)"
echo "   bash Launchers/project_cleanup.sh"
echo "   • Runs complete 9-step organization"
echo "   • Consolidates log directories"
echo "   • Archives CSV files"
echo "   • Organizes all file types"
echo

echo "2️⃣  Python Organization Script (Detailed)"
echo "   python3 Scripts/organize_files.py"
echo "   • Shows detailed statistics"
echo "   • Reports by category"
echo "   • Better for troubleshooting"
echo

echo "3️⃣  Quick Cleanup Shortcut"
echo "   ./cleanup"
echo "   • Fastest method"
echo "   • Runs from root directory"
echo

echo "📊 DIRECTORY STRUCTURE"
echo "======================"
echo "✅ Reports/              - Documentation & reports"
echo "✅ Scripts/              - Utility scripts (11 files)"
echo "✅ Tools/                - Main tools (24 files)"
echo "✅ Launchers/            - Shell script launchers"
echo "✅ Models/               - ML model files (.h5, .pkl)"
echo "✅ Logs/                 - Consolidated logs (2 files)"
echo "✅ Config/               - Configuration files (3 files)"
echo "✅ Stress_Test_Results/  - Performance test reports"
echo "✅ Results/              - Detection results (23 files)"
echo "✅ Archives/             - CSV datasets (31 files)"
echo "✅ Captures/             - Network packet captures"
echo "✅ SecIDS-CNN/datasets/  - Active datasets"
echo "✅ Device_Profile/       - Device info & whitelists"
echo "✅ UI/                   - Terminal UI"
echo

echo "🔄 FILE ORGANIZATION RULES"
echo "==========================="
echo "• Root directory: Only Master-Manual.md"
echo "• .md reports → Reports/"
echo "• .log files → Logs/"
echo "• .json configs → Config/"
echo "• .pcap files → Captures/"
echo "• .h5/.pkl models → Models/"
echo "• .csv datasets → Archives/"
echo "• Detection results → Results/"
echo "• Stress tests → Stress_Test_Results/"
echo

echo "⚙️  WHAT EACH SCRIPT DOES"
echo "=========================="
echo "organize_files.py:"
echo "  ✓ 11 organization methods"
echo "  ✓ Statistics tracking"
echo "  ✓ Detailed reporting"
echo "  ✓ Error handling with skip list"
echo

echo "project_cleanup.sh:"
echo "  ✓ 9-step process"
echo "  ✓ Directory verification"
echo "  ✓ Log consolidation"
echo "  ✓ CSV archival"
echo "  ✓ Redundancy removal"
echo

echo "💡 TIPS"
echo "======="
echo "• Run cleanup before git commits"
echo "• Execute after detection sessions"
echo "• Safe to run multiple times"
echo "• No data loss - only organizes"
echo

echo "📝 LAST UPDATE: 2026-01-31"
echo "✅ Status: All systems operational"
echo

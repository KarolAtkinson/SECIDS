#!/usr/bin/env python3
"""
SecIDS-CNN Enhanced Terminal UI
Two-panel interface with detailed information and two-stage engagement
Features: Header/Main/Footer layout, screen scaling, interactive selection
"""

# Check TensorFlow availability at startup
import sys
try:
    import tensorflow as tf
except ImportError:
    print("\n⚠️  TensorFlow not found!")
    print("\nThis program requires TensorFlow. Please run:")
    print("  cd /home/kali/Documents/Code/SECIDS-CNN")
    print("  ./Launchers/secids-ui")
    print("\nOr manually activate the virtual environment:")
    print("  source .venv_test/bin/activate")
    print("\nThen run this script again.\n")
    sys.exit(1)

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Tools"))

# Import command library
try:
    from command_library import CommandLibrary
    COMMAND_LIBRARY_AVAILABLE = True
except ImportError:
    COMMAND_LIBRARY_AVAILABLE = False
    print("⚠️  Command library not available")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.layout import Layout
    from rich.live import Live
    from rich import box
    from rich.columns import Columns
    from rich.text import Text
except ImportError:
    print("Error: rich library not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.layout import Layout
    from rich import box
    from rich.columns import Columns
    from rich.text import Text


class EnhancedSecIDSUI:
    """Enhanced Interactive terminal UI with two-panel layout"""
    
    VERSION = "2.0.0"
    
    def __init__(self):
        self.console = Console()
        self.project_root = PROJECT_ROOT
        self.config_file = self.project_root / "UI" / "ui_config.json"
        self.config = self.load_config()
        self.running = True
        self.selected_option = None
        self.current_menu = "main"
        
        # Initialize command library
        if COMMAND_LIBRARY_AVAILABLE:
            self.command_lib = CommandLibrary()
        else:
            self.command_lib = None
        
        # Get terminal size for responsive design
        self.update_screen_size()
        
    def update_screen_size(self):
        """Update screen size for responsive scaling"""
        size = shutil.get_terminal_size()
        self.screen_width = size.columns
        self.screen_height = size.lines
        
        # Calculate panel widths (40% menu, 60% details)
        self.menu_width = int(self.screen_width * 0.4)
        self.details_width = int(self.screen_width * 0.6) - 4
        
    def load_config(self) -> Dict:
        """Load saved configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                pass  # Skip on error
        return {
            "last_interface": "eth0",
            "last_duration": 60,
            "last_window": 5,
            "last_interval": 2,
            "theme": "default",
            "history": []
        }
    
    def save_config(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, indent=2, fp=f)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not save config: {e}[/yellow]")
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def create_header(self) -> Panel:
        """Create header with title and version"""
        header_text = Text()
        header_text.append("SecIDS-CNN Interactive Terminal\n", style="bold cyan")
        header_text.append("Network Threat Detection System\n", style="cyan")
        header_text.append(f"Version {self.VERSION} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim cyan")
        
        return Panel(
            header_text,
            title="[bold white]╔═══ SECIDS-CNN ═══╗[/bold white]",
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
    
    def create_footer(self, stage: str = "select") -> Panel:
        """Create footer with keystroke options"""
        keystrokes = [
            ("1-9/0", "Select Action"),
            ("ENTER", "Execute Selected"),
            ("Q", "Quit"),
            ("H", "Help")
        ]
        
        footer_text = Text()
        for i, (key, action) in enumerate(keystrokes):
            if i > 0:
                footer_text.append(" │ ", style="dim white")
            footer_text.append(f"{key}", style="bold yellow")
            footer_text.append(f": {action}", style="white")
        
        return Panel(
            footer_text,
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2)
        )
    
    def get_menu_options(self, menu_type: str) -> List[Dict]:
        """Get menu options with details for specified menu"""
        
        main_menu_options = [
            {
                "key": "1",
                "title": "🔍 Live Detection & Monitoring",
                "description": "Real-time network threat detection and monitoring",
                "details": [
                    "• Live traffic analysis with CNN model",
                    "• Real-time threat classification",
                    "• Automatic countermeasure deployment",
                    "• Network interface monitoring"
                ],
                "sub_options": [
                    "Live Detection (Single Pass)",
                    "Continuous Detection",
                    "Quick Scan",
                    "Deep Scan",
                    "Stop Detection"
                ]
            },
            {
                "key": "2",
                "title": "📡 Network Capture Operations",
                "description": "Capture and analyze network traffic",
                "details": [
                    "• PCAP file capture from network interface",
                    "• Automated capture scheduling",
                    "• Traffic filtering and analysis",
                    "• Integration with detection system"
                ],
                "sub_options": [
                    "Start Capture",
                    "Stop Capture",
                    "List Captures",
                    "Pipeline Capture (Capture + Analyze)",
                    "Manage Capture Schedule"
                ]
            },
            {
                "key": "3",
                "title": "📊 File-Based Analysis",
                "description": "Analyze existing CSV/PCAP files for threats",
                "details": [
                    "• Batch analysis of multiple files",
                    "• PCAP to CSV conversion",
                    "• Dataset feature enhancement",
                    "• Historical data analysis"
                ],
                "sub_options": [
                    "Analyze CSV File",
                    "Analyze PCAP File",
                    "Batch Analysis",
                    "PCAP to CSV Conversion",
                    "Enhance Dataset Features"
                ]
            },
            {
                "key": "4",
                "title": "🎓 Model Training & Testing",
                "description": "Train, test, and optimize CNN models",
                "details": [
                    "• Train new detection models",
                    "• Test model accuracy and performance",
                    "• Model comparison and benchmarking",
                    "• Hyperparameter optimization"
                ],
                "sub_options": [
                    "Train New Model",
                    "Test Model",
                    "Compare Models",
                    "View Model Info",
                    "Optimize Hyperparameters"
                ]
            },
            {
                "key": "5",
                "title": "⚙️  System Configuration & Setup",
                "description": "Configure system settings and environment",
                "details": [
                    "• Virtual environment setup",
                    "• TensorFlow configuration",
                    "• Path verification",
                    "• System optimization"
                ],
                "sub_options": [
                    "Setup Virtual Environment",
                    "Verify TensorFlow",
                    "Verify System Paths",
                    "Start Task Scheduler",
                    "Stop Task Scheduler",
                    "Optimize System"
                ]
            },
            {
                "key": "6",
                "title": "📈 View Reports & Results",
                "description": "Access detection results and threat reports",
                "details": [
                    "• Detection results and statistics",
                    "• Threat analysis reports",
                    "• System logs and scheduler logs",
                    "• Stress test results"
                ],
                "sub_options": [
                    "View Detection Results",
                    "Generate Threat Report",
                    "View Threat Reports",
                    "View Stress Test Reports",
                    "View System Logs",
                    "View Scheduler Logs",
                    "List All Reports"
                ]
            },
            {
                "key": "7",
                "title": "🔧 Utilities & Tools",
                "description": "Additional tools and utilities",
                "details": [
                    "• Threat analysis tools",
                    "• Whitelist/Blacklist management",
                    "• Dataset and model browsers",
                    "• Archive management"
                ],
                "sub_options": [
                    "Analyze Threat Origins",
                    "View Whitelist",
                    "View Blacklist",
                    "Update Lists",
                    "Threat Reviewer",
                    "List Datasets",
                    "List Models",
                    "View Archives",
                    "Clean Temp Files"
                ]
            },
            {
                "key": "8",
                "title": "📚 Command History",
                "description": "View and rerun previous commands",
                "details": [
                    "• Recent command history",
                    "• Quick command rerun",
                    "• Command timestamps",
                    "• Search command history"
                ],
                "sub_options": [
                    "View History",
                    "Clear History",
                    "Rerun Last Command"
                ]
            },
            {
                "key": "9",
                "title": "💾 Settings & Configuration",
                "description": "Manage application settings",
                "details": [
                    "• Default interface selection",
                    "• Detection parameters",
                    "• Theme customization",
                    "• Auto-save preferences"
                ],
                "sub_options": [
                    "Change Default Interface",
                    "Set Default Duration",
                    "Configure Detection Params",
                    "Save Current Settings"
                ]
            },
            {
                "key": "0",
                "title": "🚪 Exit",
                "description": "Exit the application",
                "details": [
                    "• Save current configuration",
                    "• Clean up temp files",
                    "• Stop background processes",
                    "• Graceful shutdown"
                ],
                "sub_options": []
            }
        ]
        
        if menu_type == "main":
            return main_menu_options
        
        # Return empty list for other menus (can be expanded later)
        return []
    
    def create_menu_panel(self, options: List[Dict], selected_index: Optional[int] = None) -> Panel:
        """Create left menu panel with options"""
        menu_content = Text()
        
        for i, option in enumerate(options):
            # Highlight selected option
            if selected_index is not None and i == selected_index:
                menu_content.append(f"▶ ", style="bold yellow")
                style = "bold yellow on blue"
            else:
                menu_content.append(f"  ", style="")
                style = "white"
            
            menu_content.append(f"[{option['key']}] {option['title']}\n", style=style)
        
        return Panel(
            menu_content,
            title="[bold cyan]Main Menu[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            width=self.menu_width,
            padding=(1, 2)
        )
    
    def create_details_panel(self, option: Dict, stage: str = "select") -> Panel:
        """Create right details panel with information"""
        details_content = Text()
        
        # Title and description
        details_content.append(f"{option['title']}\n", style="bold cyan")
        details_content.append(f"\n{option['description']}\n\n", style="white")
        
        # Details section
        details_content.append("━━━ Details ━━━\n", style="bold yellow")
        for detail in option['details']:
            details_content.append(f"{detail}\n", style="green")
        
        # Sub-options section
        if option['sub_options']:
            details_content.append("\n━━━ Available Actions ━━━\n", style="bold yellow")
            for i, sub_opt in enumerate(option['sub_options'], 1):
                details_content.append(f"  {i}. {sub_opt}\n", style="cyan")
            
            # Instructions
            details_content.append("\n━━━ How to Use ━━━\n", style="bold yellow")
            details_content.append("Press ", style="white")
            details_content.append(f"[{option['key']}]", style="bold yellow")
            details_content.append(" or ", style="white")
            details_content.append("ENTER", style="bold yellow")
            details_content.append(" to open this menu", style="white")
        
        return Panel(
            details_content,
            title="[bold cyan]Details[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            width=self.details_width,
            padding=(1, 2)
        )
    
    def display_two_panel_layout(self, menu_options: List[Dict], selected_index: int, stage: str = "select"):
        """Display two-panel layout with menu and details"""
        self.clear_screen()
        self.update_screen_size()  # Update for responsive design
        
        # Create header
        header = self.create_header()
        self.console.print(header)
        
        # Create menu and details panels
        menu_panel = self.create_menu_panel(menu_options, selected_index)
        details_panel = self.create_details_panel(menu_options[selected_index], stage)
        
        # Display side by side
        columns = Columns([menu_panel, details_panel], equal=False, expand=True)
        self.console.print(columns)
        
        # Create and display footer
        footer = self.create_footer(stage)
        self.console.print(footer)
    
    def main_menu(self):
        """Main menu with immediate action selection"""
        menu_options = self.get_menu_options("main")
        selected_index = 0
        
        while True:
            self.display_two_panel_layout(menu_options, selected_index, "select")
            
            # Get user input
            self.console.print("\n[bold yellow]Your choice:[/bold yellow] ", end="")
            choice = input().strip().lower()
            
            # Handle input
            if choice in ['q', 'quit', 'exit']:
                self.exit_program()
                break
            elif choice == 'h':
                self.show_help()
            elif choice.isdigit() and 0 <= int(choice) <= 9:
                # Direct number selection - immediately execute
                for i, opt in enumerate(menu_options):
                    if opt['key'] == choice:
                        selected_index = i
                        break
                # Execute the selected menu action immediately
                selected_key = menu_options[selected_index]['key']
                self.execute_menu_action(selected_key)
            elif choice == '':  # Enter key - execute currently highlighted option
                selected_key = menu_options[selected_index]['key']
                self.execute_menu_action(selected_key)
    
    def execute_menu_action(self, key: str):
        """Execute action based on menu key"""
        actions = {
            "1": self.detection_menu,
            "2": self.capture_menu,
            "3": self.analysis_menu,
            "4": self.training_menu,
            "5": self.setup_menu,
            "6": self.reports_menu,
            "7": self.utilities_menu,
            "8": self.history_menu,
            "9": self.settings_menu,
            "0": self.exit_program
        }
        
        action = actions.get(key)
        if action:
            action()
    
    def show_help(self):
        """Display help screen"""
        self.clear_screen()
        help_text = """
        ╔════════════════════════════════════════════════════════════╗
        ║                   SECIDS-CNN HELP GUIDE                    ║
        ╚════════════════════════════════════════════════════════════╝
        
        NAVIGATION:
          • Use number keys (1-9, 0) to select menu options
          • Press ENTER to view details (Stage 1)
          • Press ENTER again to execute (Stage 2)
          • Press ESC or B to go back
          • Press Q to quit
          
        TWO-STAGE SYSTEM:
          Stage 1: Selection - View detailed information about option
          Stage 2: Engagement - Execute the selected action
          
        PANELS:
          Left Panel:  Menu options with quick-select keys
          Right Panel: Detailed information and sub-options
          
        SCREEN SCALING:
          • Automatically adapts to terminal size
          • Recommended: 120x30 or larger terminal
          
        TIPS:
          • Hover over options to see details
          • Use number keys for quick access
          • Check footer for available keystrokes
        
        """
        self.console.print(Panel(help_text, title="Help", border_style="cyan"))
        Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    # Submenu implementations with two-panel layout
    def detection_menu(self):
        """Detection submenu with two-panel layout"""
        submenu_options = [
            {"key": "1", "title": "Live Detection (Quick)", "desc": "6s window, 4s interval", "cmd": "live-detect-fast"},
            {"key": "2", "title": "Live Detection (Standard)", "desc": "10s window, 4s interval"},
            {"key": "3", "title": "Live Detection (Slow)", "desc": "20s window, 10s interval"},
            {"key": "4", "title": "Deep Scan (Live)", "desc": "600s duration, 60s interval"},
            {"key": "5", "title": "Deep Scan (File)", "desc": "Multiple passes on file"},
            {"key": "6", "title": "File-Based Detection", "desc": "Analyze CSV file"},
            {"key": "0", "title": "Back to Main Menu", "desc": "Return"},
        ]
        
        selected_index = 0
        
        while True:
            # Display submenu with two-panel layout
            self.clear_screen()
            self.update_screen_size()
            
            # Header
            header = self.create_header()
            self.console.print(header)
            
            # Left panel - menu options
            menu_content = Text()
            menu_content.append("🔍 Live Detection & Monitoring\n\n", style="bold cyan")
            for i, opt in enumerate(submenu_options):
                if i == selected_index:
                    menu_content.append(f"▶ ", style="bold yellow")
                    style = "bold yellow on blue"
                else:
                    menu_content.append(f"  ", style="")
                    style = "white"
                menu_content.append(f"[{opt['key']}] {opt['title']}\n", style=style)
            
            menu_panel = Panel(
                menu_content,
                title="[bold cyan]Detection Options[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED,
                width=self.menu_width,
                padding=(1, 2)
            )
            
            # Right panel - details
            selected_opt = submenu_options[selected_index]
            details_content = Text()
            details_content.append(f"{selected_opt['title']}\n\n", style="bold cyan")
            details_content.append(f"{selected_opt['desc']}\n\n", style="white")
            
            if selected_opt['key'] != "0":
                details_content.append("━━━ Instructions ━━━\n", style="bold yellow")
                details_content.append("1. Press ", style="white")
                details_content.append(f"[{selected_opt['key']}]", style="bold yellow")
                details_content.append(" or ", style="white")
                details_content.append("ENTER", style="bold yellow")
                details_content.append(" to execute\n", style="white")
                details_content.append("2. Enter required parameters\n", style="white")
                details_content.append("3. Watch progress on screen\n\n", style="white")
                details_content.append("━━━ Status ━━━\n", style="bold yellow")
                details_content.append("Ready to execute", style="green")
            
            details_panel = Panel(
                details_content,
                title="[bold cyan]Action Details[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED,
                width=self.details_width,
                padding=(1, 2)
            )
            
            # Display
            columns = Columns([menu_panel, details_panel], equal=False, expand=True)
            self.console.print(columns)
            
            # Footer
            footer = self.create_footer()
            self.console.print(footer)
            
            # Get input
            self.console.print("\n[bold yellow]Your choice:[/bold yellow] ", end="")
            choice = input().strip().lower()
            
            # Handle choice
            if choice == "0" or choice in ['q', 'quit', 'exit', 'b', 'back']:
                break
            elif choice.isdigit() and 1 <= int(choice) <= 6:
                # Find and execute the selected option
                for i, opt in enumerate(submenu_options):
                    if opt['key'] == choice:
                        selected_index = i
                        break
                
                # Execute the action
                self._execute_detection_action(choice)
            elif choice == '':  # Enter key
                if selected_index < len(submenu_options) - 1:  # Not "Back"
                    self._execute_detection_action(submenu_options[selected_index]['key'])
                else:
                    break
    
    def _execute_detection_action(self, choice: str):
        """Execute detection action and show progress"""
        self.clear_screen()
        self.console.print("[bold cyan]Executing detection...[/bold cyan]\n")
        
        if choice == "1":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            if self.command_lib:
                params = {'iface': iface}
                self._execute_with_feedback('live-detect-fast', params)
            else:
                self._run_command(f"sudo python3 SecIDS-CNN/run_model.py live --iface {iface} --window 6 --interval 4")
        elif choice == "2":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(f"sudo python3 SecIDS-CNN/run_model.py live --iface {iface} --window 10 --interval 4")
        elif choice == "3":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(f"sudo python3 SecIDS-CNN/run_model.py live --iface {iface} --window 20 --interval 10")
        elif choice == "4":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(f"sudo python3 Tools/deep_scan.py --iface {iface} --duration 600 --interval 60")
        elif choice == "5":
            file_path = Prompt.ask("CSV file path")
            self._run_command(f"python3 Tools/deep_scan.py --file {file_path} --passes 10")
        elif choice == "6":
            file_path = Prompt.ask("CSV file path", default="SecIDS-CNN/datasets/MD_20260129_145407.csv")
            self._run_command(f".venv_test/bin/python SecIDS-CNN/run_model.py file {file_path}")
        
        Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def capture_menu(self):
        """Capture submenu with network capture options - two-panel layout"""
        submenu_options = [
            {"key": "1", "title": "Quick Capture (120s)", "desc": "Fast network capture"},
            {"key": "2", "title": "Custom Duration Capture", "desc": "Specify duration"},
            {"key": "3", "title": "Continuous Live Capture", "desc": "Continuous monitoring"},
            {"key": "4", "title": "List Captures", "desc": "View all captures"},
            {"key": "5", "title": "Pipeline Capture & Analyze", "desc": "Capture and analyze"},
            {"key": "0", "title": "Back to Main Menu", "desc": "Return"},
        ]
        
        selected_index = 0
        
        while True:
            self.clear_screen()
            self.update_screen_size()
            
            header = self.create_header()
            self.console.print(header)
            
            # Left panel
            menu_content = Text()
            menu_content.append("📡 Network Capture Operations\n\n", style="bold cyan")
            for i, opt in enumerate(submenu_options):
                if i == selected_index:
                    menu_content.append(f"▶ ", style="bold yellow")
                    style = "bold yellow on blue"
                else:
                    menu_content.append(f"  ", style="")
                    style = "white"
                menu_content.append(f"[{opt['key']}] {opt['title']}\n", style=style)
            
            menu_panel = Panel(menu_content, title="[bold cyan]Capture Options[/bold cyan]",
                             border_style="cyan", box=box.ROUNDED, width=self.menu_width, padding=(1, 2))
            
            # Right panel
            selected_opt = submenu_options[selected_index]
            details_content = Text()
            details_content.append(f"{selected_opt['title']}\n\n", style="bold cyan")
            details_content.append(f"{selected_opt['desc']}\n\n", style="white")
            
            if selected_opt['key'] != "0":
                details_content.append("Press ", style="white")
                details_content.append(f"[{selected_opt['key']}]", style="bold yellow")
                details_content.append(" or ENTER to execute", style="white")
            
            details_panel = Panel(details_content, title="[bold cyan]Details[/bold cyan]",
                                border_style="cyan", box=box.ROUNDED, width=self.details_width, padding=(1, 2))
            
            columns = Columns([menu_panel, details_panel], equal=False, expand=True)
            self.console.print(columns)
            
            footer = self.create_footer()
            self.console.print(footer)
            
            self.console.print("\n[bold yellow]Your choice:[/bold yellow] ", end="")
            choice = input().strip().lower()
            
            if choice == "0" or choice in ['q', 'quit', 'exit', 'b', 'back']:
                break
            elif choice.isdigit() and 1 <= int(choice) <= 5:
                for i, opt in enumerate(submenu_options):
                    if opt['key'] == choice:
                        selected_index = i
                        break
                self._execute_capture_action(choice)
            elif choice == '':
                if selected_index < len(submenu_options) - 1:
                    self._execute_capture_action(submenu_options[selected_index]['key'])
                else:
                    break
    
    def _execute_capture_action(self, choice: str):
        """Execute capture action"""
        self.clear_screen()
        self.console.print("[bold cyan]Executing capture operation...[/bold cyan]\n")
        
        if choice == "1":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(f"sudo dumpcap -i {iface} -a duration:120 -w Captures/capture_$(date +%s).pcap")
        elif choice == "2":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            duration = Prompt.ask("Duration (seconds)", default="120")
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(f"sudo dumpcap -i {iface} -a duration:{duration} -w Captures/capture_$(date +%s).pcap")
        elif choice == "3":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(f"sudo python3 Tools/continuous_live_capture.py --iface {iface} --window 120 --interval 120")
        elif choice == "4":
            self._run_command("ls -lh Captures/")
        elif choice == "5":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            duration = Prompt.ask("Duration (seconds)", default="240")
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(f"python3 Tools/pipeline_orchestrator.py --mode capture --iface {iface} --duration {duration}")
        
        Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def analysis_menu(self):
        """Analysis submenu with file analysis options - two-panel layout"""
        submenu_options = [
            {"key": "1", "title": "Analyze CSV File", "desc": "Detect threats in CSV"},
            {"key": "2", "title": "Analyze PCAP File", "desc": "Convert and analyze PCAP"},
            {"key": "3", "title": "Batch Analysis (All CSV)", "desc": "Analyze all files"},
            {"key": "4", "title": "PCAP to CSV Conversion", "desc": "Convert PCAP format"},
            {"key": "5", "title": "Enhance Dataset Features", "desc": "Add calculated features"},
            {"key": "0", "title": "Back to Main Menu", "desc": "Return"},
        ]
        
        selected_index = 0
        
        while True:
            self.clear_screen()
            self.update_screen_size()
            
            header = self.create_header()
            self.console.print(header)
            
            # Left panel
            menu_content = Text()
            menu_content.append("📊 File-Based Analysis\n\n", style="bold cyan")
            for i, opt in enumerate(submenu_options):
                if i == selected_index:
                    menu_content.append(f"▶ ", style="bold yellow")
                    style = "bold yellow on blue"
                else:
                    menu_content.append(f"  ", style="")
                    style = "white"
                menu_content.append(f"[{opt['key']}] {opt['title']}\n", style=style)
            
            menu_panel = Panel(menu_content, title="[bold cyan]Analysis Options[/bold cyan]",
                             border_style="cyan", box=box.ROUNDED, width=self.menu_width, padding=(1, 2))
            
            # Right panel
            selected_opt = submenu_options[selected_index]
            details_content = Text()
            details_content.append(f"{selected_opt['title']}\n\n", style="bold cyan")
            details_content.append(f"{selected_opt['desc']}\n\n", style="white")
            
            if selected_opt['key'] != "0":
                details_content.append("Press ", style="white")
                details_content.append(f"[{selected_opt['key']}]", style="bold yellow")
                details_content.append(" or ENTER to execute", style="white")
            
            details_panel = Panel(details_content, title="[bold cyan]Details[/bold cyan]",
                                border_style="cyan", box=box.ROUNDED, width=self.details_width, padding=(1, 2))
            
            columns = Columns([menu_panel, details_panel], equal=False, expand=True)
            self.console.print(columns)
            
            footer = self.create_footer()
            self.console.print(footer)
            
            self.console.print("\n[bold yellow]Your choice:[/bold yellow] ", end="")
            choice = input().strip().lower()
            
            if choice == "0" or choice in ['q', 'quit', 'exit', 'b', 'back']:
                break
            elif choice.isdigit() and 1 <= int(choice) <= 5:
                for i, opt in enumerate(submenu_options):
                    if opt['key'] == choice:
                        selected_index = i
                        break
                self._execute_analysis_action(choice)
            elif choice == '':
                if selected_index < len(submenu_options) - 1:
                    self._execute_analysis_action(submenu_options[selected_index]['key'])
                else:
                    break
    
    def _execute_analysis_action(self, choice: str):
        """Execute analysis action"""
        self.clear_screen()
        self.console.print("[bold cyan]Executing analysis...[/bold cyan]\n")
        
        if choice == "1":
            file_path = Prompt.ask("CSV file path", default="SecIDS-CNN/datasets/MD_20260129_145407.csv")
            self._run_command(f".venv_test/bin/python SecIDS-CNN/run_model.py file {file_path}")
        elif choice == "2":
            pcap_file = Prompt.ask("PCAP file path")
            self._run_command(f"python3 Tools/pcap_to_csv.py {pcap_file}")
        elif choice == "3":
            self._run_command("python3 SecIDS-CNN/run_model.py file SecIDS-CNN/datasets/*.csv")
        elif choice == "4":
            pcap_file = Prompt.ask("PCAP file path")
            output_csv = Prompt.ask("Output CSV path", default="Results/converted.csv")
            self._run_command(f"python3 Tools/pcap_to_csv.py {pcap_file} -o {output_csv}")
        elif choice == "5":
            dataset = Prompt.ask("Dataset path")
            self._run_command(f"python3 Scripts/refine_datasets.py {dataset}")
        
        Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def training_menu(self):
        """Training submenu with model training options"""
        self.clear_screen()
        
        options = Panel(
            "[bold cyan]Model Training & Testing[/bold cyan]\n\n"
            "[white]1.[/white] Train SecIDS-CNN Model\n"
            "[white]2.[/white] Train Unified Model\n"
            "[white]3.[/white] Test Model\n"
            "[white]4.[/white] Compare Models\n"
            "[white]5.[/white] View Model Info\n"
            "[white]6.[/white] Full Training Pipeline\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        
        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")
        
        if choice == "1":
            self._run_command("python3 SecIDS-CNN/train_and_test.py")
        elif choice == "2":
            self._run_command("python3 Model_Tester/Code/train_unified_model.py")
        elif choice == "3":
            self._run_command("python3 Model_Tester/Code/test_unified_model.py")
        elif choice == "4":
            self._run_command("python3 Model_Tester/Code/compare_models.py")
        elif choice == "5":
            self._run_command("ls -lh SecIDS-CNN/*.h5 Model_Tester/Code/models/")
        elif choice == "6":
            self._run_command("python3 Tools/pipeline_orchestrator.py --mode train")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def setup_menu(self):
        """Setup submenu with system configuration"""
        self.clear_screen()
        
        options = Panel(
            "[bold cyan]System Configuration & Setup[/bold cyan]\n\n"
            "[white]1.[/white] Check Network Interfaces\n"
            "[white]2.[/white] Verify TensorFlow\n"
            "[white]3.[/white] Install Dependencies\n"
            "[white]4.[/white] System Diagnostics\n"
            "[white]5.[/white] View Python Environment\n"
            "[white]6.[/white] Start Task Scheduler\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        
        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")
        
        if choice == "1":
            self._run_command("ip link show")
        elif choice == "2":
            self._run_command("python3 -c 'import tensorflow as tf; print(f\"TensorFlow: {tf.__version__}\")'")
        elif choice == "3":
            self._run_command("pip install -r requirements.txt")
        elif choice == "4":
            self._run_command("python3 Tools/system_checker.py")
        elif choice == "5":
            self._run_command("python3 -c 'import sys; print(sys.executable); print(sys.version)'")
        elif choice == "6":
            self._run_command("python3 Auto_Update/task_scheduler.py &")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def reports_menu(self):
        """Reports submenu with result viewing"""
        self.clear_screen()
        
        options = Panel(
            "[bold cyan]View Reports & Results[/bold cyan]\n\n"
            "[white]1.[/white] List Detection Results\n"
            "[white]2.[/white] List Threat Reports\n"
            "[white]3.[/white] List Deep Scan Reports\n"
            "[white]4.[/white] View Latest Report\n"
            "[white]5.[/white] View System Logs\n"
            "[white]6.[/white] Generate New Threat Report\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        
        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")
        
        if choice == "1":
            self._run_command("ls -lht Results/*.csv | head -20")
        elif choice == "2":
            self._run_command("ls -lht Results/*report*.md Results/*report*.json | head -20")
        elif choice == "3":
            self._run_command("ls -lht Results/deep_scan*.json | head -20")
        elif choice == "4":
            self._run_command("cat $(ls -t Results/*report*.md 2>/dev/null | head -1)")
        elif choice == "5":
            self._run_command("ls -lht Logs/ | head -20")
        elif choice == "6":
            result_file = Prompt.ask("Detection results CSV path")
            self._run_command(f"python3 Tools/report_generator.py {result_file}")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def utilities_menu(self):
        """Utilities submenu with tools"""
        self.clear_screen()
        
        options = Panel(
            "[bold cyan]Utilities & Tools[/bold cyan]\n\n"
            "[white]1.[/white] List Datasets\n"
            "[white]2.[/white] List Models\n"
            "[white]3.[/white] List Captures\n"
            "[white]4.[/white] View Whitelist\n"
            "[white]5.[/white] View Blacklist\n"
            "[white]6.[/white] Update Device Lists\n"
            "[white]7.[/white] Clean Temp Files\n"
            "[white]8.[/white] View Command Library\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        
        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")
        
        if choice == "1":
            self._run_command("ls -lh SecIDS-CNN/datasets/ Archives/")
        elif choice == "2":
            self._run_command("ls -lh SecIDS-CNN/*.h5 Models/ Model_Tester/Code/models/")
        elif choice == "3":
            self._run_command("ls -lh Captures/")
        elif choice == "4":
            self._run_command("cat Device_Profile/whitelists/whitelist_*.json | tail -50")
        elif choice == "5":
            self._run_command("cat Device_Profile/Blacklist/blacklist_*.json | tail -50")
        elif choice == "6":
            self._run_command("python3 Device_Profile/list_manager.py --update")
        elif choice == "7":
            if Confirm.ask("Clean temporary files?"):
                self._run_command("rm -f Captures/capture_temp_*.pcap && rm -f /tmp/secids_*")
        elif choice == "8":
            if self.command_lib:
                self.command_lib.list_commands()
            else:
                self._run_command("python3 Tools/command_library.py list")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def history_menu(self):
        """History submenu with command history"""
        self.clear_screen()
        
        if self.command_lib:
            self.command_lib.show_history(20)
        else:
            # Fallback to UI config history
            if self.config.get('history'):
                self.console.print("\n[bold cyan]Command History:[/bold cyan]\n")
                for entry in self.config['history'][-20:]:
                    self.console.print(f"[yellow]{entry['timestamp']}[/yellow]: {entry['command']}")
            else:
                self.console.print("[yellow]No command history available[/yellow]")
        
        choice = Prompt.ask("\n[bold yellow]Options[/bold yellow] [white](c=clear, r=rerun last, Enter=back)[/white]", default="")
        
        if choice.lower() == 'c' and Confirm.ask("Clear history?"):
            if self.command_lib:
                self.command_lib.history = []
                self.command_lib.save_history()
            self.config['history'] = []
            self.save_config()
            self.console.print("[green]✓ History cleared[/green]")
        elif choice.lower() == 'r' and self.config.get('history'):
            last_cmd = self.config['history'][-1]['command']
            self.console.print(f"\n[yellow]Rerunning:[/yellow] {last_cmd}")
            self._run_command(last_cmd)
        
        if choice:
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def settings_menu(self):
        """Settings submenu with configuration"""
        self.clear_screen()
        
        self.console.print("\n[bold cyan]Current Settings:[/bold cyan]\n")
        self.console.print(f"Default Interface: [yellow]{self.config.get('last_interface', 'eth0')}[/yellow]")
        self.console.print(f"Default Duration: [yellow]{self.config.get('last_duration', 60)}s[/yellow]")
        self.console.print(f"Default Window: [yellow]{self.config.get('last_window', 5)}s[/yellow]")
        self.console.print(f"Default Interval: [yellow]{self.config.get('last_interval', 2)}s[/yellow]")
        
        options = Panel(
            "\n[white]1.[/white] Change Default Interface\n"
            "[white]2.[/white] Change Default Duration\n"
            "[white]3.[/white] Change Default Window\n"
            "[white]4.[/white] Change Default Interval\n"
            "[white]5.[/white] Save & Apply Settings\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        
        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")
        
        if choice == "1":
            new_iface = Prompt.ask("New default interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = new_iface
            self.console.print(f"[green]✓ Set to {new_iface}[/green]")
        elif choice == "2":
            new_duration = Prompt.ask("New default duration (seconds)", default=str(self.config.get('last_duration', 60)))
            self.config['last_duration'] = int(new_duration)
            self.console.print(f"[green]✓ Set to {new_duration}s[/green]")
        elif choice == "3":
            new_window = Prompt.ask("New default window (seconds)", default=str(self.config.get('last_window', 5)))
            self.config['last_window'] = int(new_window)
            self.console.print(f"[green]✓ Set to {new_window}s[/green]")
        elif choice == "4":
            new_interval = Prompt.ask("New default interval (seconds)", default=str(self.config.get('last_interval', 2)))
            self.config['last_interval'] = int(new_interval)
            self.console.print(f"[green]✓ Set to {new_interval}s[/green]")
        elif choice == "5":
            self.save_config()
            self.console.print("[green]✓ Settings saved[/green]")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def _run_command(self, command: str):
        """Execute a shell command and display output"""
        self.console.print(f"\n[dim]Executing: {command}[/dim]\n")
        
        # Add to history
        if 'history' not in self.config:
            self.config['history'] = []
        self.config['history'].append({
            'command': command,
            'timestamp': datetime.now().isoformat()
        })
        self.save_config()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.project_root),
                capture_output=False,
                text=True
            )
            if result.returncode == 0:
                self.console.print("\n[green]✓ Command completed successfully[/green]")
            else:
                self.console.print(f"\n[red]✗ Command exited with code {result.returncode}[/red]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
    
    def _execute_with_feedback(self, shortcut: str, params: Dict = None):
        """Execute command from library with feedback"""
        if not self.command_lib:
            self.console.print("[red]Command library not available[/red]")
            return
        
        try:
            self.command_lib.execute_command(shortcut, params, dry_run=False)
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
    
    def exit_program(self):
        """Exit the program"""
        self.save_config()
        self.clear_screen()
        self.console.print("\n[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
        self.console.print("[bold cyan]║   Thank you for using SecIDS-CNN!     ║[/bold cyan]")
        self.console.print("[bold cyan]║          Stay secure! 🛡️               ║[/bold cyan]")
        self.console.print("[bold cyan]╚════════════════════════════════════════╝[/bold cyan]\n")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Main run loop"""
        try:
            while self.running:
                self.main_menu()
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Interrupted by user[/yellow]")
            self.exit_program()
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    ui = EnhancedSecIDSUI()
    ui.run()


if __name__ == "__main__":
    main()

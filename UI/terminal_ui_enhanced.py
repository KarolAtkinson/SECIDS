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
import re
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
        self.active_autostart_done = False
        self.passive_autostart_done = False
        
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
            except (json.JSONDecodeError, OSError) as exc:
                self.console.print(f"[yellow]Warning: Could not load config ({exc}), using defaults[/yellow]")
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

    def _parse_traffic_log(self, log_path: Path) -> Dict:
        """Parse recent live-detection log lines into traffic counters."""
        if not log_path.exists():
            return {
                "source": log_path.name,
                "window": 0,
                "flows_window": 0,
                "threats_window": 0,
                "total_flows": 0,
                "total_threats": 0,
                "last_update": "n/a",
                "status": "No log data"
            }

        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as handle:
                lines = handle.readlines()[-300:]

            window_pattern = re.compile(
                r"\[(?P<time>\d{2}:\d{2}:\d{2})\] Window #(?P<window>\d+): (?P<flows>\d+) flows \| "
                r"Threats: (?P<threats>\d+) \| Total: (?P<total_flows>\d+) flows, (?P<total_threats>\d+) threats"
            )
            no_packets_pattern = re.compile(r"\[(?P<time>\d{2}:\d{2}:\d{2})\] No packets in window")

            for line in reversed(lines):
                match = window_pattern.search(line)
                if match:
                    groups = match.groupdict()
                    return {
                        "source": log_path.name,
                        "window": int(groups["window"]),
                        "flows_window": int(groups["flows"]),
                        "threats_window": int(groups["threats"]),
                        "total_flows": int(groups["total_flows"]),
                        "total_threats": int(groups["total_threats"]),
                        "last_update": groups["time"],
                        "status": "Active"
                    }

                no_packets = no_packets_pattern.search(line)
                if no_packets:
                    return {
                        "source": log_path.name,
                        "window": 0,
                        "flows_window": 0,
                        "threats_window": 0,
                        "total_flows": 0,
                        "total_threats": 0,
                        "last_update": no_packets.group("time"),
                        "status": "No packets in latest window"
                    }
        except Exception as exc:
            return {
                "source": log_path.name,
                "window": 0,
                "flows_window": 0,
                "threats_window": 0,
                "total_flows": 0,
                "total_threats": 0,
                "last_update": "n/a",
                "status": f"Log parse error: {exc}"
            }

        return {
            "source": log_path.name,
            "window": 0,
            "flows_window": 0,
            "threats_window": 0,
            "total_flows": 0,
            "total_threats": 0,
            "last_update": "n/a",
            "status": "Waiting for traffic"
        }

    def get_traffic_counter(self) -> Dict:
        """Get live traffic acquisition and analysis counters."""
        running = subprocess.run(
            "pgrep -f 'SecIDS-CNN/run_model.py live' >/dev/null",
            shell=True,
            cwd=str(self.project_root)
        ).returncode == 0

        active_log = Path("/tmp/secids_active_autostart.log")
        passive_log = Path("/tmp/secids_passive_autostart.log")

        existing_logs = [path for path in [active_log, passive_log] if path.exists()]
        if existing_logs:
            source_log = max(existing_logs, key=lambda path: path.stat().st_mtime)
        else:
            source_log = active_log

        counters = self._parse_traffic_log(source_log)
        counters["running"] = running
        counters["interface"] = str(self.config.get("last_interface", "any"))
        counters["pipeline"] = "Gather → Analyze → Identify → Countermeasure"
        return counters

    def create_traffic_counter_panel(self) -> Panel:
        """Create traffic counter status panel for live pipeline visibility."""
        stats = self.get_traffic_counter()
        running_text = "RUNNING" if stats["running"] else "STOPPED"
        running_style = "green" if stats["running"] else "red"

        content = Text()
        content.append("Traffic Counter  ", style="bold cyan")
        content.append(f"[{running_text}]\n", style=f"bold {running_style}")
        content.append(f"Iface: {stats['interface']}  |  Pipeline: {stats['pipeline']}\n", style="white")
        content.append(
            f"Window: {stats['window']}  Flows(win): {stats['flows_window']}  Threats(win): {stats['threats_window']}\n",
            style="yellow"
        )
        content.append(
            f"Totals: {stats['total_flows']} flows, {stats['total_threats']} threats  |  Last: {stats['last_update']}\n",
            style="green"
        )
        content.append(f"Source: {stats['source']}  |  Status: {stats['status']}", style="dim white")

        return Panel(
            content,
            title="[bold cyan]Live Pipeline Status[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 2)
        )
    
    def get_menu_options(self, menu_type: str) -> List[Dict]:
        """Get menu options with details for specified menu"""

        root_menu_options = [
            {
                "key": "1",
                "title": "🛡️ Active",
                "description": "Full-featured SecIDS-CNN control surface",
                "details": [
                    "• Access complete detection, capture, analysis, training, and reporting",
                    "• Includes all previous main menu operations",
                    "• Best for full operational control"
                ],
                "sub_options": [
                    "Detection",
                    "Capture",
                    "Analysis",
                    "Training",
                    "Setup",
                    "Reports",
                    "Utilities",
                    "History",
                    "Settings"
                ]
            },
            {
                "key": "2",
                "title": "⚡ Passive",
                "description": "Minimal passive-mode workflow",
                "details": [
                    "• Launch passive countermeasure mode",
                    "• Use simplified monitoring/response controls",
                    "• Best for low-interaction defensive operation"
                ],
                "sub_options": [
                    "Launch Passive Countermeasure UI",
                    "View Passive Logs",
                    "Back"
                ]
            },
            {
                "key": "0",
                "title": "🚪 Exit",
                "description": "Exit the application",
                "details": [
                    "• Save current configuration",
                    "• Graceful shutdown"
                ],
                "sub_options": []
            }
        ]

        active_menu_options = [
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
            return root_menu_options

        if menu_type == "active":
            return active_menu_options
        
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

        # Show traffic counter beneath main panels
        self.console.print(self.create_traffic_counter_panel())
        
        # Create and display footer
        footer = self.create_footer(stage)
        self.console.print(footer)
    
    def main_menu(self):
        """Top-level menu: Active / Passive"""
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
            elif choice.isdigit() and 0 <= int(choice) <= 2:
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
        """Execute top-level action based on menu key"""
        actions = {
            "1": self.active_menu,
            "2": self.passive_menu,
            "0": self.exit_program
        }
        
        action = actions.get(key)
        if action:
            action()

    def active_menu(self):
        """Active mode menu (legacy full main menu)"""
        if not self.active_autostart_done:
            self._autostart_traffic_monitor(mode="active")
            self.active_autostart_done = True

        menu_options = self.get_menu_options("active")
        selected_index = 0

        while True:
            self.display_two_panel_layout(menu_options, selected_index, "select")

            self.console.print("\n[bold yellow]Active choice:[/bold yellow] ", end="")
            choice = input().strip().lower()

            if choice in ['q', 'quit', 'exit', 'b', 'back', '0']:
                break
            elif choice == 'h':
                self.show_help()
            elif choice.isdigit() and 1 <= int(choice) <= 9:
                for i, opt in enumerate(menu_options):
                    if opt['key'] == choice:
                        selected_index = i
                        break
                selected_key = menu_options[selected_index]['key']
                self.execute_active_menu_action(selected_key)
            elif choice == '':
                selected_key = menu_options[selected_index]['key']
                self.execute_active_menu_action(selected_key)

    def execute_active_menu_action(self, key: str):
        """Execute action in active mode menu"""
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
        }

        action = actions.get(key)
        if action:
            action()

    def passive_menu(self):
        """Passive mode submenu"""
        if not self.passive_autostart_done:
            self._autostart_traffic_monitor(mode="passive")
            self.passive_autostart_done = True

        self.clear_screen()

        options = Panel(
            "[bold cyan]Passive Mode Menu[/bold cyan]\n\n"
            "[white]1.[/white] Launch Passive Countermeasure UI\n"
            "[white]2.[/white] View Passive Logs\n"
            "[white]3.[/white] Stop Passive Background Monitor\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        self.console.print(self.create_traffic_counter_panel())

        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")

        if choice == "1":
            self._run_command(f"{sys.executable} Countermeasures/passive_ui.py")
        elif choice == "2":
            self._run_command("ls -lht Countermeasures/logs/ | head -20")
        elif choice == "3":
            self._run_command("pkill -f 'SecIDS-CNN/run_model.py live' || true")

        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")

    def _autostart_traffic_monitor(self, mode: str = "active"):
        """Auto-start background live traffic processing with Wireshark integration."""
        iface = str(self.config.get('last_interface', 'any')).strip() or 'any'

        if not self._ensure_sudo_capture_ready():
            self.console.print(
                "[yellow]⚠️  Auto-start skipped: sudo authentication is required for live packet capture.[/yellow]"
            )
            return

        if mode == "passive":
            window = str(self.config.get('last_window', 20))
            interval = str(self.config.get('last_interval', 10))
            backend = "tf"
            log_file = "/tmp/secids_passive_autostart.log"
        else:
            window = str(self.config.get('last_window', 10))
            interval = str(self.config.get('last_interval', 4))
            backend = "tf"
            log_file = "/tmp/secids_active_autostart.log"

        self.console.print(
            f"[cyan]Auto-starting {mode} traffic monitor in background on interface '{iface}'...[/cyan]"
        )

        self._run_command(
            "pgrep -f 'SecIDS-CNN/run_model.py live' >/dev/null || "
            f"nohup sudo -n {sys.executable} SecIDS-CNN/run_model.py live --iface {iface} "
            f"--window {window} --interval {interval} --backend {backend} > {log_file} 2>&1 &"
        )

        started = self._run_command("pgrep -f 'SecIDS-CNN/run_model.py live' >/dev/null")
        if started:
            self.console.print(
                "[green]✓ Background live processing started (Wireshark manager auto-connects inside live mode)[/green]"
            )
            self._run_command(f"tail -n 20 {log_file}")
        else:
            self.console.print(
                "[red]✗ Background live processing did not start. Check sudo/capture permissions and interface.[/red]"
            )

    def _ensure_sudo_capture_ready(self) -> bool:
        """Ensure sudo credentials are available for non-interactive background capture launch."""
        if self._run_command("sudo -n true", save_history=False):
            return True

        self.console.print(
            "[yellow]Sudo authentication is required to capture live traffic.\n"
            "Please enter your password once to cache credentials.[/yellow]"
        )
        return self._run_command("sudo -v", save_history=False)
    
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
            {"key": "1", "title": "Live Detection (Standard)", "desc": "10s window, 4s interval"},
            {"key": "2", "title": "Live Detection (Fast)", "desc": "6s window, 4s interval"},
            {"key": "3", "title": "Live Detection (Slow)", "desc": "20s window, 10s interval"},
            {"key": "4", "title": "Live Detection (Custom)", "desc": "Custom window/interval/backend"},
            {"key": "5", "title": "Deep Scan (Live)", "desc": "Comprehensive live scan"},
            {"key": "6", "title": "Deep Scan (File)", "desc": "Multi-pass file analysis"},
            {"key": "7", "title": "File-Based Detection", "desc": "Analyze CSV file"},
            {"key": "8", "title": "Stop Detection Processes", "desc": "Stop running live/deep scans"},
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
            elif choice.isdigit() and 1 <= int(choice) <= 8:
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
                self._execute_library_shortcut('live-detect', {'iface': iface})
            else:
                self._run_command(
                    f"sudo {sys.executable} SecIDS-CNN/run_model.py live --iface {iface} --window 10 --interval 4"
                )
        elif choice == "2":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            if self.command_lib:
                self._execute_library_shortcut('live-detect-fast', {'iface': iface})
            else:
                self._run_command(
                    f"sudo {sys.executable} SecIDS-CNN/run_model.py live --iface {iface} --window 6 --interval 4"
                )
        elif choice == "3":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            if self.command_lib:
                self._execute_library_shortcut('live-detect-slow', {'iface': iface})
            else:
                self._run_command(
                    f"sudo {sys.executable} SecIDS-CNN/run_model.py live --iface {iface} --window 20 --interval 10"
                )
        elif choice == "4":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            window = Prompt.ask("Window (seconds)", default=str(self.config.get('last_window', 10)))
            interval = Prompt.ask("Interval (seconds)", default=str(self.config.get('last_interval', 4)))
            backend = Prompt.ask("Backend (tf/unified)", default="tf")
            self.config['last_interface'] = iface
            self.config['last_window'] = float(window)
            self.config['last_interval'] = float(interval)
            self.save_config()
            self._run_command(
                f"sudo {sys.executable} SecIDS-CNN/run_model.py live --iface {iface} "
                f"--window {window} --interval {interval} --backend {backend}"
            )
        elif choice == "5":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            duration = Prompt.ask("Duration (seconds)", default="600")
            interval = Prompt.ask("Interval (seconds)", default="60")
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(
                f"sudo {sys.executable} Tools/deep_scan.py --iface {iface} "
                f"--duration {duration} --interval {interval}"
            )
        elif choice == "6":
            file_path = Prompt.ask("CSV file path")
            passes = Prompt.ask("Passes", default="10")
            self._run_command(f"{sys.executable} Tools/deep_scan.py --file {file_path} --passes {passes}")
        elif choice == "7":
            file_path = Prompt.ask("CSV file path", default="Archives/Test1.csv")
            if self.command_lib:
                self._execute_library_shortcut('detect-file', {'csv_file': file_path})
            else:
                self._run_command(f"{sys.executable} SecIDS-CNN/run_model.py file {file_path}")
        elif choice == "8":
            self._run_command("pkill -f 'SecIDS-CNN/run_model.py live' || true")
            self._run_command("pkill -f 'Tools/deep_scan.py --iface' || true")
        
        Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def capture_menu(self):
        """Capture submenu with network capture options - two-panel layout"""
        submenu_options = [
            {"key": "1", "title": "Quick Capture (60s)", "desc": "Fast one-minute capture"},
            {"key": "2", "title": "Standard Capture (120s)", "desc": "Two-minute capture"},
            {"key": "3", "title": "Extended Capture (300s)", "desc": "Five-minute capture"},
            {"key": "4", "title": "Custom Duration Capture", "desc": "Specify custom duration"},
            {"key": "5", "title": "List Interfaces", "desc": "Show available network interfaces"},
            {"key": "6", "title": "List Captures", "desc": "View saved capture files"},
            {"key": "7", "title": "Pipeline Capture & Analyze", "desc": "Capture and analyze"},
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
            elif choice.isdigit() and 1 <= int(choice) <= 7:
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
            if self.command_lib:
                self._execute_library_shortcut('capture-custom', {'iface': iface, 'duration': 60})
            else:
                self._run_command(f"sudo dumpcap -i {iface} -a duration:60 -w Captures/capture_$(date +%s).pcap")
        elif choice == "2":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            if self.command_lib:
                self._execute_library_shortcut('capture-quick', {'iface': iface})
            else:
                self._run_command(f"sudo dumpcap -i {iface} -a duration:120 -w Captures/capture_$(date +%s).pcap")
        elif choice == "3":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            self.config['last_interface'] = iface
            self.save_config()
            self._run_command(f"sudo dumpcap -i {iface} -a duration:300 -w Captures/capture_$(date +%s).pcap")
        elif choice == "4":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            duration = Prompt.ask("Duration (seconds)", default=str(self.config.get('last_duration', 120)))
            self.config['last_interface'] = iface
            self.config['last_duration'] = int(duration)
            self.save_config()
            if self.command_lib:
                self._execute_library_shortcut('capture-custom', {'iface': iface, 'duration': duration})
            else:
                self._run_command(
                    f"sudo dumpcap -i {iface} -a duration:{duration} -w Captures/capture_$(date +%s).pcap"
                )
        elif choice == "5":
            self._run_command("ip -br link show")
        elif choice == "6":
            if self.command_lib:
                self._execute_library_shortcut('list-captures')
            else:
                self._run_command("ls -lh Captures/")
        elif choice == "7":
            iface = Prompt.ask("Network interface", default=self.config.get('last_interface', 'eth0'))
            duration = Prompt.ask("Duration (seconds)", default="240")
            self.config['last_interface'] = iface
            self.save_config()
            if self.command_lib:
                self._execute_library_shortcut('pipeline-capture', {'iface': iface, 'duration': duration})
            else:
                self._run_command(
                    f"{sys.executable} Tools/pipeline_orchestrator.py --mode capture --iface {iface} --duration {duration}"
                )
        
        Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def analysis_menu(self):
        """Analysis submenu with file analysis options - two-panel layout"""
        submenu_options = [
            {"key": "1", "title": "Analyze CSV File", "desc": "Detect threats in CSV"},
            {"key": "2", "title": "Analyze Test1 Dataset", "desc": "Run detection on Test1.csv"},
            {"key": "3", "title": "Analyze Test2 Dataset", "desc": "Run detection on Test2.csv"},
            {"key": "4", "title": "Analyze All Datasets", "desc": "Batch analyze all dataset CSVs"},
            {"key": "5", "title": "Batch Analysis (Custom)", "desc": "Analyze multiple files"},
            {"key": "6", "title": "PCAP to CSV Conversion", "desc": "Convert PCAP format"},
            {"key": "7", "title": "Enhance Dataset Features", "desc": "Add calculated features"},
            {"key": "8", "title": "Threat Reviewer", "desc": "Review threat profiles and patterns"},
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
            elif choice.isdigit() and 1 <= int(choice) <= 8:
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
            file_path = Prompt.ask("CSV file path", default="Archives/Test1.csv")
            if self.command_lib:
                self._execute_library_shortcut('detect-file', {'csv_file': file_path})
            else:
                self._run_command(f"{sys.executable} SecIDS-CNN/run_model.py file {file_path}")
        elif choice == "2":
            self._run_command(f"{sys.executable} SecIDS-CNN/run_model.py file Archives/Test1.csv")
        elif choice == "3":
            self._run_command(f"{sys.executable} SecIDS-CNN/run_model.py file Archives/Test2.csv")
        elif choice == "4":
            self._run_command(f"{sys.executable} SecIDS-CNN/run_model.py file --all")
        elif choice == "5":
            csv_files = Prompt.ask("CSV file path(s), space-separated", default="Archives/Test1.csv Archives/Test2.csv")
            self._run_command(f"{sys.executable} SecIDS-CNN/run_model.py file {csv_files}")
        elif choice == "6":
            pcap_file = Prompt.ask("PCAP file path")
            output_csv = Prompt.ask("Output CSV path", default="Results/converted.csv")
            self._run_command(f"{sys.executable} Tools/pcap_to_secids_csv.py -i {pcap_file} -o {output_csv}")
        elif choice == "7":
            input_csv = Prompt.ask("Input dataset path")
            output_csv = Prompt.ask("Output dataset path", default="Results/enhanced_dataset.csv")
            if self.command_lib:
                self._execute_library_shortcut('enhance-dataset', {'input_csv': input_csv, 'output_csv': output_csv})
            else:
                self._run_command(f"{sys.executable} Tools/create_enhanced_dataset.py {input_csv} {output_csv}")
        elif choice == "8":
            self._run_command(f"{sys.executable} Tools/threat_reviewer.py")
        
        Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def training_menu(self):
        """Training submenu with model training options"""
        self.clear_screen()
        
        options = Panel(
            "[bold cyan]Model Training & Testing[/bold cyan]\n\n"
            "[white]1.[/white] Train SecIDS-CNN Model\n"
            "[white]2.[/white] Train Unified Model\n"
            "[white]3.[/white] Train All Models (Pipeline)\n"
            "[white]4.[/white] Test Unified Model\n"
            "[white]5.[/white] Run Smoke Tests\n"
            "[white]6.[/white] Run Full Stress Test Suite\n"
            "[white]7.[/white] Run Performance Stress Test\n"
            "[white]8.[/white] Compare Models\n"
            "[white]9.[/white] View Model Info\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        
        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")
        
        if choice == "1":
            if self.command_lib:
                self._execute_library_shortcut('train-secids')
            else:
                self._run_command(f"{sys.executable} SecIDS-CNN/train_and_test.py")
        elif choice == "2":
            if self.command_lib:
                self._execute_library_shortcut('train-unified')
            else:
                self._run_command(f"{sys.executable} Model_Tester/Code/train_unified_model.py")
        elif choice == "3":
            if self.command_lib:
                self._execute_library_shortcut('pipeline-train')
            else:
                self._run_command(f"{sys.executable} Tools/pipeline_orchestrator.py --mode train")
        elif choice == "4":
            if self.command_lib:
                self._execute_library_shortcut('test-unified')
            else:
                self._run_command(f"{sys.executable} Model_Tester/Code/test_unified_model.py")
        elif choice == "5":
            self._run_command(f"{sys.executable} Scripts/stress_test.py --mode smoke")
        elif choice == "6":
            self._run_command(f"{sys.executable} Scripts/stress_test.py --mode comprehensive")
        elif choice == "7":
            self._run_command(f"{sys.executable} Scripts/stress_test.py --mode performance")
        elif choice == "8":
            self._run_command(f"{sys.executable} Model_Tester/Code/compare_models.py")
        elif choice == "9":
            self._run_command("ls -lh SecIDS-CNN/*.h5 Models/ Model_Tester/models/")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def setup_menu(self):
        """Setup submenu with system configuration"""
        self.clear_screen()
        
        options = Panel(
            "[bold cyan]System Configuration & Setup[/bold cyan]\n\n"
            "[white]1.[/white] Verify System Setup\n"
            "[white]2.[/white] Install Dependencies\n"
            "[white]3.[/white] Check Network Interfaces\n"
            "[white]4.[/white] Create Master Dataset\n"
            "[white]5.[/white] Organize/Cleanup Files\n"
            "[white]6.[/white] Start Task Scheduler\n"
            "[white]7.[/white] Stop Task Scheduler\n"
            "[white]8.[/white] Verify TensorFlow\n"
            "[white]9.[/white] Optimize System\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        
        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")
        
        if choice == "1":
            if self.command_lib:
                self._execute_library_shortcut('verify')
            else:
                self._run_command(f"{sys.executable} Tools/verify_setup.py")
        elif choice == "2":
            self._run_command(".venv_test/bin/pip install -r requirements.txt")
        elif choice == "3":
            self._run_command("ip -br link show")
        elif choice == "4":
            self._run_command(f"{sys.executable} Scripts/create_master_dataset.py")
        elif choice == "5":
            self._run_command(f"{sys.executable} Scripts/organize_files.py")
        elif choice == "6":
            self._run_command(f"{sys.executable} Auto_Update/task_scheduler.py &")
        elif choice == "7":
            self._run_command("pkill -f 'Auto_Update/task_scheduler.py' || true")
        elif choice == "8":
            self._run_command(f"{sys.executable} -c 'import tensorflow as tf; print(f\"TensorFlow: {tf.__version__}\")'")
        elif choice == "9":
            self._run_command(f"{sys.executable} Scripts/optimize_system.py")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def reports_menu(self):
        """Reports submenu with result viewing"""
        self.clear_screen()
        
        options = Panel(
            "[bold cyan]View Reports & Results[/bold cyan]\n\n"
            "[white]1.[/white] View Detection Results\n"
            "[white]2.[/white] View Threat Reports\n"
            "[white]3.[/white] View Stress Test Reports\n"
            "[white]4.[/white] View Latest Markdown Report\n"
            "[white]5.[/white] View System Logs\n"
            "[white]6.[/white] View Scheduler Logs\n"
            "[white]7.[/white] List All Reports\n"
            "[white]8.[/white] Generate New Threat Report\n"
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
            self._run_command("ls -lht Stress_Test_Results/*.json | head -20")
        elif choice == "4":
            self._run_command("cat $(ls -t Results/*report*.md 2>/dev/null | head -1)")
        elif choice == "5":
            self._run_command("ls -lht Logs/ | head -20")
        elif choice == "6":
            self._run_command("ls -lht Auto_Update/logs/ | head -20")
        elif choice == "7":
            self._run_command("ls -lht Reports/ Results/ Stress_Test_Results/ 2>/dev/null | head -50")
        elif choice == "8":
            result_file = Prompt.ask("Detection results CSV path")
            self._run_command(f"{sys.executable} Tools/report_generator.py {result_file}")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def utilities_menu(self):
        """Utilities submenu with tools"""
        self.clear_screen()
        
        options = Panel(
            "[bold cyan]Utilities & Tools[/bold cyan]\n\n"
            "[white]1.[/white] Analyze Threat Origins\n"
            "[white]2.[/white] Threat Reviewer\n"
            "[white]3.[/white] View Whitelist\n"
            "[white]4.[/white] View Blacklist\n"
            "[white]5.[/white] Update Device Lists\n"
            "[white]6.[/white] List Datasets\n"
            "[white]7.[/white] List Models\n"
            "[white]8.[/white] View Archives\n"
            "[white]9.[/white] Launch Passive Countermeasure UI\n"
            "[white]10.[/white] Launch Active Countermeasure UI\n"
            "[white]11.[/white] Clean Temp Files\n"
            "[white]12.[/white] View Command Library\n"
            "[white]0.[/white] Back to Main Menu",
            border_style="cyan"
        )
        self.console.print(options)
        
        choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="0")
        
        if choice == "1":
            if self.command_lib:
                self._execute_library_shortcut('analyze-threats')
            else:
                self._run_command(f"{sys.executable} Scripts/analyze_threat_origins.py")
        elif choice == "2":
            self._run_command(f"{sys.executable} Tools/threat_reviewer.py")
        elif choice == "3":
            self._run_command("cat Device_Profile/whitelists/whitelist_*.json | tail -50")
        elif choice == "4":
            self._run_command("cat Device_Profile/Blacklist/blacklist_*.json | tail -50")
        elif choice == "5":
            self._run_command(f"{sys.executable} Tools/update_lists.py")
        elif choice == "6":
            if self.command_lib:
                self._execute_library_shortcut('list-datasets')
            else:
                self._run_command("ls -lh SecIDS-CNN/datasets/ Archives/")
        elif choice == "7":
            if self.command_lib:
                self._execute_library_shortcut('list-models')
            else:
                self._run_command("ls -lh SecIDS-CNN/*.h5 Models/ Model_Tester/models/")
        elif choice == "8":
            self._run_command("ls -lh Archives/")
        elif choice == "9":
            self._run_command(f"{sys.executable} Countermeasures/passive_ui.py")
        elif choice == "10":
            self._run_command(f"{sys.executable} Countermeasures/active_ui.py")
        elif choice == "11":
            if Confirm.ask("Clean temporary files?"):
                if self.command_lib:
                    self._execute_library_shortcut('clean-temp')
                else:
                    self._run_command("rm -f Captures/capture_temp_*.pcap && rm -f /tmp/secids_*")
        elif choice == "12":
            if self.command_lib:
                self.command_lib.list_commands()
            else:
                self._run_command(f"{sys.executable} Tools/command_library.py list")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def history_menu(self):
        """History submenu with command history"""
        self.clear_screen()

        combined_history = []
        if self.command_lib and self.command_lib.history:
            self.console.print("\n[bold cyan]Command Library History (latest 20):[/bold cyan]\n")
            recent_history = self.command_lib.history[-20:]
            for index, entry in enumerate(recent_history, 1):
                status_icon = "✓" if entry.get('success') else "✗"
                rendered = entry.get('command', '')
                shortcut = entry.get('shortcut', '-')
                timestamp = entry.get('timestamp', 'n/a')
                self.console.print(f"{index:>2}. [{status_icon}] [yellow]{shortcut}[/yellow] @ {timestamp}")
                self.console.print(f"    [dim]{rendered}[/dim]")
                combined_history.append(rendered)
        elif self.config.get('history'):
            self.console.print("\n[bold cyan]UI Command History (latest 20):[/bold cyan]\n")
            recent_history = self.config['history'][-20:]
            for index, entry in enumerate(recent_history, 1):
                rendered = entry.get('command', '')
                timestamp = entry.get('timestamp', 'n/a')
                self.console.print(f"{index:>2}. [yellow]{timestamp}[/yellow]")
                self.console.print(f"    [dim]{rendered}[/dim]")
                combined_history.append(rendered)
        else:
            self.console.print("[yellow]No command history available[/yellow]")

        choice = Prompt.ask(
            "\n[bold yellow]Options[/bold yellow] [white](n=rerun #, r=rerun last, c=clear, f=favorites, a=add favorite, d=remove favorite, Enter=back)[/white]",
            default=""
        ).lower().strip()

        if choice == 'c' and Confirm.ask("Clear history?"):
            if self.command_lib:
                self.command_lib.history = []
                self.command_lib.save_history()
            self.config['history'] = []
            self.save_config()
            self.console.print("[green]✓ History cleared[/green]")
        elif choice == 'r' and combined_history:
            last_command = combined_history[-1]
            self.console.print(f"\n[yellow]Rerunning:[/yellow] {last_command}")
            self._run_command(last_command)
        elif choice == 'n' and combined_history:
            selected = Prompt.ask("History entry number")
            try:
                selected_index = int(selected) - 1
                if 0 <= selected_index < len(combined_history):
                    selected_command = combined_history[selected_index]
                    self.console.print(f"\n[yellow]Rerunning:[/yellow] {selected_command}")
                    self._run_command(selected_command)
                else:
                    self.console.print("[red]Invalid history index[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number[/red]")
        elif choice == 'f':
            if self.command_lib:
                self.command_lib.show_favorites()
            else:
                self.console.print("[yellow]Command library not available[/yellow]")
        elif choice == 'a':
            if self.command_lib:
                shortcut = Prompt.ask("Shortcut to add to favorites").strip()
                if self.command_lib.add_favorite(shortcut):
                    self.console.print(f"[green]✓ Added favorite: {shortcut}[/green]")
                else:
                    self.console.print(f"[red]Could not add favorite: {shortcut}[/red]")
            else:
                self.console.print("[yellow]Command library not available[/yellow]")
        elif choice == 'd':
            if self.command_lib:
                shortcut = Prompt.ask("Shortcut to remove from favorites").strip()
                if self.command_lib.remove_favorite(shortcut):
                    self.console.print(f"[green]✓ Removed favorite: {shortcut}[/green]")
                else:
                    self.console.print(f"[red]Could not remove favorite: {shortcut}[/red]")
            else:
                self.console.print("[yellow]Command library not available[/yellow]")

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
            "[white]5.[/white] Clear Command History\n"
            "[white]6.[/white] Reset to Defaults\n"
            "[white]7.[/white] Save & Apply Settings\n"
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
            if Confirm.ask("Clear command history?"):
                self.config['history'] = []
                if self.command_lib:
                    self.command_lib.history = []
                    self.command_lib.save_history()
                self.console.print("[green]✓ Command history cleared[/green]")
        elif choice == "6":
            self.config.update({
                "last_interface": "eth0",
                "last_duration": 60,
                "last_window": 5,
                "last_interval": 2,
                "theme": "default"
            })
            self.console.print("[green]✓ Settings reset to defaults[/green]")
        elif choice == "7":
            self.save_config()
            self.console.print("[green]✓ Settings saved[/green]")
        
        if choice != "0":
            Prompt.ask("\n[yellow]Press Enter to continue[/yellow]")
    
    def _execute_library_shortcut(self, shortcut: str, params: Optional[Dict] = None):
        """Render and execute a command-library shortcut through the UI runner."""
        if not self.command_lib or shortcut not in self.command_lib.commands:
            self.console.print(f"[red]Command shortcut not available: {shortcut}[/red]")
            return False

        command_info = self.command_lib.commands[shortcut]
        rendered_command = command_info.get('cmd', '')

        if params:
            for key, value in params.items():
                rendered_command = rendered_command.replace(f"{{{key}}}", str(value))

        if '{' in rendered_command and '}' in rendered_command:
            self.console.print(f"[red]Missing required parameters for shortcut: {shortcut}[/red]")
            self.console.print(f"[dim]{rendered_command}[/dim]")
            return False

        if command_info.get('sudo', False) and not rendered_command.strip().startswith('sudo'):
            rendered_command = f"sudo {rendered_command}"

        success = self._run_command(rendered_command)
        if self.command_lib:
            self.command_lib.add_to_history(shortcut, rendered_command, success)

        return success

    def _run_command(self, command: str, save_history: bool = True):
        """Execute a shell command and display output"""
        self.console.print(f"\n[dim]Executing: {command}[/dim]\n")
        
        # Add to history
        if save_history:
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
                return True
            else:
                self.console.print(f"\n[red]✗ Command exited with code {result.returncode}[/red]")
                return False
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            return False
    
    def _execute_with_feedback(self, shortcut: str, params: Optional[Dict] = None):
        """Execute command from library with feedback"""
        if not self.command_lib:
            self.console.print("[red]Command library not available[/red]")
            return
        
        try:
            self.command_lib.execute_command(shortcut, params or {}, dry_run=False)
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

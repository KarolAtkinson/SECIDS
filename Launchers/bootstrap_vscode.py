#!/usr/bin/env python3
"""Bootstrap SecIDS-CNN for VS Code with explicit extension-install consent.

Usage:
  python Launchers/bootstrap_vscode.py
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / ".venv_test"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
VSCODE_DIR = PROJECT_ROOT / ".vscode"
EXTENSIONS_FILE = VSCODE_DIR / "extensions.json"

RECOMMENDED_EXTENSIONS = [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.debugpy",
    "ms-toolsai.jupyter",
    "ms-vscode.powershell",
]


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> int:
    print(f"[run] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd or PROJECT_ROOT))
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")
    return result.returncode


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv() -> None:
    py = venv_python()
    if py.exists():
        print("[ok] Virtual environment already exists: .venv_test")
        return

    print("[setup] Creating virtual environment (.venv_test)...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)])


def install_dependencies() -> None:
    py = venv_python()
    if not REQUIREMENTS.exists():
        raise FileNotFoundError(f"Missing requirements file: {REQUIREMENTS}")

    print("[setup] Upgrading pip and installing dependencies...")
    run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS)])


def write_vscode_recommendations() -> None:
    VSCODE_DIR.mkdir(parents=True, exist_ok=True)
    content_lines = [
        "{",
        '  "recommendations": [',
    ]
    for idx, ext in enumerate(RECOMMENDED_EXTENSIONS):
        suffix = "," if idx < len(RECOMMENDED_EXTENSIONS) - 1 else ""
        content_lines.append(f'    "{ext}"{suffix}')
    content_lines.extend([
        "  ]",
        "}",
        "",
    ])
    EXTENSIONS_FILE.write_text("\n".join(content_lines), encoding="utf-8")
    print(f"[ok] Wrote VS Code recommendations: {EXTENSIONS_FILE}")


def ask_yes_no(prompt: str, default_no: bool = True) -> bool:
    default_hint = "[y/N]" if default_no else "[Y/n]"
    value = input(f"{prompt} {default_hint} ").strip().lower()
    if not value:
        return not default_no
    return value in {"y", "yes"}


def install_extensions_with_consent() -> None:
    if not ask_yes_no("Install recommended VS Code extensions now?", default_no=True):
        print("[skip] Extension installation skipped by user.")
        return

    code_cmd = shutil.which("code")
    if not code_cmd:
        print("[warn] VS Code CLI 'code' was not found in PATH.")
        print("[hint] Open VS Code Command Palette and run: 'Shell Command: Install \"code\" command in PATH'.")
        return

    print("[setup] Installing recommended VS Code extensions...")
    for ext in RECOMMENDED_EXTENSIONS:
        run([code_cmd, "--install-extension", ext], check=False)


def print_next_steps() -> None:
    os_label = platform.system().lower()
    print("\n[done] Bootstrap complete.")
    print("[next] Open the project in VS Code and run WebUI:")
    if os_label == "windows":
        print("       .venv_test\\Scripts\\activate")
        print("       python WebUI\\production_server.py")
    else:
        print("       source .venv_test/bin/activate")
        print("       python3 WebUI/production_server.py")
    print("[next] Open: http://127.0.0.1:8080/login")


def main() -> int:
    try:
        print("[start] SecIDS-CNN VS Code bootstrap")
        ensure_venv()
        install_dependencies()
        write_vscode_recommendations()
        install_extensions_with_consent()
        print_next_steps()
        return 0
    except Exception as exc:
        print(f"[error] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

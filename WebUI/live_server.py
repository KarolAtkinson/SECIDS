#!/usr/bin/env python3
"""Live WebUI runner with Flask auto-reload and optional browser open."""

from __future__ import annotations

import os
import threading
import webbrowser

try:
    from .app import create_app
except ImportError:
    from app import create_app


HOST = os.getenv("SECIDS_WEB_HOST", "127.0.0.1")
PORT = int(os.getenv("SECIDS_WEB_PORT", "8080"))
OPEN_BROWSER = os.getenv("SECIDS_WEB_OPEN_BROWSER", "1") == "1"


def _open_browser_once(url: str) -> None:
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()


def main() -> None:
    app = create_app()
    login_path = app.config.get("SECIDS_LOGIN_PATH", "/login")
    url = f"http://{HOST}:{PORT}{login_path}"
    print(f"[live] starting SecIDS WebUI at {url}")
    if OPEN_BROWSER:
        _open_browser_once(url)
    app.run(host=HOST, port=PORT, debug=True)


if __name__ == "__main__":
    main()

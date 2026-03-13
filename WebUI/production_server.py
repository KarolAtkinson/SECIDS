#!/usr/bin/env python3
"""Production server runner for SecIDS-CNN WebUI."""

from __future__ import annotations

import os

try:
    from waitress import serve  # type: ignore[import-not-found]
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'waitress'. Install requirements and retry: "
        "./.venv_test/bin/pip install -r requirements.txt"
    ) from exc

try:
    from .app import create_app
except ImportError:
    from app import create_app


def main() -> None:
    host = os.getenv("SECIDS_WEB_HOST", "0.0.0.0")
    port = int(os.getenv("SECIDS_WEB_PORT", "8080"))
    threads = int(os.getenv("SECIDS_WEB_THREADS", "8"))

    app = create_app()
    login_path = app.config.get("SECIDS_LOGIN_PATH", "/login")
    print(f"[prod] serving SecIDS WebUI on http://{host}:{port}{login_path}")
    serve(app, host=host, port=port, threads=max(2, threads))


if __name__ == "__main__":
    main()

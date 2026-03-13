#!/usr/bin/env python3
"""WSGI entrypoint for production hosting."""

from __future__ import annotations

try:
	from .app import create_app
except ImportError:
	from app import create_app

app = create_app()

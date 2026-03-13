#!/usr/bin/env python3
"""Compatibility wrapper for legacy UI imports.

Older scripts import `UI.terminal_ui`. The active implementation lives in
`UI.terminal_ui_enhanced`, where the class name is `EnhancedSecIDSUI`.
This module provides the legacy `SecIDSUI` alias.
"""

from .terminal_ui_enhanced import EnhancedSecIDSUI as SecIDSUI

__all__ = ["SecIDSUI"]

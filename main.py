#!/usr/bin/env python3
"""GARUDA - AI-powered Geospatial Intelligence and Monitoring Platform.

Single entry point for the entire application.

Usage:
    python main.py              Start development mode
    python main.py dev          Start development mode
    python main.py prod         Start production mode
    python main.py doctor       Run system diagnostics
    python main.py backend      Run backend only
    python main.py frontend     Run frontend only
    python main.py migrate      Run database migrations
    python main.py status       Show system status
    python main.py version      Show version info
    python main.py help         Show all commands
"""

import sys

from launcher.cli import dispatch

if __name__ == "__main__":
    try:
        sys.exit(dispatch())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)

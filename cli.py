#!/usr/bin/env python3
"""
DebTube CLI - Command-line interface for YouTube Music Player.

Usage:
    python3 cli.py          # Start interactive CLI
    python3 cli.py --help   # Show help
"""

import sys
import os

# Add src directory to path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SRC_DIR, "src"))

from src.cli.cli_app import CLIApp


def main():
    """Main entry point for CLI mode."""
    app = CLIApp()
    app.run()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
DebTube - YouTube Music Player for Debian 12+
Main entry point for the application.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
SRC_DIR = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC_DIR))

# Check for required dependencies
try:
    import PyQt6
    import yt_dlp
    import mpv
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("\nPlease install the required dependencies:")
    print("  pip install -r requirements.txt")
    print("\nOr on Debian:")
    print("  sudo apt install python3-pip mpv")
    print("  pip install PyQt6 yt-dlp python-mpv")
    sys.exit(1)

from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


def main():
    """Main entry point."""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("DebTube")
    app.setOrganizationName("DebTube")
    app.setApplicationVersion("0.1.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

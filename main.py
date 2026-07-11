#!/usr/bin/env python3
"""
DebTube - YouTube Music Player for Debian 12+
Main entry point for the application.

Usage:
    python3 main.py          # Start GUI mode (default)
    python3 main.py --cli    # Start CLI mode
    python3 main.py --help   # Show help
"""

import sys
import os
import argparse

# Add src directory to path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SRC_DIR, "src"))


def can_run_gui():
    """Check if GUI mode is available."""
    # Check if DISPLAY is set (needed for GUI)
    if not os.environ.get('DISPLAY'):
        return False
    
    # Check if PyQt6 is available
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QAction
        # Test creating a QApplication
        app = QApplication([])
        app.quit()
        return True
    except ImportError:
        return False
    except Exception:
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DebTube - YouTube Music Player",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py              Start in GUI mode
  python3 main.py --cli        Start in CLI mode
  python3 main.py --help       Show this help
        """
    )
    
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in command-line mode (no GUI)"
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Run in GUI mode (default)"
    )
    
    args = parser.parse_args()
    
    # Decide which mode to run
    if args.cli:
        # Run CLI mode
        from src.cli.cli_app import CLIApp
        app = CLIApp()
        app.run()
    elif args.gui or can_run_gui():
        # Run GUI mode
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("DebTube")
        app.setOrganizationName("DebTube")
        app.setApplicationVersion("0.1.0")
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    else:
        # Fall back to CLI mode
        print("GUI mode not available (missing dependencies or display)")
        print("Falling back to CLI mode. Use --gui to force GUI mode.")
        from src.cli.cli_app import CLIApp
        app = CLIApp()
        app.run()


if __name__ == "__main__":
    main()

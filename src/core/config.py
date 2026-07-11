"""
Configuration and paths for DebTube.
Handles:
- User data directory
- Cache directory
- Configuration file
- Platform-specific paths
"""

import os
import sys
from pathlib import Path
from typing import Optional


class Config:
    """
    Global configuration for DebTube.
    Manages paths and settings.
    """
    
    # Application name
    APP_NAME = "debtube"
    APP_VERSION = "0.1.0"
    
    # Determine if we're running from a system installation
    @staticmethod
    def is_system_install() -> bool:
        """Check if running from system-wide installation."""
        # Check if we're in /usr/share/debtube or similar
        script_path = Path(__file__).parent.parent.parent
        return script_path.name == "debtube" and "/usr/share" in str(script_path)
    
    @staticmethod
    def get_data_dir() -> Path:
        """
        Get the data directory path.
        Uses XDG_DATA_HOME if set, otherwise ~/.local/share
        """
        # If running from system install, use user's local data dir
        if Config.is_system_install():
            xdg_data_home = os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
            return Path(xdg_data_home) / Config.APP_NAME
        else:
            # Running from source, use local data directory
            return Path(__file__).parent.parent.parent / "data"
    
    @staticmethod
    def get_config_dir() -> Path:
        """
        Get the configuration directory path.
        Uses XDG_CONFIG_HOME if set, otherwise ~/.config
        """
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        return Path(xdg_config_home) / Config.APP_NAME
    
    @staticmethod
    def get_cache_dir() -> Path:
        """
        Get the cache directory path.
        Uses XDG_CACHE_HOME if set, otherwise ~/.cache
        """
        xdg_cache_home = os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
        return Path(xdg_cache_home) / Config.APP_NAME
    
    @staticmethod
    def ensure_directories() -> None:
        """
        Ensure all required directories exist with proper permissions.
        """
        # Create data directory
        data_dir = Config.get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (data_dir / "cache").mkdir(parents=True, exist_ok=True)
        (data_dir / "playlists").mkdir(parents=True, exist_ok=True)
        (data_dir / "history").mkdir(parents=True, exist_ok=True)
        (data_dir / "favorites").mkdir(parents=True, exist_ok=True)
        (data_dir / "thumbnails").mkdir(parents=True, exist_ok=True)
        (data_dir / "images").mkdir(parents=True, exist_ok=True)
        
        # Create config directory
        config_dir = Config.get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create cache directory
        cache_dir = Config.get_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)

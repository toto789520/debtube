"""
Tests for CLI components.
"""

import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.cli.cli_player import CLIPlayer
from src.core.yt_client import VideoInfo


@pytest.fixture
def cli_player():
    """Create a CLIPlayer instance for testing."""
    return CLIPlayer()


def test_cli_player_initialization(cli_player):
    """Test CLIPlayer initialization."""
    from src.core.player import PlayerState
    
    assert cli_player.state == PlayerState.STOPPED
    assert cli_player.volume == 50
    assert cli_player.current_track is None


def test_cli_player_volume(cli_player):
    """Test CLIPlayer volume control."""
    cli_player.volume = 75
    assert cli_player.volume == 75
    
    cli_player.volume = 0
    assert cli_player.volume == 0
    
    cli_player.volume = 100
    assert cli_player.volume == 100
    
    # Test bounds
    cli_player.volume = -10
    assert cli_player.volume == 0
    
    cli_player.volume = 150
    assert cli_player.volume == 100


def test_cli_player_state(cli_player):
    """Test CLIPlayer state."""
    from src.core.player import PlayerState
    
    assert cli_player.state == PlayerState.STOPPED


def test_video_info_for_cli():
    """Test VideoInfo creation for CLI."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    assert video_info.id == "test123"
    assert video_info.title == "Test Video"
    assert video_info.duration == 180


def test_cli_app_initialization():
    """Test CLIApp initialization."""
    from src.cli.cli_app import CLIApp
    
    app = CLIApp()
    
    assert app.yt_client is not None
    assert app.player is not None
    assert app.history_manager is not None
    assert app.favorites_manager is not None
    assert app.playlist_manager is not None


def test_format_duration():
    """Test duration formatting in CLI."""
    from src.cli.cli_app import CLIApp
    
    app = CLIApp()
    
    assert app._format_duration(0) == "0:00"
    assert app._format_duration(45) == "0:45"
    assert app._format_duration(60) == "1:00"
    assert app._format_duration(90) == "1:30"
    assert app._format_duration(3600) == "1:00:00"
    assert app._format_duration(3661) == "1:01:01"
    assert app._format_duration(7325) == "2:02:05"

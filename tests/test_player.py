"""
Tests for the Player class.
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QObject
from src.core.player import Player, PlayerState, RepeatMode, Track
from src.core.yt_client import VideoInfo


@pytest.fixture
def mock_yt_client():
    """Create a mock YouTubeClient for testing."""
    client = MagicMock()
    client.get_audio_stream_url.return_value = "http://example.com/stream.mp3"
    return client


@pytest.fixture
def player(mock_yt_client):
    """Create a Player instance for testing."""
    # We need to run this in a QApplication context
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    
    p = Player(mock_yt_client)
    yield p
    
    # Cleanup
    p.stop()
    app.quit()


def test_player_initialization(player):
    """Test player initialization."""
    assert player.state == PlayerState.STOPPED
    assert player.volume == 50
    assert player.repeat_mode == RepeatMode.NONE
    assert player.shuffle is False
    assert player.playlist == []
    assert player.current_track is None


def test_player_volume(player):
    """Test volume control."""
    player.volume = 75
    assert player.volume == 75
    
    player.volume = 0
    assert player.volume == 0
    
    player.volume = 100
    assert player.volume == 100
    
    # Test bounds
    player.volume = -10
    assert player.volume == 0  # Should clamp to 0
    
    player.volume = 150
    assert player.volume == 100  # Should clamp to 100


def test_player_repeat_mode(player):
    """Test repeat mode."""
    player.repeat_mode = RepeatMode.ONE
    assert player.repeat_mode == RepeatMode.ONE
    
    player.repeat_mode = RepeatMode.ALL
    assert player.repeat_mode == RepeatMode.ALL
    
    player.repeat_mode = RepeatMode.NONE
    assert player.repeat_mode == RepeatMode.NONE


def test_player_shuffle(player):
    """Test shuffle mode."""
    player.shuffle = True
    assert player.shuffle is True
    
    player.shuffle = False
    assert player.shuffle is False


def test_add_to_playlist(player):
    """Test adding tracks to playlist."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    track = Track(video_info=video_info)
    
    player.add_to_playlist(track)
    assert len(player.playlist) == 1
    assert player.playlist[0].id == "test123"


def test_clear_playlist(player):
    """Test clearing playlist."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    track = Track(video_info=video_info)
    
    player.add_to_playlist(track)
    assert len(player.playlist) == 1
    
    player.clear_playlist()
    assert len(player.playlist) == 0


def test_remove_from_playlist(player):
    """Test removing track from playlist."""
    video_info1 = VideoInfo(
        id="test123",
        title="Test Video 1",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb1.jpg",
        url="http://example.com/watch?v=test123"
    )
    video_info2 = VideoInfo(
        id="test456",
        title="Test Video 2",
        channel="Test Channel",
        channel_id="UC123",
        duration=200,
        thumbnail_url="http://example.com/thumb2.jpg",
        url="http://example.com/watch?v=test456"
    )
    
    player.add_to_playlist(Track(video_info=video_info1))
    player.add_to_playlist(Track(video_info=video_info2))
    assert len(player.playlist) == 2
    
    player.remove_from_playlist(0)
    assert len(player.playlist) == 1
    assert player.playlist[0].id == "test456"


def test_set_playlist(player):
    """Test setting a new playlist."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    tracks = [Track(video_info=video_info)]
    player.set_playlist(tracks)
    
    assert len(player.playlist) == 1
    assert player.playlist[0].id == "test123"


def test_player_state_signals(player, qtbot):
    """Test that player emits state change signals."""
    with qtbot.capture_signals(player.state_changed) as signals:
        # Player should start in STOPPED state
        assert len(signals) == 0


def test_track_properties():
    """Test Track dataclass properties."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    track = Track(video_info=video_info, position=0)
    
    assert track.id == "test123"
    assert track.title == "Test Video"
    assert track.duration == 180
    assert track.position == 0

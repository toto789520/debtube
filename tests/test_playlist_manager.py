"""
Tests for the PlaylistManager class.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from src.core.playlist_manager import PlaylistManager, SavedPlaylist
from src.core.yt_client import VideoInfo, PlaylistInfo


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_yt_client():
    """Create a mock YouTubeClient for testing."""
    client = MagicMock()
    
    # Mock video info
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    # Mock playlist info
    playlist_info = PlaylistInfo(
        id="PL123",
        title="Test Playlist",
        channel="Test Channel",
        channel_id="UC123",
        video_count=1,
        thumbnail_url="http://example.com/playlist_thumb.jpg",
        url="http://example.com/playlist?list=PL123",
        videos=[video_info]
    )
    
    client.get_playlist_info.return_value = playlist_info
    client.get_user_playlists.return_value = [playlist_info]
    
    return client


@pytest.fixture
def playlist_manager(mock_yt_client, temp_data_dir, monkeypatch):
    """Create a PlaylistManager instance for testing."""
    # Patch the data directory
    import src.core.playlist_manager as pm_module
    original_dir = pm_module.PLAYLISTS_DIR
    pm_module.PLAYLISTS_DIR = temp_data_dir / "playlists"
    pm_module.PLAYLISTS_DIR.mkdir(parents=True, exist_ok=True)
    
    yield PlaylistManager(mock_yt_client)
    
    # Restore original directory
    pm_module.PLAYLISTS_DIR = original_dir


def test_create_local_playlist(playlist_manager):
    """Test creating a new local playlist."""
    playlist = playlist_manager.create_local_playlist("My Test Playlist")
    
    assert playlist is not None
    assert playlist.title == "My Test Playlist"
    assert playlist.source == "local"
    assert playlist.source_id == "local"
    assert len(playlist.videos) == 0
    assert playlist.id.startswith("local_")


def test_save_and_load_playlist(playlist_manager):
    """Test saving and loading a playlist."""
    # Create a playlist
    playlist = playlist_manager.create_local_playlist("Test Playlist")
    
    # Add a video
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    playlist.add_video(video_info)
    
    # Save the playlist
    assert playlist_manager.save_playlist(playlist)
    
    # Load the playlist
    loaded_playlist = playlist_manager.load_playlist(playlist.id)
    
    assert loaded_playlist is not None
    assert loaded_playlist.title == playlist.title
    assert len(loaded_playlist.videos) == 1
    assert loaded_playlist.videos[0]["id"] == "test123"


def test_list_playlists(playlist_manager):
    """Test listing all saved playlists."""
    # Create some playlists
    playlist1 = playlist_manager.create_local_playlist("Playlist 1")
    playlist2 = playlist_manager.create_local_playlist("Playlist 2")
    
    # Save them
    playlist_manager.save_playlist(playlist1)
    playlist_manager.save_playlist(playlist2)
    
    # List all playlists
    playlists = playlist_manager.list_playlists()
    
    assert len(playlists) == 2
    titles = [p.title for p in playlists]
    assert "Playlist 1" in titles
    assert "Playlist 2" in titles


def test_delete_playlist(playlist_manager):
    """Test deleting a playlist."""
    # Create and save a playlist
    playlist = playlist_manager.create_local_playlist("Playlist to Delete")
    playlist_manager.save_playlist(playlist)
    
    # Verify it exists
    assert playlist_manager.load_playlist(playlist.id) is not None
    
    # Delete it
    assert playlist_manager.delete_playlist(playlist.id)
    
    # Verify it's gone
    assert playlist_manager.load_playlist(playlist.id) is None


def test_import_youtube_playlist(playlist_manager, mock_yt_client):
    """Test importing a YouTube playlist."""
    playlist = playlist_manager.import_youtube_playlist("PL123")
    
    assert playlist is not None
    assert playlist.title == "Test Playlist"
    assert playlist.source == "youtube"
    assert playlist.source_id == "PL123"
    assert len(playlist.videos) == 1


def test_import_user_playlists(playlist_manager, mock_yt_client):
    """Test importing all playlists from a user."""
    playlists = playlist_manager.import_user_playlists("UC123")
    
    assert len(playlists) == 1
    assert playlists[0].title == "Test Playlist"


def test_add_and_remove_video_from_playlist(playlist_manager):
    """Test adding and removing videos from a playlist."""
    playlist = playlist_manager.create_local_playlist("Test Playlist")
    
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    # Add video
    playlist.add_video(video_info)
    assert len(playlist.videos) == 1
    
    # Remove video
    assert playlist.remove_video("test123")
    assert len(playlist.videos) == 0
    
    # Try to remove non-existent video
    assert not playlist.remove_video("nonexistent")


def test_get_video_from_playlist(playlist_manager):
    """Test getting a video from a playlist."""
    playlist = playlist_manager.create_local_playlist("Test Playlist")
    
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    playlist.add_video(video_info)
    
    # Get video
    retrieved_video = playlist.get_video("test123")
    assert retrieved_video is not None
    assert retrieved_video.id == "test123"
    assert retrieved_video.title == "Test Video"
    
    # Get non-existent video
    assert playlist.get_video("nonexistent") is None


def test_saved_playlist_serialization(playlist_manager):
    """Test SavedPlaylist serialization and deserialization."""
    playlist = playlist_manager.create_local_playlist("Test Playlist")
    
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    playlist.add_video(video_info)
    
    # Serialize
    data = playlist.to_dict()
    assert isinstance(data, dict)
    assert "id" in data
    assert "title" in data
    assert "videos" in data
    
    # Deserialize
    restored = SavedPlaylist.from_dict(data)
    assert restored.id == playlist.id
    assert restored.title == playlist.title
    assert len(restored.videos) == 1

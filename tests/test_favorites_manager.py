"""
Tests for the FavoritesManager class.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core.favorites_manager import FavoritesManager, FavoriteEntry
from src.core.yt_client import VideoInfo


@pytest.fixture
def temp_favorites_dir():
    """Create a temporary favorites directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def favorites_manager(temp_favorites_dir, monkeypatch):
    """Create a FavoritesManager instance for testing."""
    # Patch the favorites directory
    import src.core.favorites_manager as fm_module
    original_dir = fm_module.FAVORITES_DIR
    original_file = fm_module.FAVORITES_FILE
    fm_module.FAVORITES_DIR = temp_favorites_dir / "favorites"
    fm_module.FAVORITES_DIR.mkdir(parents=True, exist_ok=True)
    fm_module.FAVORITES_FILE = fm_module.FAVORITES_DIR / "favorites.json"
    
    yield FavoritesManager()
    
    # Restore original paths
    fm_module.FAVORITES_DIR = original_dir
    fm_module.FAVORITES_FILE = original_file


def test_add_favorite(favorites_manager):
    """Test adding a video to favorites."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    assert favorites_manager.add_favorite(video_info, category="Music")
    
    favorites = favorites_manager.get_favorites()
    assert len(favorites) == 1
    assert favorites[0].video_id == "test123"
    assert favorites[0].category == "Music"


def test_add_duplicate_favorite(favorites_manager):
    """Test adding a duplicate favorite."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    # Add first time
    assert favorites_manager.add_favorite(video_info)
    
    # Try to add again
    assert not favorites_manager.add_favorite(video_info)
    
    favorites = favorites_manager.get_favorites()
    assert len(favorites) == 1


def test_remove_favorite(favorites_manager):
    """Test removing a favorite."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    favorites_manager.add_favorite(video_info)
    assert len(favorites_manager.get_favorites()) == 1
    
    assert favorites_manager.remove_favorite("test123")
    assert len(favorites_manager.get_favorites()) == 0
    
    # Try to remove non-existent favorite
    assert not favorites_manager.remove_favorite("nonexistent")


def test_get_favorites_by_category(favorites_manager):
    """Test getting favorites by category."""
    # Add favorites in different categories
    video1 = VideoInfo(
        id="test1",
        title="Video 1",
        channel="Channel 1",
        channel_id="UC1",
        duration=180,
        thumbnail_url="http://example.com/thumb1.jpg",
        url="http://example.com/watch?v=test1"
    )
    video2 = VideoInfo(
        id="test2",
        title="Video 2",
        channel="Channel 2",
        channel_id="UC2",
        duration=200,
        thumbnail_url="http://example.com/thumb2.jpg",
        url="http://example.com/watch?v=test2"
    )
    
    favorites_manager.add_favorite(video1, category="Music")
    favorites_manager.add_favorite(video2, category="Movies")
    
    music_favorites = favorites_manager.get_favorites_by_category("Music")
    assert len(music_favorites) == 1
    assert music_favorites[0].video_id == "test1"
    
    movies_favorites = favorites_manager.get_favorites_by_category("Movies")
    assert len(movies_favorites) == 1
    assert movies_favorites[0].video_id == "test2"


def test_get_categories(favorites_manager):
    """Test getting all categories."""
    video1 = VideoInfo(
        id="test1",
        title="Video 1",
        channel="Channel 1",
        channel_id="UC1",
        duration=180,
        thumbnail_url="http://example.com/thumb1.jpg",
        url="http://example.com/watch?v=test1"
    )
    video2 = VideoInfo(
        id="test2",
        title="Video 2",
        channel="Channel 2",
        channel_id="UC2",
        duration=200,
        thumbnail_url="http://example.com/thumb2.jpg",
        url="http://example.com/watch?v=test2"
    )
    
    favorites_manager.add_favorite(video1, category="Music")
    favorites_manager.add_favorite(video2, category="Movies")
    
    categories = favorites_manager.get_categories()
    assert "Music" in categories
    assert "Movies" in categories


def test_is_favorite(favorites_manager):
    """Test checking if a video is a favorite."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    assert not favorites_manager.is_favorite("test123")
    
    favorites_manager.add_favorite(video_info)
    
    assert favorites_manager.is_favorite("test123")
    assert not favorites_manager.is_favorite("nonexistent")


def test_update_category(favorites_manager):
    """Test updating the category of a favorite."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    favorites_manager.add_favorite(video_info, category="Music")
    
    assert favorites_manager.update_category("test123", "Movies")
    
    entry = favorites_manager.get_favorite("test123")
    assert entry.category == "Movies"
    
    # Try to update non-existent favorite
    assert not favorites_manager.update_category("nonexistent", "Movies")


def test_update_notes(favorites_manager):
    """Test updating notes for a favorite."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    favorites_manager.add_favorite(video_info)
    
    assert favorites_manager.update_notes("test123", "This is a great video!")
    
    entry = favorites_manager.get_favorite("test123")
    assert entry.notes == "This is a great video!"
    
    # Try to update non-existent favorite
    assert not favorites_manager.update_notes("nonexistent", "Notes")


def test_clear_favorites(favorites_manager):
    """Test clearing all favorites."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    favorites_manager.add_favorite(video_info)
    assert len(favorites_manager.get_favorites()) == 1
    
    favorites_manager.clear_favorites()
    assert len(favorites_manager.get_favorites()) == 0


def test_clear_category(favorites_manager):
    """Test clearing a specific category."""
    video1 = VideoInfo(
        id="test1",
        title="Video 1",
        channel="Channel 1",
        channel_id="UC1",
        duration=180,
        thumbnail_url="http://example.com/thumb1.jpg",
        url="http://example.com/watch?v=test1"
    )
    video2 = VideoInfo(
        id="test2",
        title="Video 2",
        channel="Channel 2",
        channel_id="UC2",
        duration=200,
        thumbnail_url="http://example.com/thumb2.jpg",
        url="http://example.com/watch?v=test2"
    )
    
    favorites_manager.add_favorite(video1, category="Music")
    favorites_manager.add_favorite(video2, category="Movies")
    
    assert len(favorites_manager.get_favorites()) == 2
    
    favorites_manager.clear_category("Music")
    
    favorites = favorites_manager.get_favorites()
    assert len(favorites) == 1
    assert favorites[0].category == "Movies"


def test_get_favorite(favorites_manager):
    """Test getting a specific favorite."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    favorites_manager.add_favorite(video_info)
    
    entry = favorites_manager.get_favorite("test123")
    assert entry is not None
    assert entry.video_id == "test123"
    
    # Get non-existent favorite
    assert favorites_manager.get_favorite("nonexistent") is None


def test_favorite_entry_from_video_info():
    """Test creating a FavoriteEntry from VideoInfo."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    entry = FavoriteEntry.from_video_info(video_info, category="Music")
    
    assert entry.video_id == "test123"
    assert entry.title == "Test Video"
    assert entry.channel == "Test Channel"
    assert entry.category == "Music"
    assert entry.added_at is not None


def test_favorite_entry_serialization():
    """Test FavoriteEntry serialization and deserialization."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    entry = FavoriteEntry.from_video_info(video_info, category="Music")
    
    # Serialize
    data = entry.to_dict()
    assert isinstance(data, dict)
    assert "video_id" in data
    assert "title" in data
    assert "category" in data
    
    # Deserialize
    restored = FavoriteEntry.from_dict(data)
    assert restored.video_id == entry.video_id
    assert restored.title == entry.title
    assert restored.category == entry.category

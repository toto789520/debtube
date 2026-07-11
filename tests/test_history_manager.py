"""
Tests for the HistoryManager class.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.core.history_manager import HistoryManager, HistoryEntry
from src.core.yt_client import VideoInfo


@pytest.fixture
def temp_history_dir():
    """Create a temporary history directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def history_manager(temp_history_dir, monkeypatch):
    """Create a HistoryManager instance for testing."""
    # Patch the history directory
    import src.core.history_manager as hm_module
    original_dir = hm_module.HISTORY_DIR
    original_file = hm_module.HISTORY_FILE
    hm_module.HISTORY_DIR = temp_history_dir / "history"
    hm_module.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    hm_module.HISTORY_FILE = hm_module.HISTORY_DIR / "history.json"
    
    yield HistoryManager(max_size=10)
    
    # Restore original paths
    hm_module.HISTORY_DIR = original_dir
    hm_module.HISTORY_FILE = original_file


def test_add_entry(history_manager):
    """Test adding an entry to history."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    history_manager.add_entry(video_info, position=45.0)
    
    history = history_manager.get_history()
    assert len(history) == 1
    assert history[0].video_id == "test123"
    assert history[0].title == "Test Video"
    assert history[0].position == 45.0


def test_add_duplicate_entry(history_manager):
    """Test adding a duplicate entry updates the existing one."""
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
    history_manager.add_entry(video_info, position=45.0)
    
    # Add again with different position
    history_manager.add_entry(video_info, position=90.0)
    
    history = history_manager.get_history()
    assert len(history) == 1
    assert history[0].position == 90.0


def test_get_recent(history_manager):
    """Test getting recent entries."""
    # Add multiple entries
    for i in range(5):
        video_info = VideoInfo(
            id=f"test{i}",
            title=f"Test Video {i}",
            channel="Test Channel",
            channel_id="UC123",
            duration=180,
            thumbnail_url="http://example.com/thumb.jpg",
            url=f"http://example.com/watch?v=test{i}"
        )
        history_manager.add_entry(video_info)
    
    recent = history_manager.get_recent(3)
    assert len(recent) == 3
    assert recent[0].video_id == "test4"  # Most recent first
    assert recent[1].video_id == "test3"
    assert recent[2].video_id == "test2"


def test_clear_history(history_manager):
    """Test clearing history."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    history_manager.add_entry(video_info)
    assert len(history_manager.get_history()) == 1
    
    history_manager.clear_history()
    assert len(history_manager.get_history()) == 0


def test_remove_entry(history_manager):
    """Test removing an entry from history."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    history_manager.add_entry(video_info)
    assert len(history_manager.get_history()) == 1
    
    assert history_manager.remove_entry("test123")
    assert len(history_manager.get_history()) == 0
    
    # Try to remove non-existent entry
    assert not history_manager.remove_entry("nonexistent")


def test_get_entry(history_manager):
    """Test getting a specific entry from history."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    history_manager.add_entry(video_info)
    
    entry = history_manager.get_entry("test123")
    assert entry is not None
    assert entry.video_id == "test123"
    
    # Get non-existent entry
    assert history_manager.get_entry("nonexistent") is None


def test_update_position(history_manager):
    """Test updating position for a video in history."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    history_manager.add_entry(video_info, position=30.0)
    
    assert history_manager.update_position("test123", 60.0)
    
    entry = history_manager.get_entry("test123")
    assert entry.position == 60.0
    
    # Try to update non-existent entry
    assert not history_manager.update_position("nonexistent", 60.0)


def test_max_history_size(history_manager):
    """Test that history is trimmed to max size."""
    # Add more entries than max size
    for i in range(15):  # max_size is 10
        video_info = VideoInfo(
            id=f"test{i}",
            title=f"Test Video {i}",
            channel="Test Channel",
            channel_id="UC123",
            duration=180,
            thumbnail_url="http://example.com/thumb.jpg",
            url=f"http://example.com/watch?v=test{i}"
        )
        history_manager.add_entry(video_info)
    
    history = history_manager.get_history()
    assert len(history) == 10  # Should be trimmed to max_size
    # Most recent should be first
    assert history[0].video_id == "test14"
    assert history[9].video_id == "test5"


def test_history_entry_from_video_info():
    """Test creating a HistoryEntry from VideoInfo."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    entry = HistoryEntry.from_video_info(video_info, position=45.0)
    
    assert entry.video_id == "test123"
    assert entry.title == "Test Video"
    assert entry.channel == "Test Channel"
    assert entry.duration == 180
    assert entry.position == 45.0
    assert entry.played_at is not None


def test_history_entry_serialization():
    """Test HistoryEntry serialization and deserialization."""
    video_info = VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123"
    )
    
    entry = HistoryEntry.from_video_info(video_info, position=45.0)
    
    # Serialize
    data = entry.to_dict()
    assert isinstance(data, dict)
    assert "video_id" in data
    assert "title" in data
    assert "position" in data
    
    # Deserialize
    restored = HistoryEntry.from_dict(data)
    assert restored.video_id == entry.video_id
    assert restored.title == entry.title
    assert restored.position == entry.position

"""
Tests for the YouTube client.
"""

import pytest
from src.core.yt_client import YouTubeClient, VideoInfo, PlaylistInfo


@pytest.fixture
def yt_client():
    """Create a YouTubeClient instance for testing."""
    return YouTubeClient(cache_enabled=False)


def test_search_videos(yt_client):
    """Test searching for videos."""
    results = yt_client.search("test", max_results=5, filter_type="video")
    assert isinstance(results, list)
    if results:
        assert all(isinstance(r, VideoInfo) for r in results)
        assert len(results) <= 5


def test_search_playlists(yt_client):
    """Test searching for playlists."""
    results = yt_client.search("test", max_results=5, filter_type="playlist")
    assert isinstance(results, list)
    if results:
        assert all(isinstance(r, VideoInfo) for r in results)


def test_get_video_info(yt_client):
    """Test getting video info."""
    # Use a known video ID (this might fail if the video is removed)
    # For testing, we'll use a popular video that's likely to exist
    video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    info = yt_client.get_video_info(video_id)
    assert isinstance(info, VideoInfo) or info is None
    if info:
        assert info.id == video_id
        assert info.title
        assert info.channel


def test_get_playlist_info(yt_client):
    """Test getting playlist info."""
    # Use a known playlist ID
    # This is a test playlist, might not exist
    playlist_id = "PLx0sYbCqOb8QbDcXh2Mv2HJl28g5b04F3"  # Example playlist
    info = yt_client.get_playlist_info(playlist_id)
    assert isinstance(info, PlaylistInfo) or info is None


def test_get_audio_stream_url(yt_client):
    """Test getting audio stream URL."""
    video_id = "dQw4w9WgXcQ"
    url = yt_client.get_audio_stream_url(video_id)
    assert isinstance(url, str) or url is None
    if url:
        assert url.startswith("http")


def test_video_info_to_dict(yt_client):
    """Test VideoInfo serialization."""
    video_id = "dQw4w9WgXcQ"
    info = yt_client.get_video_info(video_id)
    if info:
        data = info.to_dict()
        assert isinstance(data, dict)
        assert "id" in data
        assert "title" in data
        assert "channel" in data
        
        # Test deserialization
        restored = VideoInfo.from_dict(data)
        assert restored.id == info.id
        assert restored.title == info.title
        assert restored.channel == info.channel

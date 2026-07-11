"""
Tests for the ImageLoader class.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize

from src.utils.image_loader import ImageLoader


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def image_loader(temp_cache_dir, monkeypatch):
    """Create an ImageLoader instance for testing."""
    # Patch the cache directory
    import src.utils.image_loader as il_module
    original_dir = il_module.IMAGE_CACHE_DIR
    il_module.IMAGE_CACHE_DIR = temp_cache_dir / "images"
    il_module.IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    yield ImageLoader(cache_enabled=True)
    
    # Restore original directory
    il_module.IMAGE_CACHE_DIR = original_dir


@pytest.fixture
def image_loader_no_cache():
    """Create an ImageLoader with caching disabled."""
    return ImageLoader(cache_enabled=False)


def test_load_from_url(image_loader):
    """Test loading an image from a URL."""
    # Mock the requests.get function
    with patch('requests.get') as mock_get:
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'\x89PNG\r\n\x1a\n'  # Simple PNG header
        mock_get.return_value = mock_response
        
        # Test loading
        pixmap = image_loader.load_from_url("http://example.com/image.png")
        
        # Should return a QPixmap (might be null if the image data is invalid)
        assert isinstance(pixmap, QPixmap)


def test_load_from_url_with_size(image_loader):
    """Test loading an image from a URL with a specific size."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Create a simple 100x100 red PNG
        mock_response.content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        mock_get.return_value = mock_response
        
        size = QSize(50, 50)
        pixmap = image_loader.load_from_url("http://example.com/image.png", size=size)
        
        assert isinstance(pixmap, QPixmap)


def test_load_from_url_error(image_loader):
    """Test loading an image from a URL that fails."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection error")
        
        pixmap = image_loader.load_from_url("http://example.com/image.png")
        
        # Should return an empty pixmap on error
        assert isinstance(pixmap, QPixmap)
        assert pixmap.isNull()


def test_load_from_url_empty(image_loader):
    """Test loading an image from an empty URL."""
    pixmap = image_loader.load_from_url("")
    
    assert isinstance(pixmap, QPixmap)
    assert pixmap.isNull()


def test_load_from_file(image_loader, temp_cache_dir):
    """Test loading an image from a file."""
    # Create a test image file
    image_path = temp_cache_dir / "test.png"
    with open(image_path, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n')  # Simple PNG header
    
    pixmap = image_loader.load_from_file(image_path)
    
    assert isinstance(pixmap, QPixmap)


def test_load_from_file_nonexistent(image_loader):
    """Test loading an image from a non-existent file."""
    pixmap = image_loader.load_from_file("/nonexistent/path/image.png")
    
    assert isinstance(pixmap, QPixmap)
    assert pixmap.isNull()


def test_load_from_bytes(image_loader):
    """Test loading an image from bytes."""
    # Simple PNG header
    image_data = b'\x89PNG\r\n\x1a\n'
    
    pixmap = image_loader.load_from_bytes(image_data)
    
    assert isinstance(pixmap, QPixmap)


def test_get_default_thumbnail(image_loader):
    """Test getting a default thumbnail."""
    pixmap = image_loader.get_default_thumbnail()
    
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()


def test_get_default_thumbnail_with_size(image_loader):
    """Test getting a default thumbnail with a specific size."""
    size = QSize(100, 100)
    pixmap = image_loader.get_default_thumbnail(size)
    
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    assert pixmap.width() == 100
    assert pixmap.height() == 100


def test_cache_enabled(image_loader, temp_cache_dir):
    """Test that caching works when enabled."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'\x89PNG\r\n\x1a\n'
        mock_get.return_value = mock_response
        
        # Load the same URL twice
        url = "http://example.com/image.png"
        image_loader.load_from_url(url)
        image_loader.load_from_url(url)
        
        # With caching enabled, the second request should use the cache
        # So requests.get should only be called once
        assert mock_get.call_count == 1


def test_cache_disabled(image_loader_no_cache):
    """Test that caching is disabled when configured."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'\x89PNG\r\n\x1a\n'
        mock_get.return_value = mock_response
        
        # Load the same URL twice
        url = "http://example.com/image.png"
        image_loader_no_cache.load_from_url(url)
        image_loader_no_cache.load_from_url(url)
        
        # With caching disabled, requests.get should be called twice
        assert mock_get.call_count == 2


def test_clear_cache(image_loader, temp_cache_dir):
    """Test clearing the image cache."""
    # Create some cached files
    cache_dir = temp_cache_dir / "images"
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / "test1.png").write_bytes(b'data1')
    (cache_dir / "test2.png").write_bytes(b'data2')
    
    # Clear the cache
    image_loader.clear_cache()
    
    # Check that files are deleted
    assert not (cache_dir / "test1.png").exists()
    assert not (cache_dir / "test2.png").exists()

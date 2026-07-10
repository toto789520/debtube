"""
Image loader for thumbnails and icons.
Handles:
- Downloading thumbnails from URLs
- Caching images locally
- Loading images from files
- Converting to QPixmap for PyQt
"""

import os
import hashlib
from typing import Optional, Union
from pathlib import Path
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QSize, Qt
import requests


# Directory for cached images
IMAGE_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "images"
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ImageLoader:
    """
    Loads and caches images for the application.
    """
    
    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
    
    def _get_cache_path(self, url: str) -> Path:
        """Get the cache path for a URL."""
        if not url:
            return IMAGE_CACHE_DIR / "default.png"
        
        # Create a hash of the URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        ext = self._get_extension(url)
        return IMAGE_CACHE_DIR / f"{url_hash}{ext}"
    
    def _get_extension(self, url: str) -> str:
        """Get the file extension from a URL."""
        if "jpg" in url.lower() or "jpeg" in url.lower():
            return ".jpg"
        elif "png" in url.lower():
            return ".png"
        elif "webp" in url.lower():
            return ".webp"
        return ".png"
    
    def load_from_url(
        self, 
        url: str, 
        size: Optional[QSize] = None,
        default: Optional[QPixmap] = None
    ) -> QPixmap:
        """
        Load an image from a URL.
        
        Args:
            url: URL of the image
            size: Optional size to scale the image to
            default: Default pixmap to return if loading fails
        
        Returns:
            QPixmap with the loaded image
        """
        if not url:
            return default or QPixmap()
        
        # Check cache first
        cache_path = self._get_cache_path(url)
        if self.cache_enabled and cache_path.exists():
            pixmap = self.load_from_file(cache_path, size)
            if not pixmap.isNull():
                return pixmap
        
        # Download the image
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Save to cache
            if self.cache_enabled:
                with open(cache_path, "wb") as f:
                    f.write(response.content)
            
            # Load the image
            image = QImage.fromData(response.content)
            if image.isNull():
                return default or QPixmap()
            
            pixmap = QPixmap.fromImage(image)
            if size:
                pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            return pixmap
            
        except Exception as e:
            print(f"Error loading image from URL {url}: {e}")
            return default or QPixmap()
    
    def load_from_file(
        self, 
        path: Union[str, Path], 
        size: Optional[QSize] = None
    ) -> QPixmap:
        """
        Load an image from a file.
        
        Args:
            path: Path to the image file
            size: Optional size to scale the image to
        
        Returns:
            QPixmap with the loaded image
        """
        path = Path(path)
        if not path.exists():
            return QPixmap()
        
        try:
            image = QImage(str(path))
            if image.isNull():
                return QPixmap()
            
            pixmap = QPixmap.fromImage(image)
            if size:
                pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            return pixmap
        except Exception as e:
            print(f"Error loading image from file {path}: {e}")
            return QPixmap()
    
    def load_from_bytes(
        self, 
        data: bytes, 
        size: Optional[QSize] = None
    ) -> QPixmap:
        """
        Load an image from bytes.
        
        Args:
            data: Image data as bytes
            size: Optional size to scale the image to
        
        Returns:
            QPixmap with the loaded image
        """
        try:
            image = QImage.fromData(data)
            if image.isNull():
                return QPixmap()
            
            pixmap = QPixmap.fromImage(image)
            if size:
                pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            return pixmap
        except Exception as e:
            print(f"Error loading image from bytes: {e}")
            return QPixmap()
    
    def clear_cache(self) -> None:
        """Clear the image cache."""
        if self.cache_enabled:
            for path in IMAGE_CACHE_DIR.glob("*"):
                try:
                    path.unlink()
                except Exception as e:
                    print(f"Error deleting cached image {path}: {e}")
    
    def get_default_thumbnail(self, size: Optional[QSize] = None) -> QPixmap:
        """
        Get a default thumbnail image.
        
        Args:
            size: Optional size for the thumbnail
        
        Returns:
            QPixmap with a default thumbnail
        """
        # Create a simple gray placeholder
        if size:
            pixmap = QPixmap(size)
        else:
            pixmap = QPixmap(100, 100)
        
        pixmap.fill(Qt.GlobalColor.gray)
        return pixmap

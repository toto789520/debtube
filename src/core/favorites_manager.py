"""
Favorites manager for saving favorite videos.
Handles:
- Adding/removing favorite videos
- Loading saved favorites
- Organizing favorites into categories
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field

from .yt_client import VideoInfo


# Directory for favorites data
FAVORITES_DIR = Path(__file__).parent.parent.parent / "data" / "favorites"
FAVORITES_DIR.mkdir(parents=True, exist_ok=True)
FAVORITES_FILE = FAVORITES_DIR / "favorites.json"


@dataclass
class FavoriteEntry:
    """Represents a favorite video entry."""
    video_id: str
    title: str
    channel: str
    channel_id: str
    duration: int
    thumbnail_url: str
    url: str
    added_at: str
    category: str = "General"
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FavoriteEntry":
        return cls(**data)
    
    @classmethod
    def from_video_info(cls, video_info: VideoInfo, category: str = "General") -> "FavoriteEntry":
        """Create a favorite entry from VideoInfo."""
        return cls(
            video_id=video_info.id,
            title=video_info.title,
            channel=video_info.channel,
            channel_id=video_info.channel_id,
            duration=video_info.duration,
            thumbnail_url=video_info.thumbnail_url,
            url=video_info.url,
            added_at=datetime.now().isoformat(),
            category=category
        )


class FavoritesManager:
    """
    Manages favorite videos.
    """
    
    def __init__(self):
        self._favorites: List[FavoriteEntry] = []
        self._load_favorites()
    
    def _load_favorites(self) -> None:
        """Load favorites from file."""
        if not FAVORITES_FILE.exists():
            self._favorites = []
            return
        
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._favorites = [FavoriteEntry.from_dict(entry) for entry in data]
        except (json.JSONDecodeError, IOError):
            self._favorites = []
    
    def _save_favorites(self) -> None:
        """Save favorites to file."""
        try:
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump([entry.to_dict() for entry in self._favorites], f, ensure_ascii=False, indent=2)
        except IOError:
            pass
    
    def add_favorite(self, video_info: VideoInfo, category: str = "General") -> bool:
        """
        Add a video to favorites.
        
        Args:
            video_info: Video information
            category: Category for the favorite
        
        Returns:
            True if added, False if already exists
        """
        # Check if already in favorites
        for entry in self._favorites:
            if entry.video_id == video_info.id:
                return False
        
        # Add new favorite
        new_entry = FavoriteEntry.from_video_info(video_info, category)
        self._favorites.append(new_entry)
        self._save_favorites()
        return True
    
    def remove_favorite(self, video_id: str) -> bool:
        """
        Remove a video from favorites.
        
        Args:
            video_id: ID of the video to remove
        
        Returns:
            True if removed, False otherwise
        """
        for i, entry in enumerate(self._favorites):
            if entry.video_id == video_id:
                self._favorites.pop(i)
                self._save_favorites()
                return True
        return False
    
    def get_favorites(self) -> List[FavoriteEntry]:
        """
        Get all favorites.
        
        Returns:
            List of FavoriteEntry objects
        """
        return self._favorites.copy()
    
    def get_favorites_by_category(self, category: str) -> List[FavoriteEntry]:
        """
        Get favorites in a specific category.
        
        Args:
            category: Category name
        
        Returns:
            List of FavoriteEntry objects in the category
        """
        return [entry for entry in self._favorites if entry.category == category]
    
    def get_categories(self) -> List[str]:
        """
        Get all unique categories.
        
        Returns:
            List of category names
        """
        categories = set(entry.category for entry in self._favorites)
        return sorted(list(categories))
    
    def is_favorite(self, video_id: str) -> bool:
        """
        Check if a video is in favorites.
        
        Args:
            video_id: ID of the video
        
        Returns:
            True if the video is a favorite
        """
        return any(entry.video_id == video_id for entry in self._favorites)
    
    def update_category(self, video_id: str, new_category: str) -> bool:
        """
        Update the category of a favorite video.
        
        Args:
            video_id: ID of the video
            new_category: New category name
        
        Returns:
            True if updated, False otherwise
        """
        for entry in self._favorites:
            if entry.video_id == video_id:
                entry.category = new_category
                self._save_favorites()
                return True
        return False
    
    def update_notes(self, video_id: str, notes: str) -> bool:
        """
        Update the notes for a favorite video.
        
        Args:
            video_id: ID of the video
            notes: New notes
        
        Returns:
            True if updated, False otherwise
        """
        for entry in self._favorites:
            if entry.video_id == video_id:
                entry.notes = notes
                self._save_favorites()
                return True
        return False
    
    def clear_favorites(self) -> None:
        """Clear all favorites."""
        self._favorites = []
        self._save_favorites()
    
    def clear_category(self, category: str) -> None:
        """
        Clear all favorites in a category.
        
        Args:
            category: Category name
        """
        self._favorites = [entry for entry in self._favorites if entry.category != category]
        self._save_favorites()
    
    def get_favorite(self, video_id: str) -> Optional[FavoriteEntry]:
        """
        Get a specific favorite entry.
        
        Args:
            video_id: ID of the video
        
        Returns:
            FavoriteEntry or None if not found
        """
        for entry in self._favorites:
            if entry.video_id == video_id:
                return entry
        return None

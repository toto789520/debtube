"""
History manager for tracking played videos.
Handles:
- Saving recently played videos
- Loading play history
- Managing history size
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from .config import Config
from .yt_client import VideoInfo


# Use config for history directory
HISTORY_DIR = Config.get_data_dir() / "history"
HISTORY_FILE = HISTORY_DIR / "history.json"


@dataclass
class HistoryEntry:
    """Represents an entry in the play history."""
    video_id: str
    title: str
    channel: str
    channel_id: str
    duration: int
    thumbnail_url: str
    url: str
    played_at: str
    position: float = 0.0  # Position where playback stopped
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "HistoryEntry":
        return cls(**data)
    
    @classmethod
    def from_video_info(cls, video_info: VideoInfo, position: float = 0.0) -> "HistoryEntry":
        """Create a history entry from VideoInfo."""
        return cls(
            video_id=video_info.id,
            title=video_info.title,
            channel=video_info.channel,
            channel_id=video_info.channel_id,
            duration=video_info.duration,
            thumbnail_url=video_info.thumbnail_url,
            url=video_info.url,
            played_at=datetime.now().isoformat(),
            position=position
        )


class HistoryManager:
    """
    Manages the play history.
    """
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        # Ensure directories exist
        Config.ensure_directories()
    
    def add_entry(self, video_info: VideoInfo, position: float = 0.0) -> None:
        """
        Add a video to the history.
        
        Args:
            video_info: Video information
            position: Playback position in seconds
        """
        # Load existing history
        history = self._load_history()
        
        # Check if this video is already in history
        for i, entry in enumerate(history):
            if entry.video_id == video_info.id:
                # Update existing entry
                history[i] = HistoryEntry.from_video_info(video_info, position)
                self._save_history(history)
                return
        
        # Add new entry
        new_entry = HistoryEntry.from_video_info(video_info, position)
        history.insert(0, new_entry)
        
        # Trim history to max size
        if len(history) > self.max_size:
            history = history[:self.max_size]
        
        # Save history
        self._save_history(history)
    
    def get_history(self) -> List[HistoryEntry]:
        """
        Get the full play history.
        
        Returns:
            List of HistoryEntry objects
        """
        return self._load_history()
    
    def get_recent(self, count: int = 10) -> List[HistoryEntry]:
        """
        Get the most recent entries from history.
        
        Args:
            count: Number of entries to return
        
        Returns:
            List of HistoryEntry objects
        """
        history = self._load_history()
        return history[:count]
    
    def clear_history(self) -> None:
        """Clear the play history."""
        self._save_history([])
    
    def remove_entry(self, video_id: str) -> bool:
        """
        Remove an entry from history.
        
        Args:
            video_id: ID of the video to remove
        
        Returns:
            True if removed, False otherwise
        """
        history = self._load_history()
        
        for i, entry in enumerate(history):
            if entry.video_id == video_id:
                history.pop(i)
                self._save_history(history)
                return True
        
        return False
    
    def get_entry(self, video_id: str) -> Optional[HistoryEntry]:
        """
        Get a specific entry from history.
        
        Args:
            video_id: ID of the video
        
        Returns:
            HistoryEntry or None if not found
        """
        history = self._load_history()
        
        for entry in history:
            if entry.video_id == video_id:
                return entry
        
        return None
    
    def update_position(self, video_id: str, position: float) -> bool:
        """
        Update the playback position for a video in history.
        
        Args:
            video_id: ID of the video
            position: New playback position
        
        Returns:
            True if updated, False otherwise
        """
        history = self._load_history()
        
        for i, entry in enumerate(history):
            if entry.video_id == video_id:
                history[i].position = position
                history[i].played_at = datetime.now().isoformat()
                self._save_history(history)
                return True
        
        return False
    
    def _load_history(self) -> List[HistoryEntry]:
        """Load history from file."""
        if not HISTORY_FILE.exists():
            return []
        
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [HistoryEntry.from_dict(entry) for entry in data]
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self, history: List[HistoryEntry]) -> None:
        """Save history to file."""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([entry.to_dict() for entry in history], f, ensure_ascii=False, indent=2)
        except IOError:
            pass

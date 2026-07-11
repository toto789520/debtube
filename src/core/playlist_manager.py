"""
Playlist manager for saving and loading playlists.
Handles:
- Saving playlists to JSON files
- Loading saved playlists
- Managing user playlists (from YouTube)
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field

from .yt_client import PlaylistInfo, VideoInfo, YouTubeClient


# Directory for saved playlists
PLAYLISTS_DIR = Path(__file__).parent.parent.parent / "data" / "playlists"
PLAYLISTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SavedPlaylist:
    """Represents a saved playlist."""
    id: str
    title: str
    source: str  # "youtube" or "local"
    source_id: str  # YouTube playlist ID or "local"
    created_at: str
    updated_at: str
    videos: List[Dict] = field(default_factory=list)  # List of VideoInfo as dicts
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SavedPlaylist":
        return cls(**data)
    
    def add_video(self, video: VideoInfo) -> None:
        """Add a video to the playlist."""
        # Check if video already exists
        for v in self.videos:
            if v.get("id") == video.id:
                return
        self.videos.append(video.to_dict())
        self.updated_at = datetime.now().isoformat()
    
    def remove_video(self, video_id: str) -> bool:
        """Remove a video from the playlist."""
        for i, v in enumerate(self.videos):
            if v.get("id") == video_id:
                self.videos.pop(i)
                self.updated_at = datetime.now().isoformat()
                return True
        return False
    
    def get_video(self, video_id: str) -> Optional[VideoInfo]:
        """Get a video from the playlist."""
        for v in self.videos:
            if v.get("id") == video_id:
                return VideoInfo.from_dict(v)
        return None


class PlaylistManager:
    """
    Manages saving and loading of playlists.
    """
    
    def __init__(self, yt_client: YouTubeClient):
        self.yt_client = yt_client
    
    def get_playlist_path(self, playlist_id: str) -> Path:
        """Get the file path for a playlist."""
        return PLAYLISTS_DIR / f"{playlist_id}.json"
    
    def save_playlist(self, playlist: SavedPlaylist) -> bool:
        """
        Save a playlist to a file.
        
        Args:
            playlist: Playlist to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            path = self.get_playlist_path(playlist.id)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(playlist.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving playlist: {e}")
            return False
    
    def load_playlist(self, playlist_id: str) -> Optional[SavedPlaylist]:
        """
        Load a playlist from a file.
        
        Args:
            playlist_id: ID of the playlist to load
        
        Returns:
            SavedPlaylist object or None if not found
        """
        path = self.get_playlist_path(playlist_id)
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SavedPlaylist.from_dict(data)
        except Exception as e:
            print(f"Error loading playlist: {e}")
            return None
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a saved playlist.
        
        Args:
            playlist_id: ID of the playlist to delete
        
        Returns:
            True if successful, False otherwise
        """
        path = self.get_playlist_path(playlist_id)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                print(f"Error deleting playlist: {e}")
                return False
        return False
    
    def list_playlists(self) -> List[SavedPlaylist]:
        """
        List all saved playlists.
        
        Returns:
            List of SavedPlaylist objects
        """
        playlists = []
        for path in PLAYLISTS_DIR.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                playlist = SavedPlaylist.from_dict(data)
                playlists.append(playlist)
            except Exception as e:
                print(f"Error loading playlist {path.name}: {e}")
        return playlists
    
    def import_youtube_playlist(self, playlist_id: str) -> Optional[SavedPlaylist]:
        """
        Import a YouTube playlist and save it locally.
        
        Args:
            playlist_id: YouTube playlist ID
        
        Returns:
            SavedPlaylist object or None if failed
        """
        # Get playlist info from YouTube
        yt_playlist = self.yt_client.get_playlist_info(playlist_id)
        if not yt_playlist:
            return None
        
        # Create a saved playlist
        saved_playlist = SavedPlaylist(
            id=f"yt_{playlist_id}",
            title=yt_playlist.title,
            source="youtube",
            source_id=playlist_id,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            videos=[v.to_dict() for v in yt_playlist.videos]
        )
        
        # Save the playlist
        if self.save_playlist(saved_playlist):
            return saved_playlist
        return None
    
    def import_user_playlists(self, channel_id: str) -> List[SavedPlaylist]:
        """
        Import all public playlists from a YouTube user/channel.
        
        Args:
            channel_id: YouTube channel ID or username
        
        Returns:
            List of SavedPlaylist objects that were imported
        """
        # Get user playlists from YouTube
        yt_playlists = self.yt_client.get_user_playlists(channel_id)
        imported = []
        
        for yt_playlist in yt_playlists:
            # Import each playlist
            saved_playlist = self.import_youtube_playlist(yt_playlist.id)
            if saved_playlist:
                imported.append(saved_playlist)
        
        return imported
    
    def update_youtube_playlist(self, saved_playlist: SavedPlaylist) -> bool:
        """
        Update a saved YouTube playlist with the latest videos from YouTube.
        
        Args:
            saved_playlist: Playlist to update
        
        Returns:
            True if successful, False otherwise
        """
        if saved_playlist.source != "youtube":
            return False
        
        # Get latest playlist info from YouTube
        yt_playlist = self.yt_client.get_playlist_info(saved_playlist.source_id)
        if not yt_playlist:
            return False
        
        # Update the saved playlist
        saved_playlist.title = yt_playlist.title
        saved_playlist.videos = [v.to_dict() for v in yt_playlist.videos]
        saved_playlist.updated_at = datetime.now().isoformat()
        
        # Save the updated playlist
        return self.save_playlist(saved_playlist)
    
    def create_local_playlist(self, title: str) -> SavedPlaylist:
        """
        Create a new empty local playlist.
        
        Args:
            title: Title of the playlist
        
        Returns:
            New SavedPlaylist object
        """
        import uuid
        playlist_id = f"local_{uuid.uuid4().hex[:8]}"
        
        playlist = SavedPlaylist(
            id=playlist_id,
            title=title,
            source="local",
            source_id="local",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            videos=[]
        )
        
        self.save_playlist(playlist)
        return playlist

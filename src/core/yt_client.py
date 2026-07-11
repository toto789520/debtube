"""
YouTube/YouTube Music Client using yt-dlp.
Handles:
- Searching for videos/music
- Fetching public playlists from a user/channel
- Extracting metadata (title, thumbnail, duration, subtitles, etc.)
- Getting direct audio streams for playback
"""

import yt_dlp
import os
import json
from typing import List, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import timedelta

from .config import Config

# Use config for data directory
DATA_DIR = Config.get_data_dir()


@dataclass
class VideoInfo:
    """Metadata for a YouTube video."""
    id: str
    title: str
    channel: str
    channel_id: str
    duration: int  # in seconds
    thumbnail_url: str
    url: str
    is_live: bool = False
    view_count: int = 0
    upload_date: str = ""
    description: str = ""
    subtitles: List[Dict] = None  # List of subtitle tracks
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "VideoInfo":
        return cls(**data)


@dataclass 
class PlaylistInfo:
    """Metadata for a YouTube playlist."""
    id: str
    title: str
    channel: str
    channel_id: str
    video_count: int
    thumbnail_url: str
    url: str
    videos: List[VideoInfo] = None
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "videos": [v.to_dict() for v in (self.videos or [])]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlaylistInfo":
        playlist = cls(
            id=data["id"],
            title=data["title"],
            channel=data["channel"],
            channel_id=data["channel_id"],
            video_count=data["video_count"],
            thumbnail_url=data["thumbnail_url"],
            url=data["url"],
            videos=[]
        )
        if "videos" in data:
            playlist.videos = [VideoInfo.from_dict(v) for v in data["videos"]]
        return playlist


class YouTubeClient:
    """
    Client for interacting with YouTube and YouTube Music.
    Uses yt-dlp for scraping and extracting data.
    """
    
    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self.cache_dir = DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Common yt-dlp options
        self.base_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
        }
    
    def _get_cache_path(self, key: str) -> Path:
        """Get path for a cache file."""
        return self.cache_dir / f"{key}.json"
    
    def _read_cache(self, key: str) -> Optional[Dict]:
        """Read from cache if available."""
        if not self.cache_enabled:
            return None
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def _write_cache(self, key: str, data: Dict) -> None:
        """Write to cache."""
        if not self.cache_enabled:
            return
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
    
    def search(
        self, 
        query: str, 
        max_results: int = 20,
        filter_type: str = "video",
        yt_music: bool = False
    ) -> List[VideoInfo]:
        """
        Search for videos or music on YouTube.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            filter_type: "video", "playlist", or "all"
            yt_music: If True, search on YouTube Music (uses different URL)
        
        Returns:
            List of VideoInfo objects
        """
        cache_key = f"search_{hash(query)}_{max_results}_{filter_type}_{yt_music}"
        cached = self._read_cache(cache_key)
        if cached:
            return [VideoInfo.from_dict(v) for v in cached]
        
        # Build search URL
        if yt_music:
            search_url = f'ytmsearch{max_results}:"{query}"'
        else:
            search_url = f'ytsearch{max_results}:"{query}"'
        
        # Configure yt-dlp options
        ydl_opts = {
            **self.base_opts,
            "extract_flat": True,
            "playlists_items": "50" if filter_type == "all" else None,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(search_url, download=False)
                
            videos = []
            if "entries" in results:
                for entry in results["entries"]:
                    if entry is None:
                        continue
                    
                    # Skip playlists if we only want videos
                    if filter_type == "video" and entry.get("_type") == "playlist":
                        continue
                    
                    # Skip videos if we only want playlists
                    if filter_type == "playlist" and entry.get("_type") != "playlist":
                        continue
                    
                    video_info = self._parse_entry(entry)
                    if video_info:
                        videos.append(video_info)
            
            # Cache results
            cache_data = [v.to_dict() for v in videos]
            self._write_cache(cache_key, cache_data)
            
            return videos
            
        except yt_dlp.utils.DownloadError as e:
            print(f"Search error: {e}")
            return []
    
    def get_video_info(self, video_id: str) -> Optional[VideoInfo]:
        """
        Get detailed information about a specific video.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            VideoInfo object or None if not found
        """
        cache_key = f"video_{video_id}"
        cached = self._read_cache(cache_key)
        if cached:
            return VideoInfo.from_dict(cached)
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            **self.base_opts,
            "extract_flat": True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            video_info = self._parse_entry(info)
            if video_info:
                # Cache the result
                self._write_cache(cache_key, video_info.to_dict())
            return video_info
            
        except yt_dlp.utils.DownloadError as e:
            print(f"Error getting video info: {e}")
            return None
    
    def get_playlist_info(self, playlist_id: str) -> Optional[PlaylistInfo]:
        """
        Get information about a playlist and its videos.
        
        Args:
            playlist_id: YouTube playlist ID
        
        Returns:
            PlaylistInfo object or None if not found
        """
        cache_key = f"playlist_{playlist_id}"
        cached = self._read_cache(cache_key)
        if cached:
            return PlaylistInfo.from_dict(cached)
        
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        ydl_opts = {
            **self.base_opts,
            "extract_flat": False,
            "playlist_items": "100",  # Max items to fetch
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            if not info:
                return None
            
            # Parse playlist info
            playlist_info = PlaylistInfo(
                id=info.get("id", playlist_id),
                title=info.get("title", "Unknown Playlist"),
                channel=info.get("uploader", "Unknown"),
                channel_id=info.get("uploader_id", ""),
                video_count=info.get("playlist_count", 0),
                thumbnail_url=info.get("thumbnail", ""),
                url=url,
                videos=[]
            )
            
            # Parse videos in playlist
            if "entries" in info:
                for entry in info["entries"]:
                    if entry:
                        video_info = self._parse_entry(entry)
                        if video_info:
                            playlist_info.videos.append(video_info)
            
            # Cache the result
            self._write_cache(cache_key, playlist_info.to_dict())
            return playlist_info
            
        except yt_dlp.utils.DownloadError as e:
            print(f"Error getting playlist info: {e}")
            return None
    
    def get_user_playlists(self, channel_id: str, max_playlists: int = 50) -> List[PlaylistInfo]:
        """
        Get all public playlists from a user/channel.
        
        Args:
            channel_id: YouTube channel ID or username
            max_playlists: Maximum number of playlists to return
        
        Returns:
            List of PlaylistInfo objects
        """
        cache_key = f"user_playlists_{channel_id}_{max_playlists}"
        cached = self._read_cache(cache_key)
        if cached:
            return [PlaylistInfo.from_dict(p) for p in cached]
        
        # First, get the channel URL
        channel_url = f"https://www.youtube.com/@{channel_id}/playlists"
        if not channel_id.startswith("UC"):
            # Try to resolve username to channel ID
            try:
                with yt_dlp.YoutubeDL(self.base_opts) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/@{channel_id}", download=False)
                    channel_id = info.get("channel_id", channel_id)
                    channel_url = f"https://www.youtube.com/channel/{channel_id}/playlists"
            except Exception:
                pass
        
        ydl_opts = {
            **self.base_opts,
            "extract_flat": True,
            "playlist_items": "1",  # Only get playlist metadata, not videos
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
            playlists = []
            if "entries" in info:
                for entry in info["entries"][:max_playlists]:
                    if entry and entry.get("_type") == "playlist":
                        playlist_info = PlaylistInfo(
                            id=entry.get("id", ""),
                            title=entry.get("title", "Unknown Playlist"),
                            channel=entry.get("uploader", "Unknown"),
                            channel_id=entry.get("uploader_id", ""),
                            video_count=entry.get("playlist_count", 0),
                            thumbnail_url=entry.get("thumbnail", ""),
                            url=entry.get("url", ""),
                            videos=[]  # Don't fetch videos yet
                        )
                        playlists.append(playlist_info)
            
            # Cache results
            cache_data = [p.to_dict() for p in playlists]
            self._write_cache(cache_key, cache_data)
            
            return playlists
            
        except yt_dlp.utils.DownloadError as e:
            print(f"Error getting user playlists: {e}")
            return []
    
    def get_audio_stream_url(self, video_id: str, format: str = "best") -> Optional[str]:
        """
        Get a direct audio stream URL for a video.
        
        Args:
            video_id: YouTube video ID
            format: "best" (default), "opus", "mp3", or "m4a"
        
        Returns:
            Direct audio stream URL or None
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Map format to yt-dlp format selector
        format_selectors = {
            "best": "ba",
            "opus": "ba[ext=opus]",
            "mp3": "ba[ext=mp3]",
            "m4a": "ba[ext=m4a]",
        }
        format_selector = format_selectors.get(format, "ba")
        
        ydl_opts = {
            **self.base_opts,
            "format": format_selector,
            "get_url": True,
            "get_title": False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get("url")
        except yt_dlp.utils.DownloadError as e:
            print(f"Error getting audio stream: {e}")
            return None
    
    def download_thumbnail(
        self, 
        video_id: str, 
        output_path: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Download the thumbnail for a video.
        
        Args:
            video_id: YouTube video ID
            output_path: Optional output path (defaults to data/thumbnails/{id}.jpg)
        
        Returns:
            Path to the downloaded thumbnail or None
        """
        if output_path is None:
            output_path = DATA_DIR / "thumbnails" / f"{video_id}.jpg"
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            **self.base_opts,
            "skip_download": False,
            "outtmpl": str(output_path),
            "format": "best[ext=jpg]/best[ext=webp]",
            "writethumbnail": True,
            "noplaylist": True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                return output_path if output_path.exists() else None
        except Exception as e:
            print(f"Error downloading thumbnail: {e}")
            return None
    
    def _parse_entry(self, entry: Dict) -> Optional[VideoInfo]:
        """
        Parse a yt-dlp entry into a VideoInfo object.
        
        Args:
            entry: Dictionary from yt-dlp
        
        Returns:
            VideoInfo object or None if invalid
        """
        if not entry or entry.get("_type") == "url":
            return None
        
        # Handle playlist entries (they have nested video info)
        if entry.get("_type") == "playlist":
            return None
        
        # Get the actual video info
        if "entries" in entry and entry["_type"] == "playlist":
            # This is a playlist, skip
            return None
        
        # For playlist videos, the entry might have the video info directly
        video_data = entry
        
        # Extract duration
        duration = 0
        if "duration" in video_data:
            try:
                duration = video_data["duration"]
            except (KeyError, TypeError):
                pass
        
        # Extract subtitles
        subtitles = []
        if "subtitles" in video_data:
            subtitles = video_data["subtitles"]
        elif "automatic_captions" in video_data:
            subtitles = video_data["automatic_captions"]
        
        try:
            video_info = VideoInfo(
                id=video_data.get("id", ""),
                title=video_data.get("title", "Unknown"),
                channel=video_data.get("uploader", "Unknown"),
                channel_id=video_data.get("uploader_id", ""),
                duration=duration,
                thumbnail_url=video_data.get("thumbnail", ""),
                url=video_data.get("url", f"https://www.youtube.com/watch?v={video_data.get('id', '')}"),
                is_live=video_data.get("is_live", False),
                view_count=video_data.get("view_count", 0),
                upload_date=video_data.get("upload_date", ""),
                description=video_data.get("description", ""),
                subtitles=subtitles
            )
            return video_info
        except Exception as e:
            print(f"Error parsing video entry: {e}")
            return None

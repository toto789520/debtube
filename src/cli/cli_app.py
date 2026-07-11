"""
CLI Application for DebTube.
Provides a command-line interface for searching and playing YouTube music.
"""

import sys
import time
from typing import Optional, List
from pathlib import Path

from ..core.yt_client import YouTubeClient, VideoInfo
from ..core.playlist_manager import PlaylistManager
from ..core.history_manager import HistoryManager
from ..core.favorites_manager import FavoritesManager
from .cli_player import CLIPlayer


class CLIApp:
    """
    Command-line interface for DebTube.
    """
    
    def __init__(self):
        self.yt_client = YouTubeClient()
        self.playlist_manager = PlaylistManager(self.yt_client)
        self.history_manager = HistoryManager()
        self.favorites_manager = FavoritesManager()
        self.player = CLIPlayer()
        
        self._running = True
    
    def run(self):
        """Run the CLI application."""
        print("=" * 60)
        print("DebTube CLI - YouTube Music Player")
        print("=" * 60)
        print()
        print("Commands:")
        print("  search <query>     - Search for videos")
        print("  play <id>         - Play a video by ID")
        print("  playlist <id>    - Import and play a playlist")
        print("  user <channel>   - Import user playlists")
        print("  history          - Show play history")
        print("  favorites        - Show favorites")
        print("  volume <0-100>   - Set volume")
        print("  pause            - Pause playback")
        print("  stop             - Stop playback")
        print("  help             - Show this help")
        print("  quit             - Exit")
        print()
        
        while self._running:
            try:
                cmd = input("debtube> ").strip()
                if not cmd:
                    continue
                
                self._process_command(cmd)
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except EOFError:
                print()
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _process_command(self, cmd: str):
        """Process a command."""
        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:]
        
        if command == "quit" or command == "exit":
            self._running = False
            self.player.stop()
            print("Goodbye!")
        
        elif command == "help":
            self._show_help()
        
        elif command == "search":
            if not args:
                print("Usage: search <query>")
                return
            self._search(" ".join(args))
        
        elif command == "play":
            if not args:
                print("Usage: play <video_id>")
                return
            self._play(args[0])
        
        elif command == "playlist":
            if not args:
                print("Usage: playlist <playlist_id>")
                return
            self._import_playlist(args[0])
        
        elif command == "user":
            if not args:
                print("Usage: user <channel_id>")
                return
            self._import_user_playlists(args[0])
        
        elif command == "history":
            self._show_history()
        
        elif command == "favorites":
            self._show_favorites()
        
        elif command == "volume":
            if not args:
                print(f"Current volume: {self.player.volume}")
                return
            try:
                volume = int(args[0])
                if 0 <= volume <= 100:
                    self.player.volume = volume
                    print(f"Volume set to {volume}")
                else:
                    print("Volume must be between 0 and 100")
            except ValueError:
                print("Volume must be a number")
        
        elif command == "pause":
            self.player.pause()
            if self.player.state == PlayerState.PAUSED:
                print("Paused")
            else:
                print("Resumed")
        
        elif command == "stop":
            self.player.stop()
            print("Stopped")
        
        elif command == "nowplaying":
            if self.player.current_track:
                print(f"Now playing: {self.player.current_track.title} - {self.player.current_track.channel}")
            else:
                print("No track playing")
        
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")
    
    def _search(self, query: str):
        """Search for videos."""
        print(f"\nSearching for: {query}")
        results = self.yt_client.search(query, max_results=10)
        
        if not results:
            print("No results found")
            return
        
        print(f"\nFound {len(results)} results:")
        for i, video in enumerate(results, 1):
            print(f"  {i}. {video.title} - {video.channel} ({self._format_duration(video.duration)})")
            print(f"     ID: {video.id}")
        
        print("\nEnter a number to play, or 0 to cancel:")
        try:
            choice = input("  > ").strip()
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(results):
                    self._play(results[idx-1].id)
                elif idx == 0:
                    return
                else:
                    print("Invalid selection")
        except Exception:
            pass
    
    def _play(self, video_id: str):
        """Play a video by ID."""
        print(f"\nGetting video info for: {video_id}")
        video_info = self.yt_client.get_video_info(video_id)
        
        if not video_info:
            print(f"Video {video_id} not found")
            return
        
        print(f"Playing: {video_info.title} - {video_info.channel}")
        
        # Get audio URL
        audio_url = self.yt_client.get_audio_stream_url(video_id)
        if not audio_url:
            print("Could not get audio stream")
            return
        
        # Add to history
        self.history_manager.add_entry(video_info)
        
        # Play
        self.player.play(video_info, audio_url)
        
        # Wait for playback to finish
        while self.player.state != PlayerState.STOPPED:
            time.sleep(0.5)
        
        print(f"Finished playing: {video_info.title}")
    
    def _import_playlist(self, playlist_id: str):
        """Import and play a playlist."""
        print(f"\nImporting playlist: {playlist_id}")
        playlist = self.playlist_manager.import_youtube_playlist(playlist_id)
        
        if not playlist:
            print(f"Playlist {playlist_id} not found")
            return
        
        print(f"\nPlaylist: {playlist.title} ({len(playlist.videos)} videos)")
        
        # Play all videos in the playlist
        for i, video in enumerate(playlist.videos, 1):
            print(f"\n[{i}/{len(playlist.videos)}] {video.title}")
            audio_url = self.yt_client.get_audio_stream_url(video.id)
            if audio_url:
                self.player.play(video, audio_url)
                while self.player.state != PlayerState.STOPPED:
                    time.sleep(0.5)
    
    def _import_user_playlists(self, channel_id: str):
        """Import all playlists from a user."""
        print(f"\nImporting playlists from: {channel_id}")
        playlists = self.playlist_manager.import_user_playlists(channel_id)
        
        if not playlists:
            print(f"No playlists found for {channel_id}")
            return
        
        print(f"\nFound {len(playlists)} playlists:")
        for i, playlist in enumerate(playlists, 1):
            print(f"  {i}. {playlist.title} ({playlist.video_count} videos)")
            print(f"     ID: {playlist.id}")
        
        print("\nEnter a number to play, or 0 to cancel:")
        try:
            choice = input("  > ").strip()
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(playlists):
                    self._import_playlist(playlists[idx-1].id)
                elif idx == 0:
                    return
                else:
                    print("Invalid selection")
        except Exception:
            pass
    
    def _show_history(self):
        """Show play history."""
        history = self.history_manager.get_recent(20)
        
        if not history:
            print("No history")
            return
        
        print(f"\nRecent history ({len(history)} entries):")
        for i, entry in enumerate(history, 1):
            print(f"  {i}. {entry.title} - {entry.channel} ({self._format_duration(entry.duration)})")
            print(f"     Played: {entry.played_at}")
    
    def _show_favorites(self):
        """Show favorites."""
        favorites = self.favorites_manager.get_favorites()
        
        if not favorites:
            print("No favorites")
            return
        
        print(f"\nFavorites ({len(favorites)} entries):")
        for i, entry in enumerate(favorites, 1):
            print(f"  {i}. {entry.title} - {entry.channel} ({self._format_duration(entry.duration)})")
            print(f"     Category: {entry.category}")
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS."""
        if seconds <= 0:
            return "0:00"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def _show_help(self):
        """Show help."""
        print("\nAvailable commands:")
        print("  search <query>     - Search for videos on YouTube")
        print("  play <id>         - Play a video by its YouTube ID")
        print("  playlist <id>    - Import and play a YouTube playlist")
        print("  user <channel>   - Import and list all playlists from a channel")
        print("  history          - Show recent play history")
        print("  favorites        - Show favorite videos")
        print("  volume <0-100>   - Set playback volume (0-100)")
        print("  pause            - Pause/resume playback")
        print("  stop             - Stop playback")
        print("  nowplaying       - Show currently playing track")
        print("  help             - Show this help message")
        print("  quit             - Exit the application")
        print()

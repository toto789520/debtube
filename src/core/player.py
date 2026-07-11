"""
Audio player using MPV for YouTube stream playback.
Handles:
- Playing audio streams from YouTube
- Play/Pause/Stop/Next/Previous controls
- Volume control
- Progress tracking
- Playlist management
"""

import subprocess
import threading
import time
from typing import List, Optional, Callable
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from dataclasses import dataclass, field
from enum import Enum, auto

from .yt_client import VideoInfo, YouTubeClient


class PlayerState(Enum):
    """Player states."""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    BUFFERING = auto()
    ERROR = auto()


class RepeatMode(Enum):
    """Repeat modes."""
    NONE = auto()
    ONE = auto()  # Repeat current track
    ALL = auto()  # Repeat all tracks


@dataclass
class Track:
    """Represents a track in the playlist."""
    video_info: VideoInfo
    audio_url: Optional[str] = None
    position: int = 0  # Position in the playlist
    
    @property
    def id(self) -> str:
        return self.video_info.id
    
    @property
    def title(self) -> str:
        return self.video_info.title
    
    @property
    def duration(self) -> int:
        return self.video_info.duration


class Player(QObject):
    """
    MPV-based audio player for YouTube streams.
    Runs in a separate thread to avoid blocking the GUI.
    """
    
    # Signals
    state_changed = pyqtSignal(PlayerState)
    track_changed = pyqtSignal(Track)
    position_changed = pyqtSignal(float)  # Position in seconds
    duration_changed = pyqtSignal(float)  # Duration in seconds
    volume_changed = pyqtSignal(int)  # Volume percentage (0-100)
    playlist_changed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, yt_client: YouTubeClient):
        super().__init__()
        self.yt_client = yt_client
        self._state = PlayerState.STOPPED
        self._volume = 50
        self._repeat_mode = RepeatMode.NONE
        self._shuffle = False
        
        # Playlist
        self._playlist: List[Track] = []
        self._current_index = -1
        
        # MPV process
        self._mpv_process: Optional[subprocess.Popen] = None
        self._mpv_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Progress tracking
        self._current_position = 0.0
        self._current_duration = 0.0
        self._progress_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._on_track_end: Optional[Callable] = None
    
    @property
    def state(self) -> PlayerState:
        return self._state
    
    @property
    def volume(self) -> int:
        return self._volume
    
    @volume.setter
    def volume(self, value: int):
        if 0 <= value <= 100:
            self._volume = value
            self._update_mpv_volume()
            self.volume_changed.emit(value)
    
    @property
    def repeat_mode(self) -> RepeatMode:
        return self._repeat_mode
    
    @repeat_mode.setter
    def repeat_mode(self, mode: RepeatMode):
        self._repeat_mode = mode
    
    @property
    def shuffle(self) -> bool:
        return self._shuffle
    
    @shuffle.setter
    def shuffle(self, enabled: bool):
        self._shuffle = enabled
    
    @property
    def playlist(self) -> List[Track]:
        return self._playlist.copy()
    
    @property
    def current_track(self) -> Optional[Track]:
        if 0 <= self._current_index < len(self._playlist):
            return self._playlist[self._current_index]
        return None
    
    @property
    def current_position(self) -> float:
        return self._current_position
    
    @property
    def current_duration(self) -> float:
        return self._current_duration
    
    def play(self, track: Optional[Track] = None):
        """
        Play a specific track or resume current track.
        
        Args:
            track: Track to play (if None, resumes current track)
        """
        if track is not None:
            # Find the track in the playlist
            try:
                index = next(i for i, t in enumerate(self._playlist) if t.id == track.id)
                self._current_index = index
                self.track_changed.emit(track)
            except StopIteration:
                # Track not in playlist, add it
                self._playlist.append(track)
                self._current_index = len(self._playlist) - 1
                self.track_changed.emit(track)
                self.playlist_changed.emit(self._playlist)
        
        if self._current_index < 0 or self._current_index >= len(self._playlist):
            self.error_occurred.emit("No track selected")
            return
        
        track = self._playlist[self._current_index]
        
        # Stop current playback
        self.stop()
        
        # Get audio URL if not already set
        if not track.audio_url:
            audio_url = self.yt_client.get_audio_stream_url(track.id)
            if not audio_url:
                self.error_occurred.emit(f"Could not get audio stream for {track.title}")
                return
            track.audio_url = audio_url
        
        # Start playback in a new thread
        self._stop_event.clear()
        self._state = PlayerState.BUFFERING
        self.state_changed.emit(self._state)
        
        self._mpv_thread = threading.Thread(
            target=self._play_track,
            args=(track,),
            daemon=True
        )
        self._mpv_thread.start()
        
        # Start progress tracking
        self._start_progress_tracking()
    
    def pause(self):
        """Pause or resume playback."""
        if self._state == PlayerState.PLAYING:
            self._pause_mpv()
            self._state = PlayerState.PAUSED
            self.state_changed.emit(self._state)
        elif self._state == PlayerState.PAUSED:
            self._resume_mpv()
            self._state = PlayerState.PLAYING
            self.state_changed.emit(self._state)
    
    def stop(self):
        """Stop playback."""
        self._stop_event.set()
        if self._mpv_process:
            self._terminate_mpv()
        if self._mpv_thread:
            self._mpv_thread.join(timeout=1)
        if self._progress_thread:
            self._stop_event.set()
            self._progress_thread.join(timeout=1)
        
        self._state = PlayerState.STOPPED
        self._current_position = 0.0
        self._current_duration = 0.0
        self.state_changed.emit(self._state)
        self.position_changed.emit(0.0)
    
    def next(self):
        """Play the next track in the playlist."""
        if not self._playlist:
            return
        
        if self._repeat_mode == RepeatMode.ONE:
            # Repeat current track
            self.play()
            return
        
        if self._shuffle:
            # Random track
            import random
            new_index = random.randint(0, len(self._playlist) - 1)
        else:
            # Next track
            if self._repeat_mode == RepeatMode.ALL and self._current_index == len(self._playlist) - 1:
                new_index = 0
            else:
                new_index = self._current_index + 1
        
        if new_index < len(self._playlist):
            self._current_index = new_index
            self.play()
        else:
            # End of playlist
            self.stop()
    
    def previous(self):
        """Play the previous track in the playlist."""
        if not self._playlist:
            return
        
        if self._shuffle:
            import random
            new_index = random.randint(0, len(self._playlist) - 1)
        else:
            if self._current_index <= 0:
                if self._repeat_mode == RepeatMode.ALL:
                    new_index = len(self._playlist) - 1
                else:
                    new_index = 0
            else:
                new_index = self._current_index - 1
        
        if 0 <= new_index < len(self._playlist):
            self._current_index = new_index
            self.play()
    
    def add_to_playlist(self, track: Track):
        """Add a track to the playlist."""
        self._playlist.append(track)
        self.playlist_changed.emit(self._playlist)
    
    def add_to_playlist_and_play(self, track: Track):
        """Add a track to the playlist and play it immediately."""
        self._playlist.append(track)
        self._current_index = len(self._playlist) - 1
        self.playlist_changed.emit(self._playlist)
        self.play(track)
    
    def clear_playlist(self):
        """Clear the playlist."""
        self.stop()
        self._playlist.clear()
        self._current_index = -1
        self.playlist_changed.emit(self._playlist)
    
    def remove_from_playlist(self, index: int):
        """Remove a track from the playlist."""
        if 0 <= index < len(self._playlist):
            if index == self._current_index:
                self.stop()
                self._current_index = -1
            elif index < self._current_index:
                self._current_index -= 1
            
            self._playlist.pop(index)
            self.playlist_changed.emit(self._playlist)
    
    def seek(self, position: float):
        """
        Seek to a specific position in the current track.
        
        Args:
            position: Position in seconds
        """
        if self._mpv_process and self._state == PlayerState.PLAYING:
            try:
                # MPV uses seconds for seeking
                self._mpv_process.stdin.write(f"seek {position} absolute\n")
                self._mpv_process.stdin.flush()
                self._current_position = position
                self.position_changed.emit(position)
            except Exception as e:
                print(f"Error seeking: {e}")
    
    def set_playlist(self, tracks: List[Track]):
        """Replace the current playlist."""
        self.stop()
        self._playlist = tracks.copy()
        self._current_index = -1
        self.playlist_changed.emit(self._playlist)
    
    def _play_track(self, track: Track):
        """Internal method to play a track using MPV."""
        if self._stop_event.is_set():
            return
        
        try:
            # Build MPV command
            cmd = [
                "mpv",
                "--no-video",
                "--audio-only",
                "--volume=" + str(self._volume),
                "--no-osc",
                "--no-input-default-bindings",
                "--input-ipc-server=/tmp/mpv-socket",
                "--idle",
                "--no-terminal",
                "--really-quiet",
                track.audio_url
            ]
            
            # Start MPV
            self._mpv_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for MPV to start
            time.sleep(0.5)
            
            if self._stop_event.is_set():
                self._terminate_mpv()
                return
            
            # Update state
            self._state = PlayerState.PLAYING
            self._current_duration = track.duration
            self.duration_changed.emit(track.duration)
            self.state_changed.emit(self._state)
            
            # Wait for playback to finish
            while self._mpv_process.poll() is None:
                if self._stop_event.is_set():
                    self._terminate_mpv()
                    return
                time.sleep(0.1)
            
            # Track ended
            if not self._stop_event.is_set():
                # Auto-play next track
                self.next()
                
        except Exception as e:
            self._state = PlayerState.ERROR
            self.state_changed.emit(self._state)
            self.error_occurred.emit(str(e))
        finally:
            if not self._stop_event.is_set():
                self._state = PlayerState.STOPPED
                self.state_changed.emit(self._state)
    
    def _pause_mpv(self):
        """Send pause command to MPV."""
        if self._mpv_process:
            try:
                self._mpv_process.stdin.write("cycle pause\n")
                self._mpv_process.stdin.flush()
            except Exception as e:
                print(f"Error pausing: {e}")
    
    def _resume_mpv(self):
        """Send resume command to MPV."""
        self._pause_mpv()  # cycle pause toggles play/pause
    
    def _update_mpv_volume(self):
        """Update MPV volume."""
        if self._mpv_process:
            try:
                self._mpv_process.stdin.write(f"set volume {self._volume}\n")
                self._mpv_process.stdin.flush()
            except Exception as e:
                print(f"Error setting volume: {e}")
    
    def _terminate_mpv(self):
        """Terminate MPV process."""
        if self._mpv_process:
            try:
                self._mpv_process.terminate()
                self._mpv_process.wait(timeout=1)
            except Exception as e:
                print(f"Error terminating MPV: {e}")
            finally:
                self._mpv_process = None
    
    def _start_progress_tracking(self):
        """Start a thread to track playback progress."""
        if self._progress_thread:
            self._stop_event.set()
            self._progress_thread.join(timeout=1)
        
        self._stop_event.clear()
        self._progress_thread = threading.Thread(
            target=self._track_progress,
            daemon=True
        )
        self._progress_thread.start()
    
    def _track_progress(self):
        """Track playback progress using MPV's IPC."""
        import socket
        import json
        
        try:
            # Connect to MPV's IPC socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect("/tmp/mpv-socket")
            
            # Send command to get property updates
            sock.sendall(b'{"command":["observe_property",2,"time-pos"]}\n')
            sock.sendall(b'{"command":["observe_property",3,"duration"]}\n')
            
            while not self._stop_event.is_set():
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    
                    # Parse JSON messages
                    for line in data.decode().split("\n"):
                        if not line.strip():
                            continue
                        
                        try:
                            msg = json.loads(line)
                            if "event" in msg and msg["event"] == "property-change":
                                prop_name = msg.get("name")
                                prop_value = msg.get("data")
                                
                                if prop_name == "time-pos" and prop_value is not None:
                                    self._current_position = float(prop_value)
                                    self.position_changed.emit(self._current_position)
                                elif prop_name == "duration" and prop_value is not None:
                                    self._current_duration = float(prop_value)
                                    self.duration_changed.emit(self._current_duration)
                        except json.JSONDecodeError:
                            continue
                            
                except Exception as e:
                    print(f"Progress tracking error: {e}")
                    break
                    
        except Exception as e:
            print(f"Could not connect to MPV socket: {e}")
        finally:
            try:
                sock.close()
            except:
                pass

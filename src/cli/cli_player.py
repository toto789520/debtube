"""
CLI Player for DebTube.
Handles audio playback in command-line mode using MPV.
"""

import subprocess
import threading
import time
from typing import Optional, List
from pathlib import Path

from ..core.yt_client import VideoInfo
from ..core.player import PlayerState, RepeatMode


class CLIPlayer:
    """
    Simple CLI player using MPV for audio playback.
    """
    
    def __init__(self):
        self._state = PlayerState.STOPPED
        self._volume = 50
        self._current_track: Optional[VideoInfo] = None
        self._mpv_process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
    
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
    
    @property
    def current_track(self) -> Optional[VideoInfo]:
        return self._current_track
    
    def play(self, video_info: VideoInfo, audio_url: str):
        """Play a video."""
        self._current_track = video_info
        self._stop_event.clear()
        
        # Stop current playback
        self.stop()
        
        # Start MPV
        cmd = [
            "mpv",
            "--no-video",
            "--audio-only",
            f"--volume={self._volume}",
            "--no-osc",
            "--no-input-default-bindings",
            "--idle",
            "--no-terminal",
            "--really-quiet",
            audio_url
        ]
        
        try:
            self._mpv_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self._state = PlayerState.PLAYING
            
            # Wait for playback to finish
            while self._mpv_process.poll() is None:
                if self._stop_event.is_set():
                    self._terminate_mpv()
                    return
                time.sleep(0.1)
            
        except Exception as e:
            print(f"Error playing: {e}")
        finally:
            if not self._stop_event.is_set():
                self._state = PlayerState.STOPPED
    
    def pause(self):
        """Pause playback."""
        if self._mpv_process and self._state == PlayerState.PLAYING:
            try:
                self._mpv_process.stdin.write(b"cycle pause\n")
                self._mpv_process.stdin.flush()
                self._state = PlayerState.PAUSED
            except Exception as e:
                print(f"Error pausing: {e}")
    
    def stop(self):
        """Stop playback."""
        self._stop_event.set()
        if self._mpv_process:
            self._terminate_mpv()
        self._state = PlayerState.STOPPED
        self._current_track = None
    
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

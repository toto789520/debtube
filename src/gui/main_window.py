"""
Main application window for DebTube.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QSizePolicy, QStatusBar, QMenuBar, QMenu, QAction
)
from PyQt6.QtGui import QIcon, QAction, QKeySequence
from PyQt6.QtCore import Qt, QSize

from ..core.yt_client import YouTubeClient, VideoInfo
from ..core.player import Player, Track
from ..core.playlist_manager import PlaylistManager
from .search_widget import SearchWidget
from .playlist_widget import PlaylistWidget
from .player_widget import PlayerWidget
from ..utils.image_loader import ImageLoader


class MainWindow(QMainWindow):
    """
    Main application window.
    Contains:
    - Menu bar
    - Search widget
    - Player widget
    - Playlist widget
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.yt_client = YouTubeClient()
        self.image_loader = ImageLoader()
        self.playlist_manager = PlaylistManager(self.yt_client)
        self.player = Player(self.yt_client)
        
        # Initialize UI components
        self.search_widget = SearchWidget(self.yt_client, self.image_loader)
        self.playlist_widget = PlaylistWidget(self.playlist_manager, self.image_loader)
        self.player_widget = PlayerWidget(self.player)
        
        self._setup_ui()
        self._setup_connections()
        self._setup_menu()
        
        # Set window properties
        self.setWindowTitle("DebTube - YouTube Music Player")
        self.setMinimumSize(800, 600)
        self.resize(1024, 768)
        
        # Create a default playlist
        self.current_playlist = self.playlist_manager.create_local_playlist("My Playlist")
        self.playlist_widget.set_playlist(self.current_playlist)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Central widget
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #1e1e1e;")
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter for search and playlist
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("background-color: #1e1e1e;")
        
        # Left panel - Search
        self.splitter.addWidget(self.search_widget)
        
        # Right panel - Playlist
        self.splitter.addWidget(self.playlist_widget)
        
        # Set initial sizes
        self.splitter.setSizes([600, 400])
        
        # Add splitter to layout
        main_layout.addWidget(self.splitter, stretch=1)
        
        # Player widget at the bottom
        main_layout.addWidget(self.player_widget)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("color: #aaaaaa;")
        self.setStatusBar(self.status_bar)
        
        # Set dark theme
        self._set_dark_theme()
    
    def _setup_connections(self):
        """Set up signal connections between widgets."""
        # Search widget connections
        self.search_widget.video_selected.connect(self._on_video_selected)
        self.search_widget.video_double_clicked.connect(self._on_video_double_clicked)
        self.search_widget.playlist_selected.connect(self._on_playlist_selected)
        
        # Playlist widget connections
        self.playlist_widget.video_selected.connect(self._on_video_selected)
        self.playlist_widget.video_double_clicked.connect(self._on_video_double_clicked)
        self.playlist_widget.playlist_selected.connect(self._on_playlist_loaded)
        
        # Player widget connections
        self.player_widget.play_clicked.connect(self._on_play_clicked)
        self.player_widget.pause_clicked.connect(self._on_pause_clicked)
        self.player_widget.stop_clicked.connect(self._on_stop_clicked)
        self.player_widget.next_clicked.connect(self._on_next_clicked)
        self.player_widget.previous_clicked.connect(self._on_previous_clicked)
        self.player_widget.volume_changed.connect(self._on_volume_changed)
        self.player_widget.seek_requested.connect(self._on_seek)
        
        # Player state connections
        self.player.state_changed.connect(self._on_player_state_changed)
        self.player.track_changed.connect(self._on_track_changed)
        self.player.error_occurred.connect(self._on_player_error)
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menu_bar = QMenuBar()
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #222222;
                color: #ffffff;
                padding: 4px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #4CAF50;
            }
            QMenu {
                background-color: #222222;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 4px 24px 4px 8px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
        """)
        
        # File menu
        file_menu = QMenu("File", menu_bar)
        
        # New playlist action
        new_playlist_action = QAction("New Playlist", file_menu)
        new_playlist_action.setShortcut(QKeySequence("Ctrl+N"))
        new_playlist_action.triggered.connect(self._on_new_playlist)
        file_menu.addAction(new_playlist_action)
        
        # Load playlist action
        load_playlist_action = QAction("Load Playlist", file_menu)
        load_playlist_action.setShortcut(QKeySequence("Ctrl+O"))
        load_playlist_action.triggered.connect(self._on_load_playlist)
        file_menu.addAction(load_playlist_action)
        
        # Save playlist action
        save_playlist_action = QAction("Save Playlist", file_menu)
        save_playlist_action.setShortcut(QKeySequence("Ctrl+S"))
        save_playlist_action.triggered.connect(self._on_save_playlist)
        file_menu.addAction(save_playlist_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", file_menu)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Playlist menu
        playlist_menu = QMenu("Playlist", menu_bar)
        
        # Import YouTube playlist action
        import_playlist_action = QAction("Import YouTube Playlist", playlist_menu)
        import_playlist_action.triggered.connect(self._on_import_youtube_playlist)
        playlist_menu.addAction(import_playlist_action)
        
        # Import user playlists action
        import_user_action = QAction("Import User Playlists", playlist_menu)
        import_user_action.triggered.connect(self._on_import_user_playlists)
        playlist_menu.addAction(import_user_action)
        
        # Update current playlist action
        update_playlist_action = QAction("Update Current Playlist", playlist_menu)
        update_playlist_action.triggered.connect(self._on_update_playlist)
        playlist_menu.addAction(update_playlist_action)
        
        # Help menu
        help_menu = QMenu("Help", menu_bar)
        
        # About action
        about_action = QAction("About", help_menu)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
        # Add menus to menu bar
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(playlist_menu)
        menu_bar.addMenu(help_menu)
        
        self.setMenuBar(menu_bar)
    
    def _set_dark_theme(self):
        """Set a dark theme for the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QSplitter::handle {
                background-color: #333333;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #444444;
            }
            QToolTip {
                background-color: #222222;
                color: #ffffff;
                border: 1px solid #333333;
            }
        """)
    
    def _on_video_selected(self, video_info: VideoInfo):
        """Handle video selection (add to playlist)."""
        # Create a track from the video info
        track = Track(video_info=video_info)
        
        # Add to playlist
        self.playlist_widget.add_video(video_info)
        
        # Add to player playlist
        self.player.add_to_playlist(track)
        
        self.status_bar.showMessage(f"Added '{video_info.title}' to playlist", 2000)
    
    def _on_video_double_clicked(self, video_info: VideoInfo):
        """Handle video double-click (play immediately)."""
        # Create a track from the video info
        track = Track(video_info=video_info)
        
        # Add to playlist and play
        self.player.add_to_playlist_and_play(track)
        
        # Also add to the playlist widget
        self.playlist_widget.add_video(video_info)
        
        self.status_bar.showMessage(f"Playing '{video_info.title}'", 2000)
    
    def _on_playlist_selected(self, playlist_id: str):
        """Handle playlist selection from search."""
        # Import the YouTube playlist
        playlist = self.playlist_manager.import_youtube_playlist(playlist_id)
        if playlist:
            self.playlist_widget.set_playlist(playlist)
            self.current_playlist = playlist
            self.status_bar.showMessage(f"Imported playlist: {playlist.title}", 2000)
    
    def _on_playlist_loaded(self, playlist_id: str):
        """Handle playlist loaded from playlist widget."""
        playlist = self.playlist_manager.load_playlist(playlist_id)
        if playlist:
            self.current_playlist = playlist
            
            # Add all videos to player playlist
            for video_dict in playlist.videos:
                video_info = VideoInfo.from_dict(video_dict)
                track = Track(video_info=video_info)
                self.player.add_to_playlist(track)
            
            self.status_bar.showMessage(f"Loaded playlist: {playlist.title}", 2000)
    
    def _on_play_clicked(self):
        """Handle play button click."""
        if self.player.current_track:
            self.player.play()
        elif self.player.playlist:
            # Play the first track
            self.player.play(self.player.playlist[0])
        else:
            self.status_bar.showMessage("No tracks in playlist", 2000)
    
    def _on_pause_clicked(self):
        """Handle pause button click."""
        self.player.pause()
    
    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.player.stop()
    
    def _on_next_clicked(self):
        """Handle next button click."""
        self.player.next()
    
    def _on_previous_clicked(self):
        """Handle previous button click."""
        self.player.previous()
    
    def _on_volume_changed(self, volume: int):
        """Handle volume change."""
        self.player.volume = volume
    
    def _on_seek(self, position: float):
        """Handle seek request."""
        self.player.seek(position)
    
    def _on_player_state_changed(self, state):
        """Handle player state change."""
        from ..core.player import PlayerState
        
        if state == PlayerState.PLAYING:
            track = self.player.current_track
            if track:
                self.status_bar.showMessage(f"Playing: {track.title}", 2000)
        elif state == PlayerState.PAUSED:
            self.status_bar.showMessage("Paused", 2000)
        elif state == PlayerState.STOPPED:
            self.status_bar.showMessage("Stopped", 2000)
        elif state == PlayerState.ERROR:
            self.status_bar.showMessage("Error occurred", 2000)
    
    def _on_track_changed(self, track: Track):
        """Handle track change."""
        if track:
            self.status_bar.showMessage(f"Now playing: {track.title}", 2000)
    
    def _on_player_error(self, error: str):
        """Handle player error."""
        self.status_bar.showMessage(f"Error: {error}", 5000)
    
    def _on_new_playlist(self):
        """Handle new playlist action."""
        from PyQt6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(
            self, 
            "New Playlist", 
            "Enter playlist name:"
        )
        
        if ok and text:
            playlist = self.playlist_manager.create_local_playlist(text)
            self.playlist_widget.set_playlist(playlist)
            self.current_playlist = playlist
            self.status_bar.showMessage(f"Created new playlist: {text}", 2000)
    
    def _on_load_playlist(self):
        """Handle load playlist action."""
        # This is handled by the playlist widget
        pass
    
    def _on_save_playlist(self):
        """Handle save playlist action."""
        if self.current_playlist:
            if self.playlist_manager.save_playlist(self.current_playlist):
                self.status_bar.showMessage(
                    f"Saved playlist: {self.current_playlist.title}", 
                    2000
                )
    
    def _on_import_youtube_playlist(self):
        """Handle import YouTube playlist action."""
        from PyQt6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(
            self,
            "Import YouTube Playlist",
            "Enter YouTube playlist ID or URL:"
        )
        
        if ok and text:
            # Extract playlist ID from URL if needed
            playlist_id = text
            if "youtube.com" in text or "youtu.be" in text:
                # Try to extract ID from URL
                import re
                match = re.search(r"(?:list=|playlist\?|/playlist/)([a-zA-Z0-9_-]+)", text)
                if match:
                    playlist_id = match.group(1)
            
            # Import the playlist
            playlist = self.playlist_manager.import_youtube_playlist(playlist_id)
            if playlist:
                self.playlist_widget.set_playlist(playlist)
                self.current_playlist = playlist
                self.status_bar.showMessage(
                    f"Imported playlist: {playlist.title}",
                    2000
                )
            else:
                self.status_bar.showMessage(
                    f"Failed to import playlist: {playlist_id}",
                    2000
                )
    
    def _on_import_user_playlists(self):
        """Handle import user playlists action."""
        from PyQt6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(
            self,
            "Import User Playlists",
            "Enter YouTube channel ID or username:"
        )
        
        if ok and text:
            # Import all playlists from the user
            playlists = self.playlist_manager.import_user_playlists(text)
            if playlists:
                # Set the first playlist
                self.playlist_widget.set_playlist(playlists[0])
                self.current_playlist = playlists[0]
                self.status_bar.showMessage(
                    f"Imported {len(playlists)} playlists from {text}",
                    2000
                )
            else:
                self.status_bar.showMessage(
                    f"No playlists found for: {text}",
                    2000
                )
    
    def _on_update_playlist(self):
        """Handle update current playlist action."""
        if self.current_playlist and self.current_playlist.source == "youtube":
            if self.playlist_manager.update_youtube_playlist(self.current_playlist):
                self.playlist_widget.set_playlist(self.current_playlist)
                self.status_bar.showMessage(
                    f"Updated playlist: {self.current_playlist.title}",
                    2000
                )
            else:
                self.status_bar.showMessage(
                    "Failed to update playlist",
                    2000
                )
    
    def _on_about(self):
        """Handle about action."""
        from PyQt6.QtWidgets import QMessageBox
        
        about_text = """
        <h2>DebTube - YouTube Music Player</h2>
        <p>Version 0.1.0</p>
        <p>A simple YouTube music player for Debian 12+</p>
        <p>Uses yt-dlp for YouTube access and MPV for playback</p>
        <p>&copy; 2024 DebTube Team</p>
        """
        
        QMessageBox.about(self, "About DebTube", about_text)
    
    def closeEvent(self, event):
        """Handle close event."""
        # Stop the player
        self.player.stop()
        
        # Save current playlist
        if self.current_playlist:
            self.playlist_manager.save_playlist(self.current_playlist)
        
        event.accept()

"""
Main application window for DebTube.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QSizePolicy, QStatusBar, QMenuBar, QMenu, QAction, QTabWidget,
    QDockWidget, QStackedWidget
)
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal

from ..core.yt_client import YouTubeClient, VideoInfo
from ..core.player import Player, Track, PlayerState
from ..core.playlist_manager import PlaylistManager
from ..core.history_manager import HistoryManager
from ..core.favorites_manager import FavoritesManager
from .search_widget import SearchWidget
from .playlist_widget import PlaylistWidget
from .player_widget import PlayerWidget
from .video_item import VideoItemWidget
from .floating_video_window import FloatingVideoWindow
from .history_widget import HistoryWidget
from .favorites_widget import FavoritesWidget
from ..utils.image_loader import ImageLoader


class MainWindow(QMainWindow):
    """
    Main application window.
    Contains:
    - Menu bar
    - Search widget
    - Player widget
    - Playlist widget
    - History widget
    - Favorites widget
    - Floating video window (optional)
    """
    
    # Signals
    video_played = pyqtSignal(VideoInfo, float)
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.yt_client = YouTubeClient()
        self.image_loader = ImageLoader()
        self.playlist_manager = PlaylistManager(self.yt_client)
        self.history_manager = HistoryManager()
        self.favorites_manager = FavoritesManager()
        self.player = Player(self.yt_client)
        
        # Initialize UI components
        self.search_widget = SearchWidget(self.yt_client, self.image_loader)
        self.playlist_widget = PlaylistWidget(self.playlist_manager, self.image_loader)
        self.player_widget = PlayerWidget(self.player)
        self.history_widget = HistoryWidget(self.history_manager, self.image_loader)
        self.favorites_widget = FavoritesWidget(self.favorites_manager, self.image_loader)
        
        # Floating video window
        self.floating_window: Optional[FloatingVideoWindow] = None
        self._is_fullscreen = False
        self._is_mini_mode = False
        
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
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background-color: #1e1e1e;
                border: none;
            }
            QTabBar::tab {
                background-color: #222222;
                color: #aaaaaa;
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid #1e1e1e;
            }
            QTabBar::tab:selected {
                background-color: #282828;
                color: #ffffff;
                border-bottom: 2px solid #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #282828;
                color: #ffffff;
            }
        """)
        
        # Search tab
        self.search_tab = QWidget()
        search_layout = QVBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        search_layout.addWidget(self.search_widget)
        self.search_tab.setLayout(search_layout)
        
        # Playlist tab
        self.playlist_tab = QWidget()
        playlist_layout = QVBoxLayout()
        playlist_layout.setContentsMargins(0, 0, 0, 0)
        playlist_layout.setSpacing(0)
        playlist_layout.addWidget(self.playlist_widget)
        self.playlist_tab.setLayout(playlist_layout)
        
        # History tab
        self.history_tab = QWidget()
        history_layout = QVBoxLayout()
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(0)
        history_layout.addWidget(self.history_widget)
        self.history_tab.setLayout(history_layout)
        
        # Favorites tab
        self.favorites_tab = QWidget()
        favorites_layout = QVBoxLayout()
        favorites_layout.setContentsMargins(0, 0, 0, 0)
        favorites_layout.setSpacing(0)
        favorites_layout.addWidget(self.favorites_widget)
        self.favorites_tab.setLayout(favorites_layout)
        
        # Add tabs
        self.tab_widget.addTab(self.search_tab, "🔍 Search")
        self.tab_widget.addTab(self.playlist_tab, "📝 Playlist")
        self.tab_widget.addTab(self.history_tab, "🕒 History")
        self.tab_widget.addTab(self.favorites_tab, "⭐ Favorites")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget, stretch=1)
        
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
        self.player_widget.fullscreen_requested.connect(self._on_fullscreen_requested)
        
        # Player state connections
        self.player.state_changed.connect(self._on_player_state_changed)
        self.player.track_changed.connect(self._on_track_changed)
        self.player.position_changed.connect(self._on_position_changed)
        self.player.error_occurred.connect(self._on_player_error)
        
        # History widget connections
        self.history_widget.video_selected.connect(self._on_video_selected)
        self.history_widget.video_double_clicked.connect(self._on_video_double_clicked)
        
        # Favorites widget connections
        self.favorites_widget.video_selected.connect(self._on_video_selected)
        self.favorites_widget.video_double_clicked.connect(self._on_video_double_clicked)
        
        # Connect video played signal to history
        self.video_played.connect(self._on_video_played)
    
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
        
        # View menu
        view_menu = QMenu("View", menu_bar)
        
        # Fullscreen action
        fullscreen_action = QAction("Fullscreen", view_menu)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Mini mode action
        mini_mode_action = QAction("Mini Mode", view_menu)
        mini_mode_action.setShortcut(QKeySequence("Ctrl+M"))
        mini_mode_action.triggered.connect(self._toggle_mini_mode)
        view_menu.addAction(mini_mode_action)
        
        # Floating video action
        floating_video_action = QAction("Floating Video", view_menu)
        floating_video_action.setShortcut(QKeySequence("Ctrl+F"))
        floating_video_action.triggered.connect(self._toggle_floating_video)
        view_menu.addAction(floating_video_action)
        
        # Separator
        view_menu.addSeparator()
        
        # Switch to Search tab
        search_tab_action = QAction("Search", view_menu)
        search_tab_action.setShortcut(QKeySequence("Ctrl+1"))
        search_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(search_tab_action)
        
        # Switch to Playlist tab
        playlist_tab_action = QAction("Playlist", view_menu)
        playlist_tab_action.setShortcut(QKeySequence("Ctrl+2"))
        playlist_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(playlist_tab_action)
        
        # Switch to History tab
        history_tab_action = QAction("History", view_menu)
        history_tab_action.setShortcut(QKeySequence("Ctrl+3"))
        history_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(history_tab_action)
        
        # Switch to Favorites tab
        favorites_tab_action = QAction("Favorites", view_menu)
        favorites_tab_action.setShortcut(QKeySequence("Ctrl+4"))
        favorites_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction(favorites_tab_action)
        
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
        
        # Clear playlist action
        clear_playlist_action = QAction("Clear Playlist", playlist_menu)
        clear_playlist_action.triggered.connect(self._on_clear_playlist)
        playlist_menu.addAction(clear_playlist_action)
        
        # Tools menu
        tools_menu = QMenu("Tools", menu_bar)
        
        # Clear history action
        clear_history_action = QAction("Clear History", tools_menu)
        clear_history_action.triggered.connect(self._on_clear_history)
        tools_menu.addAction(clear_history_action)
        
        # Help menu
        help_menu = QMenu("Help", menu_bar)
        
        # About action
        about_action = QAction("About", help_menu)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
        # Add menus to menu bar
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(view_menu)
        menu_bar.addMenu(playlist_menu)
        menu_bar.addMenu(tools_menu)
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
            QTabWidget::tab-bar {
                alignment: left;
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
        
        # Emit video played signal for history
        self.video_played.emit(video_info, 0.0)
        
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
    
    def _on_fullscreen_requested(self):
        """Handle fullscreen request from player widget."""
        self._toggle_fullscreen()
    
    def _on_player_state_changed(self, state: PlayerState):
        """Handle player state change."""
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
            
            # Update floating window if open
            if self.floating_window:
                self.floating_window.update_video_info(track.video_info)
    
    def _on_position_changed(self, position: float):
        """Handle position change."""
        # Update history with current position
        if self.player.current_track:
            self.history_manager.update_position(
                self.player.current_track.id,
                position
            )
    
    def _on_player_error(self, error: str):
        """Handle player error."""
        self.status_bar.showMessage(f"Error: {error}", 5000)
    
    def _on_video_played(self, video_info: VideoInfo, position: float):
        """Handle video played signal (for history)."""
        self.history_manager.add_entry(video_info, position)
        self.history_widget.refresh()
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self._is_fullscreen:
            self.showNormal()
            self._is_fullscreen = False
        else:
            self.showFullScreen()
            self._is_fullscreen = True
    
    def _toggle_mini_mode(self):
        """Toggle mini mode."""
        if self._is_mini_mode:
            # Restore normal mode
            self.resize(1024, 768)
            self._is_mini_mode = False
            self.status_bar.showMessage("Mini mode: OFF", 2000)
        else:
            # Switch to mini mode
            self.resize(400, 200)
            self._is_mini_mode = True
            self.status_bar.showMessage("Mini mode: ON", 2000)
    
    def _toggle_floating_video(self):
        """Toggle floating video window."""
        if self.floating_window:
            # Close floating window
            self.floating_window.close()
            self.floating_window = None
            self.status_bar.showMessage("Floating video: OFF", 2000)
        else:
            # Create floating window with current track
            current_track = self.player.current_track
            if current_track:
                self.floating_window = FloatingVideoWindow(
                    video_info=current_track.video_info,
                    image_loader=self.image_loader,
                    parent=self
                )
                
                # Connect signals
                self.floating_window.closed.connect(self._on_floating_window_closed)
                self.floating_window.play_clicked.connect(self._on_play_clicked)
                self.floating_window.pause_clicked.connect(self._on_pause_clicked)
                self.floating_window.stop_clicked.connect(self._on_stop_clicked)
                self.floating_window.fullscreen_requested.connect(self._toggle_fullscreen)
                
                # Show the window
                self.floating_window.show()
                self.status_bar.showMessage("Floating video: ON", 2000)
            else:
                self.status_bar.showMessage("No track to display", 2000)
    
    def _on_floating_window_closed(self):
        """Handle floating window closed."""
        self.floating_window = None
    
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
    
    def _on_clear_playlist(self):
        """Handle clear playlist action."""
        self.player.clear_playlist()
        self.playlist_widget.clear_playlist()
        self.status_bar.showMessage("Playlist cleared", 2000)
    
    def _on_clear_history(self):
        """Handle clear history action."""
        self.history_manager.clear_history()
        self.history_widget.refresh()
        self.status_bar.showMessage("History cleared", 2000)
    
    def _on_about(self):
        """Handle about action."""
        from PyQt6.QtWidgets import QMessageBox
        
        about_text = """
        <h2>DebTube - YouTube Music Player</h2>
        <p>Version 0.2.0</p>
        <p>A simple YouTube music player for Debian 12+</p>
        <p>Uses yt-dlp for YouTube access and MPV for playback</p>
        <p>&copy; 2024 DebTube Team</p>
        """
        
        QMessageBox.about(self, "About DebTube", about_text)
    
    def closeEvent(self, event):
        """Handle close event."""
        # Stop the player
        self.player.stop()
        
        # Close floating window if open
        if self.floating_window:
            self.floating_window.close()
        
        # Save current playlist
        if self.current_playlist:
            self.playlist_manager.save_playlist(self.current_playlist)
        
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        # Global shortcuts
        if event.key() == Qt.Key.Key_Escape:
            if self._is_fullscreen:
                self._toggle_fullscreen()
                event.accept()
                return
        
        # Pass to parent
        super().keyPressEvent(event)

"""
Playlist widget for displaying and managing playlists.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QSizePolicy, QMenu, QInputDialog
)
from PyQt6.QtGui import QFont, QIcon, QAction, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from ..core.yt_client import VideoInfo, PlaylistInfo
from ..core.playlist_manager import SavedPlaylist, PlaylistManager
from .video_item import VideoItemWidget
from ..utils.image_loader import ImageLoader


class PlaylistWidget(QWidget):
    """
    Widget for displaying and managing playlists.
    Supports:
    - Displaying videos in a playlist
    - Adding/removing videos
    - Saving/loading playlists
    - Context menu for actions
    """
    
    # Signals
    video_selected = pyqtSignal(VideoInfo)
    video_double_clicked = pyqtSignal(VideoInfo)
    playlist_selected = pyqtSignal(str)  # playlist_id
    
    def __init__(
        self, 
        playlist_manager: PlaylistManager,
        image_loader: ImageLoader,
        show_thumbnails: bool = True
    ):
        super().__init__()
        self.playlist_manager = playlist_manager
        self.image_loader = image_loader
        self.show_thumbnails = show_thumbnails
        
        self._current_playlist: Optional[SavedPlaylist] = None
        self._video_widgets: List[VideoItemWidget] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Header with playlist info and actions
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(12)
        
        self.playlist_title_label = QLabel("Playlist")
        self.playlist_title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.playlist_title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(self.playlist_title_label, stretch=1)
        
        # Action buttons
        self.save_button = QPushButton("💾 Save")
        self.save_button.setStyleSheet(self._get_button_style())
        self.save_button.setToolTip("Save current playlist")
        self.save_button.clicked.connect(self._on_save_clicked)
        header_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton("📂 Load")
        self.load_button.setStyleSheet(self._get_button_style())
        self.load_button.setToolTip("Load a saved playlist")
        self.load_button.clicked.connect(self._on_load_clicked)
        header_layout.addWidget(self.load_button)
        
        self.new_button = QPushButton("➕ New")
        self.new_button.setStyleSheet(self._get_button_style())
        self.new_button.setToolTip("Create new playlist")
        self.new_button.clicked.connect(self._on_new_clicked)
        header_layout.addWidget(self.new_button)
        
        main_layout.addLayout(header_layout)
        
        # Videos list
        self.videos_container = QWidget()
        self.videos_layout = QVBoxLayout()
        self.videos_layout.setContentsMargins(0, 0, 0, 0)
        self.videos_layout.setSpacing(4)
        self.videos_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.videos_container.setLayout(self.videos_layout)
        
        # Scroll area for videos
        from PyQt6.QtWidgets import QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.videos_container)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e;")
        
        main_layout.addWidget(self.scroll_area, stretch=1)
        
        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #222222;")
    
    def _get_button_style(self) -> str:
        """Get the stylesheet for buttons."""
        return """
            QPushButton {
                background-color: #333333;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
        """
    
    def set_playlist(self, playlist: SavedPlaylist):
        """
        Set the current playlist to display.
        
        Args:
            playlist: Playlist to display
        """
        self._current_playlist = playlist
        self.playlist_title_label.setText(playlist.title)
        self._refresh_videos()
    
    def add_video(self, video_info: VideoInfo):
        """
        Add a video to the current playlist.
        
        Args:
            video_info: Video to add
        """
        if not self._current_playlist:
            # Create a new playlist if none exists
            self._current_playlist = self.playlist_manager.create_local_playlist("Untitled Playlist")
            self.playlist_title_label.setText(self._current_playlist.title)
        
        # Add to playlist
        self._current_playlist.add_video(video_info)
        self.playlist_manager.save_playlist(self._current_playlist)
        
        # Add to UI
        self._add_video_widget(video_info)
    
    def remove_video(self, video_id: str):
        """
        Remove a video from the current playlist.
        
        Args:
            video_id: ID of the video to remove
        """
        if not self._current_playlist:
            return
        
        # Remove from playlist
        self._current_playlist.remove_video(video_id)
        self.playlist_manager.save_playlist(self._current_playlist)
        
        # Remove from UI
        self._refresh_videos()
    
    def clear_playlist(self):
        """Clear the current playlist."""
        if self._current_playlist:
            self._current_playlist.videos = []
            self.playlist_manager.save_playlist(self._current_playlist)
        self._refresh_videos()
    
    def _refresh_videos(self):
        """Refresh the list of videos in the UI."""
        # Clear existing widgets
        for widget in self._video_widgets:
            widget.deleteLater()
        self._video_widgets = []
        
        # Clear layout
        while self.videos_layout.count():
            item = self.videos_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new widgets
        if self._current_playlist:
            for video_dict in self._current_playlist.videos:
                video_info = VideoInfo.from_dict(video_dict)
                self._add_video_widget(video_info)
    
    def _add_video_widget(self, video_info: VideoInfo):
        """
        Add a video widget to the layout.
        
        Args:
            video_info: Video information
        """
        widget = VideoItemWidget(
            video_info=video_info,
            image_loader=self.image_loader,
            show_thumbnail=self.show_thumbnails
        )
        widget.clicked.connect(lambda: self.video_selected.emit(video_info))
        widget.double_clicked.connect(lambda: self.video_double_clicked.emit(video_info))
        
        # Add context menu
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, v=video_info: self._show_context_menu(widget, v, pos)
        )
        
        self.videos_layout.addWidget(widget)
        self._video_widgets.append(widget)
    
    def _show_context_menu(self, widget: VideoItemWidget, video_info: VideoInfo, pos):
        """
        Show context menu for a video item.
        
        Args:
            widget: The video widget
            video_info: Video information
            pos: Position for the menu
        """
        menu = QMenu(self)
        
        # Play action
        play_action = QAction("Play", menu)
        play_action.triggered.connect(lambda: self.video_double_clicked.emit(video_info))
        menu.addAction(play_action)
        
        # Remove action
        remove_action = QAction("Remove from playlist", menu)
        remove_action.triggered.connect(lambda: self.remove_video(video_info.id))
        menu.addAction(remove_action)
        
        # Info action
        info_action = QAction("Show info", menu)
        info_action.triggered.connect(lambda: self._show_video_info(video_info))
        menu.addAction(info_action)
        
        menu.exec(widget.mapToGlobal(pos))
    
    def _show_video_info(self, video_info: VideoInfo):
        """
        Show video information in a dialog.
        
        Args:
            video_info: Video information
        """
        from PyQt6.QtWidgets import QMessageBox
        
        info_text = f"""
        <b>{video_info.title}</b><br><br>
        Channel: {video_info.channel}<br>
        Duration: {self._format_duration(video_info.duration)}<br>
        Views: {video_info.view_count:,}<br>
        Upload Date: {video_info.upload_date}<br><br>
        {video_info.description[:200]}...
        """
        
        QMessageBox.information(self, "Video Info", info_text)
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS."""
        from ..utils.helpers import format_duration
        return format_duration(seconds)
    
    def _on_save_clicked(self):
        """Handle save button click."""
        if not self._current_playlist:
            return
        
        # Save the playlist
        if self.playlist_manager.save_playlist(self._current_playlist):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Saved", f"Playlist '{self._current_playlist.title}' saved successfully.")
    
    def _on_load_clicked(self):
        """Handle load button click."""
        # Get list of saved playlists
        playlists = self.playlist_manager.list_playlists()
        
        if not playlists:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Playlists", "No saved playlists found.")
            return
        
        # Create a dialog to select a playlist
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Playlist")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        list_widget = QListWidget()
        for playlist in playlists:
            item = QListWidgetItem(playlist.title)
            item.setData(Qt.ItemDataRole.UserRole, playlist.id)
            list_widget.addItem(item)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(list_widget)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_item = list_widget.currentItem()
            if selected_item:
                playlist_id = selected_item.data(Qt.ItemDataRole.UserRole)
                playlist = self.playlist_manager.load_playlist(playlist_id)
                if playlist:
                    self.set_playlist(playlist)
                    self.playlist_selected.emit(playlist_id)
    
    def _on_new_clicked(self):
        """Handle new playlist button click."""
        text, ok = QInputDialog.getText(
            self, 
            "New Playlist", 
            "Enter playlist name:"
        )
        
        if ok and text:
            playlist = self.playlist_manager.create_local_playlist(text)
            self.set_playlist(playlist)
            self.playlist_selected.emit(playlist.id)

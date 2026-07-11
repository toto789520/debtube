"""
Search widget for searching YouTube videos and playlists.
"""

from typing import List, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QComboBox, QLabel, QSizePolicy, QListWidget, QListWidgetItem,
    QStackedWidget, QFrame
)
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer

from ..core.yt_client import VideoInfo, YouTubeClient
from ..core.player import Track
from .video_item import VideoItemWidget
from ..utils.image_loader import ImageLoader


class SearchWidget(QWidget):
    """
    Widget for searching YouTube content.
    Supports:
    - Searching for videos
    - Searching for playlists
    - Displaying results
    - Adding results to playlist
    """
    
    # Signals
    video_selected = pyqtSignal(VideoInfo)
    video_double_clicked = pyqtSignal(VideoInfo)
    playlist_selected = pyqtSignal(str)  # playlist_id
    
    def __init__(
        self, 
        yt_client: YouTubeClient,
        image_loader: ImageLoader,
        show_thumbnails: bool = True
    ):
        super().__init__()
        self.yt_client = yt_client
        self.image_loader = image_loader
        self.show_thumbnails = show_thumbnails
        
        self._search_results: List[VideoInfo] = []
        self._video_widgets: List[VideoItemWidget] = []
        self._search_timer: Optional[QTimer] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 8, 8, 8)
        search_layout.setSpacing(8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for music, videos, or playlists...")
        self.search_input.setFont(QFont("Segoe UI", 10))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 12px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_search)
        
        self.search_button = QPushButton("🔍 Search")
        self.search_button.setStyleSheet(self._get_button_style())
        self.search_button.clicked.connect(self._on_search)
        
        # Search type selector
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Videos", "Playlists", "All"])
        self.search_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                color: #ffffff;
                selection-background-color: #4CAF50;
            }
        """)
        
        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(self.search_type_combo)
        search_layout.addWidget(self.search_button)
        
        main_layout.addLayout(search_layout)
        
        # YouTube Music toggle
        self.yt_music_toggle = QPushButton("YouTube Music: OFF")
        self.yt_music_toggle.setCheckable(True)
        self.yt_music_toggle.setStyleSheet(self._get_toggle_button_style(False))
        self.yt_music_toggle.clicked.connect(self._on_yt_music_toggle)
        
        toggle_layout = QHBoxLayout()
        toggle_layout.setContentsMargins(8, 0, 8, 0)
        toggle_layout.addWidget(self.yt_music_toggle)
        toggle_layout.addStretch()
        main_layout.addLayout(toggle_layout)
        
        # Results container
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(4)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_container.setLayout(self.results_layout)
        
        # Scroll area for results
        from PyQt6.QtWidgets import QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.results_container)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e;")
        
        main_layout.addWidget(self.scroll_area, stretch=1)
        
        # Status label
        self.status_label = QLabel("Enter a search query above")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet("color: #aaaaaa;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #222222;")
        
        # Setup search timer for delayed search
        self._search_timer = QTimer()
        self._search_timer.setInterval(500)  # 500ms delay
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._on_search)
    
    def _get_button_style(self) -> str:
        """Get the stylesheet for buttons."""
        return """
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                padding: 6px 12px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #55BF55;
            }
            QPushButton:pressed {
                background-color: #3A8F3A;
            }
        """
    
    def _get_toggle_button_style(self, active: bool) -> str:
        """Get the stylesheet for toggle button."""
        if active:
            return """
                QPushButton {
                    background-color: #4CAF50;
                    border: none;
                    border-radius: 4px;
                    color: #ffffff;
                    padding: 4px 8px;
                    font-size: 10px;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #333333;
                    border: none;
                    border-radius: 4px;
                    color: #aaaaaa;
                    padding: 4px 8px;
                    font-size: 10px;
                }
            """
    
    def _on_text_changed(self, text: str):
        """Handle text changed in search input."""
        if text.strip():
            self._search_timer.start()
        else:
            self._search_timer.stop()
    
    def _on_search(self):
        """Perform a search."""
        query = self.search_input.text().strip()
        if not query:
            self._clear_results()
            self.status_label.setText("Enter a search query above")
            return
        
        # Get search type
        search_type = self.search_type_combo.currentText().lower()
        filter_type = "video" if search_type == "videos" else "playlist" if search_type == "playlists" else "all"
        
        # Get YouTube Music flag
        yt_music = self.yt_music_toggle.isChecked()
        
        # Perform search
        self.status_label.setText(f"Searching for '{query}'...")
        
        # Search in a thread to avoid blocking the UI
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class SearchThread(QThread):
            finished = pyqtSignal(List[VideoInfo])
            error = pyqtSignal(str)
            
            def __init__(self, query, filter_type, yt_music):
                super().__init__()
                self.query = query
                self.filter_type = filter_type
                self.yt_music = yt_music
            
            def run(self):
                try:
                    results = self.parent().yt_client.search(
                        self.query,
                        max_results=20,
                        filter_type=self.filter_type,
                        yt_music=self.yt_music
                    )
                    self.finished.emit(results)
                except Exception as e:
                    self.error.emit(str(e))
        
        thread = SearchThread(query, filter_type, yt_music)
        thread.finished.connect(self._on_search_finished)
        thread.error.connect(self._on_search_error)
        thread.start()
    
    def _on_search_finished(self, results: List[VideoInfo]):
        """Handle search results."""
        self._search_results = results
        self._display_results(results)
        
        if results:
            self.status_label.setText(f"Found {len(results)} results")
        else:
            self.status_label.setText("No results found")
    
    def _on_search_error(self, error: str):
        """Handle search error."""
        self._clear_results()
        self.status_label.setText(f"Error: {error}")
    
    def _display_results(self, results: List[VideoInfo]):
        """Display search results."""
        # Clear existing widgets
        self._clear_results()
        
        if not results:
            return
        
        # Add new widgets
        for video_info in results:
            widget = VideoItemWidget(
                video_info=video_info,
                image_loader=self.image_loader,
                show_thumbnail=self.show_thumbnails
            )
            widget.clicked.connect(lambda v=video_info: self.video_selected.emit(v))
            widget.double_clicked.connect(lambda v=video_info: self.video_double_clicked.emit(v))
            
            # Add context menu
            widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            widget.customContextMenuRequested.connect(
                lambda pos, vi=video_info: self._show_context_menu(widget, vi, pos)
            )
            
            self.results_layout.addWidget(widget)
            self._video_widgets.append(widget)
    
    def _clear_results(self):
        """Clear search results."""
        for widget in self._video_widgets:
            widget.deleteLater()
        self._video_widgets = []
        
        # Clear layout
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _show_context_menu(self, widget: VideoItemWidget, video_info: VideoInfo, pos):
        """
        Show context menu for a search result.
        
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
        
        # Add to playlist action
        add_action = QAction("Add to playlist", menu)
        add_action.triggered.connect(lambda: self.video_selected.emit(video_info))
        menu.addAction(add_action)
        
        # Show info action
        info_action = QAction("Show info", menu)
        info_action.triggered.connect(lambda: self._show_video_info(video_info))
        menu.addAction(info_action)
        
        # If it's a playlist, add import action
        if video_info.id.startswith("PL") or video_info.id.startswith("OLAK5uy"):
            import_action = QAction("Import playlist", menu)
            import_action.triggered.connect(lambda: self.playlist_selected.emit(video_info.id))
            menu.addAction(import_action)
        
        menu.exec(widget.mapToGlobal(pos))
    
    def _show_video_info(self, video_info: VideoInfo):
        """
        Show video information in a dialog.
        
        Args:
            video_info: Video information
        """
        from PyQt6.QtWidgets import QMessageBox
        from ..utils.helpers import format_duration, format_view_count, format_date
        
        info_text = f"""
        <b>{video_info.title}</b><br><br>
        Channel: {video_info.channel}<br>
        Duration: {format_duration(video_info.duration)}<br>
        Views: {format_view_count(video_info.view_count)}<br>
        Upload Date: {format_date(video_info.upload_date)}<br><br>
        ID: {video_info.id}<br>
        URL: <a href="{video_info.url}">{video_info.url}</a>
        """
        
        QMessageBox.information(self, "Video Info", info_text)
    
    def _on_yt_music_toggle(self, checked: bool):
        """Handle YouTube Music toggle."""
        self.yt_music_toggle.setText(f"YouTube Music: {'ON' if checked else 'OFF'}")
        self.yt_music_toggle.setStyleSheet(self._get_toggle_button_style(checked))
        
        # Re-search if there's a query
        if self.search_input.text().strip():
            self._on_search()
    
    def set_search_text(self, text: str):
        """Set the search text."""
        self.search_input.setText(text)
    
    def focus_search(self):
        """Focus the search input."""
        self.search_input.setFocus()

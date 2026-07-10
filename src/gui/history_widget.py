"""
History widget for displaying recently played videos.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QScrollArea, QFrame
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from ..core.history_manager import HistoryManager, HistoryEntry
from ..core.yt_client import VideoInfo
from ..utils.image_loader import ImageLoader
from .video_item import VideoItemWidget


class HistoryWidget(QWidget):
    """
    Widget for displaying play history.
    """
    
    # Signals
    video_selected = pyqtSignal(VideoInfo)
    video_double_clicked = pyqtSignal(VideoInfo)
    
    def __init__(
        self,
        history_manager: HistoryManager,
        image_loader: ImageLoader,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.history_manager = history_manager
        self.image_loader = image_loader
        self._history_entries: List[HistoryEntry] = []
        self._video_widgets: List[VideoItemWidget] = []
        
        self._setup_ui()
        self._refresh_history()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(12)
        
        self.title_label = QLabel("🕒 History")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(self.title_label, stretch=1)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet(self._get_button_style())
        self.clear_button.clicked.connect(self._on_clear_clicked)
        header_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(header_layout)
        
        # History list
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout()
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(4)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_container.setLayout(self.history_layout)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.history_container)
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
    
    def _refresh_history(self):
        """Refresh the history display."""
        # Clear existing widgets
        self._clear_widgets()
        
        # Get history
        self._history_entries = self.history_manager.get_history()
        
        # Add new widgets
        for entry in self._history_entries:
            video_info = VideoInfo(
                id=entry.video_id,
                title=entry.title,
                channel=entry.channel,
                channel_id=entry.channel_id,
                duration=entry.duration,
                thumbnail_url=entry.thumbnail_url,
                url=entry.url
            )
            self._add_video_widget(video_info)
    
    def _clear_widgets(self):
        """Clear all video widgets."""
        for widget in self._video_widgets:
            widget.deleteLater()
        self._video_widgets = []
        
        # Clear layout
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _add_video_widget(self, video_info: VideoInfo):
        """Add a video widget to the layout."""
        widget = VideoItemWidget(
            video_info=video_info,
            image_loader=self.image_loader,
            show_thumbnail=True,
            show_duration=True,
            show_channel=True
        )
        widget.clicked.connect(lambda v=video_info: self.video_selected.emit(v))
        widget.double_clicked.connect(lambda v=video_info: self.video_double_clicked.emit(v))
        
        self.history_layout.addWidget(widget)
        self._video_widgets.append(widget)
    
    def _on_clear_clicked(self):
        """Handle clear button click."""
        self.history_manager.clear_history()
        self._refresh_history()
    
    def add_to_history(self, video_info: VideoInfo, position: float = 0.0):
        """
        Add a video to history and refresh display.
        
        Args:
            video_info: Video information
            position: Playback position
        """
        self.history_manager.add_entry(video_info, position)
        self._refresh_history()
    
    def refresh(self):
        """Refresh the history display."""
        self._refresh_history()

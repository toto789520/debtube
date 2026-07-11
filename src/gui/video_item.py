"""
Video item widget for displaying video information in lists.
"""

from typing import Optional
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from ..core.yt_client import VideoInfo
from ..utils.helpers import format_duration, format_view_count, format_date
from ..utils.image_loader import ImageLoader


class VideoItemWidget(QWidget):
    """
    Widget for displaying a video item with thumbnail, title, and metadata.
    """
    
    # Signal emitted when the item is clicked
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    
    def __init__(
        self, 
        video_info: VideoInfo,
        image_loader: ImageLoader,
        thumbnail_size: QSize = QSize(120, 68),
        show_thumbnail: bool = True,
        show_duration: bool = True,
        show_views: bool = True,
        show_channel: bool = True,
        show_date: bool = False
    ):
        super().__init__()
        self.video_info = video_info
        self.image_loader = image_loader
        self.thumbnail_size = thumbnail_size
        self.show_thumbnail = show_thumbnail
        self.show_duration = show_duration
        self.show_views = show_views
        self.show_channel = show_channel
        self.show_date = show_date
        
        self._setup_ui()
        self._load_thumbnail()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        
        # Thumbnail
        if self.show_thumbnail:
            self.thumbnail_label = QLabel()
            self.thumbnail_label.setFixedSize(self.thumbnail_size)
            self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.thumbnail_label.setStyleSheet("background-color: #333;")
            main_layout.addWidget(self.thumbnail_label)
        
        # Info layout
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self.title_label = QLabel(self.video_info.title)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(self.title_label)
        
        # Metadata
        metadata_parts = []
        
        if self.show_channel:
            metadata_parts.append(self.video_info.channel)
        
        if self.show_duration:
            metadata_parts.append(format_duration(self.video_info.duration))
        
        if self.show_views and self.video_info.view_count > 0:
            metadata_parts.append(format_view_count(self.video_info.view_count))
        
        if self.show_date and self.video_info.upload_date:
            metadata_parts.append(format_date(self.video_info.upload_date))
        
        if metadata_parts:
            self.metadata_label = QLabel(" | ".join(metadata_parts))
            self.metadata_label.setFont(QFont("Segoe UI", 8))
            self.metadata_label.setStyleSheet("color: #aaaaaa;")
            info_layout.addWidget(self.metadata_label)
        
        main_layout.addLayout(info_layout, stretch=1)
        
        # Duration label (right-aligned)
        if self.show_duration and not any([self.show_channel, self.show_views, self.show_date]):
            self.duration_label = QLabel(format_duration(self.video_info.duration))
            self.duration_label.setFont(QFont("Segoe UI", 8))
            self.duration_label.setStyleSheet("color: #aaaaaa;")
            main_layout.addWidget(self.duration_label)
        
        self.setLayout(main_layout)
        
        # Set stylesheet
        self.setStyleSheet("""
            VideoItemWidget {
                background-color: #222222;
                border-radius: 4px;
            }
            VideoItemWidget:hover {
                background-color: #333333;
            }
        """)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
    
    def _load_thumbnail(self):
        """Load the thumbnail for the video."""
        if not self.show_thumbnail:
            return
        
        # Use a placeholder initially
        self.thumbnail_label.setPixmap(self.image_loader.get_default_thumbnail(self.thumbnail_size))
        
        # Load the actual thumbnail in the background
        if self.video_info.thumbnail_url:
            pixmap = self.image_loader.load_from_url(
                self.video_info.thumbnail_url,
                self.thumbnail_size
            )
            if not pixmap.isNull():
                self.thumbnail_label.setPixmap(pixmap)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double-click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter events."""
        self.setStyleSheet("""
            VideoItemWidget {
                background-color: #333333;
                border-radius: 4px;
            }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        self.setStyleSheet("""
            VideoItemWidget {
                background-color: #222222;
                border-radius: 4px;
            }
        """)
        super().leaveEvent(event)
    
    def update_video_info(self, video_info: VideoInfo):
        """Update the video information displayed by this widget."""
        self.video_info = video_info
        self.title_label.setText(video_info.title)
        
        # Update metadata
        metadata_parts = []
        if self.show_channel:
            metadata_parts.append(video_info.channel)
        if self.show_duration:
            metadata_parts.append(format_duration(video_info.duration))
        if self.show_views and video_info.view_count > 0:
            metadata_parts.append(format_view_count(video_info.view_count))
        if self.show_date and video_info.upload_date:
            metadata_parts.append(format_date(video_info.upload_date))
        
        if metadata_parts and hasattr(self, "metadata_label"):
            self.metadata_label.setText(" | ".join(metadata_parts))
        
        # Reload thumbnail
        self._load_thumbnail()

"""
Floating video window for displaying video with controls.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from ..core.yt_client import VideoInfo
from ..utils.image_loader import ImageLoader


class FloatingVideoWindow(QWidget):
    """
    Floating window that displays a video with playback controls.
    Can be moved around the screen and resized.
    """
    
    # Signals
    closed = pyqtSignal()
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    fullscreen_requested = pyqtSignal()
    
    def __init__(
        self,
        video_info: VideoInfo,
        image_loader: ImageLoader,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.video_info = video_info
        self.image_loader = image_loader
        self._is_dragging = False
        self._drag_start_position = QPoint()
        
        self._setup_ui()
        self._setup_styles()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Set window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Title bar with drag handle
        self.title_bar = QWidget()
        self.title_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.title_bar.setFixedHeight(30)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        self.title_label = QLabel(self.video_info.title)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff;")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.channel_label = QLabel(self.video_info.channel)
        self.channel_label.setFont(QFont("Segoe UI", 8))
        self.channel_label.setStyleSheet("color: #aaaaaa;")
        
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
            QPushButton:pressed {
                background-color: #cc3333;
            }
        """)
        self.close_button.clicked.connect(self.close)
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.channel_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_button)
        
        self.title_bar.setLayout(title_layout)
        
        # Video/Thumbnail display
        self.video_frame = QFrame()
        self.video_frame.setFrameShape(QFrame.Shape.Box)
        self.video_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.video_frame.setStyleSheet("background-color: #000000;")
        self.video_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.video_layout = QVBoxLayout()
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Thumbnail display (when not playing video)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: #111111;")
        
        # Video widget (for actual video playback)
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.hide()
        
        self.video_layout.addWidget(self.thumbnail_label)
        self.video_layout.addWidget(self.video_widget)
        self.video_frame.setLayout(self.video_layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(32, 32)
        self.play_button.setStyleSheet(self._get_control_button_style())
        self.play_button.clicked.connect(self._on_play_clicked)
        
        self.pause_button = QPushButton("⏸")
        self.pause_button.setFixedSize(32, 32)
        self.pause_button.setStyleSheet(self._get_control_button_style())
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.pause_button.hide()
        
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(32, 32)
        self.stop_button.setStyleSheet(self._get_control_button_style())
        self.stop_button.clicked.connect(self._on_stop_clicked)
        
        self.fullscreen_button = QPushButton("⛶")
        self.fullscreen_button.setFixedSize(32, 32)
        self.fullscreen_button.setStyleSheet(self._get_control_button_style())
        self.fullscreen_button.clicked.connect(self._on_fullscreen_clicked)
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self.fullscreen_button)
        
        # Add widgets to main layout
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(self.video_frame, stretch=1)
        main_layout.addLayout(controls_layout)
        
        self.setLayout(main_layout)
        
        # Set initial size
        self.resize(400, 300)
        
        # Load thumbnail
        self._load_thumbnail()
    
    def _setup_styles(self):
        """Set up stylesheets."""
        self.setStyleSheet("""
            FloatingVideoWindow {
                background-color: #222222;
                border-radius: 8px;
                border: 1px solid #333333;
            }
            QLabel {
                color: #ffffff;
            }
        """)
    
    def _get_control_button_style(self) -> str:
        """Get stylesheet for control buttons."""
        return """
            QPushButton {
                background-color: #333333;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
        """
    
    def _load_thumbnail(self):
        """Load the thumbnail for the video."""
        if self.video_info.thumbnail_url:
            pixmap = self.image_loader.load_from_url(
                self.video_info.thumbnail_url,
                QSize(400, 225)
            )
            if not pixmap.isNull():
                self.thumbnail_label.setPixmap(pixmap)
                return
        
        # Use default thumbnail
        self.thumbnail_label.setPixmap(self.image_loader.get_default_thumbnail(QSize(400, 225)))
    
    def _on_play_clicked(self):
        """Handle play button click."""
        self.play_clicked.emit()
        self.play_button.hide()
        self.pause_button.show()
    
    def _on_pause_clicked(self):
        """Handle pause button click."""
        self.pause_clicked.emit()
        self.pause_button.hide()
        self.play_button.show()
    
    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.stop_clicked.emit()
        self.pause_button.hide()
        self.play_button.show()
    
    def _on_fullscreen_clicked(self):
        """Handle fullscreen button click."""
        self.fullscreen_requested.emit()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_position = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events for dragging."""
        if self._is_dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_start_position
            self.move(new_pos)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter events."""
        self.setStyleSheet("""
            FloatingVideoWindow {
                background-color: #282828;
                border-radius: 8px;
                border: 1px solid #444444;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        self.setStyleSheet("""
            FloatingVideoWindow {
                background-color: #222222;
                border-radius: 8px;
                border: 1px solid #333333;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        super().leaveEvent(event)
    
    def closeEvent(self, event):
        """Handle close events."""
        self.closed.emit()
        super().closeEvent(event)
    
    def set_video_mode(self, enabled: bool):
        """
        Enable or disable video mode.
        
        Args:
            enabled: True to show video widget, False to show thumbnail
        """
        if enabled:
            self.thumbnail_label.hide()
            self.video_widget.show()
        else:
            self.video_widget.hide()
            self.thumbnail_label.show()
    
    def update_video_info(self, video_info: VideoInfo):
        """
        Update the video information.
        
        Args:
            video_info: New video information
        """
        self.video_info = video_info
        self.title_label.setText(video_info.title)
        self.channel_label.setText(video_info.channel)
        self._load_thumbnail()
    
    def set_playing(self, playing: bool):
        """
        Update the UI to reflect playing state.
        
        Args:
            playing: True if playing, False otherwise
        """
        if playing:
            self.play_button.hide()
            self.pause_button.show()
        else:
            self.pause_button.hide()
            self.play_button.show()

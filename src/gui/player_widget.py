"""
Player control widget with play/pause/stop/next/previous buttons and progress bar.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider,
    QLabel, QSizePolicy
)
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer

from ..core.player import Player, PlayerState, Track
from ..utils.helpers import format_duration


class PlayerWidget(QWidget):
    """
    Widget for controlling the player with playback controls and progress display.
    """
    
    # Signals
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    volume_changed = pyqtSignal(int)
    seek_requested = pyqtSignal(float)
    
    def __init__(self, player: Player):
        super().__init__()
        self.player = player
        self._setup_ui()
        self._setup_connections()
        self._update_state(PlayerState.STOPPED)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Progress bar
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)  # Will be scaled to actual duration
        self.progress_slider.setValue(0)
        self.progress_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333333;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 2px;
            }
        """)
        
        # Time labels
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(8)
        
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setFont(QFont("Segoe UI", 8))
        self.current_time_label.setStyleSheet("color: #aaaaaa;")
        self.current_time_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.duration_label = QLabel("0:00")
        self.duration_label.setFont(QFont("Segoe UI", 8))
        self.duration_label.setStyleSheet("color: #aaaaaa;")
        self.duration_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.duration_label)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)
        
        # Previous button
        self.previous_button = QPushButton()
        self.previous_button.setIcon(self._create_icon("⏮"))
        self.previous_button.setFixedSize(32, 32)
        self.previous_button.setStyleSheet(self._get_button_style())
        self.previous_button.setToolTip("Previous")
        
        # Play/Pause button
        self.play_button = QPushButton()
        self.play_button.setIcon(self._create_icon("▶"))
        self.play_button.setFixedSize(40, 40)
        self.play_button.setStyleSheet(self._get_play_button_style())
        self.play_button.setToolTip("Play")
        
        # Next button
        self.next_button = QPushButton()
        self.next_button.setIcon(self._create_icon("⏭"))
        self.next_button.setFixedSize(32, 32)
        self.next_button.setStyleSheet(self._get_button_style())
        self.next_button.setToolTip("Next")
        
        # Stop button
        self.stop_button = QPushButton()
        self.stop_button.setIcon(self._create_icon("⏹"))
        self.stop_button.setFixedSize(32, 32)
        self.stop_button.setStyleSheet(self._get_button_style())
        self.stop_button.setToolTip("Stop")
        
        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.stop_button)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(8)
        
        self.volume_button = QPushButton()
        self.volume_button.setIcon(self._create_icon("🔊"))
        self.volume_button.setFixedSize(24, 24)
        self.volume_button.setStyleSheet(self._get_button_style())
        self.volume_button.setToolTip("Mute")
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333333;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 10px;
                height: 10px;
                border-radius: 5px;
                margin: -3px 0;
            }
            QSlider::sub-page:horizontal {
                background: #ffffff;
                border-radius: 2px;
            }
        """)
        
        volume_layout.addWidget(self.volume_button)
        volume_layout.addWidget(self.volume_slider)
        
        # Track info
        self.track_info_label = QLabel("No track selected")
        self.track_info_label.setFont(QFont("Segoe UI", 10))
        self.track_info_label.setStyleSheet("color: #ffffff;")
        self.track_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add widgets to main layout
        main_layout.addWidget(self.progress_slider)
        main_layout.addLayout(time_layout)
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(volume_layout)
        main_layout.addWidget(self.track_info_label)
        
        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #1e1e1e;")
    
    def _setup_connections(self):
        """Set up signal connections."""
        # Button connections
        self.play_button.clicked.connect(self._on_play_clicked)
        self.pause_button.clicked.connect(self._on_pause_clicked)  # Will be set up dynamically
        self.next_button.clicked.connect(self._on_next_clicked)
        self.previous_button.clicked.connect(self._on_previous_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.volume_button.clicked.connect(self._on_volume_button_clicked)
        self.progress_slider.sliderMoved.connect(self._on_seek)
        
        # Player connections
        self.player.state_changed.connect(self._on_state_changed)
        self.player.track_changed.connect(self._on_track_changed)
        self.player.position_changed.connect(self._on_position_changed)
        self.player.duration_changed.connect(self._on_duration_changed)
        self.player.volume_changed.connect(self._on_volume_updated)
    
    def _create_icon(self, text: str) -> QIcon:
        """Create an icon from text."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Simple approach: use a QLabel to render the text
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 10))
        label.setStyleSheet("color: white;")
        label.setFixedSize(16, 16)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Render the label to a pixmap
        pixmap = label.grab()
        return QIcon(pixmap)
    
    def _get_button_style(self) -> str:
        """Get the stylesheet for control buttons."""
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
    
    def _get_play_button_style(self) -> str:
        """Get the stylesheet for the play button."""
        return """
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 20px;
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #55BF55;
            }
            QPushButton:pressed {
                background-color: #3A8F3A;
            }
        """
    
    def _on_play_clicked(self):
        """Handle play button click."""
        self.play_clicked.emit()
    
    def _on_pause_clicked(self):
        """Handle pause button click."""
        self.pause_clicked.emit()
    
    def _on_next_clicked(self):
        """Handle next button click."""
        self.next_clicked.emit()
    
    def _on_previous_clicked(self):
        """Handle previous button click."""
        self.previous_clicked.emit()
    
    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.stop_clicked.emit()
    
    def _on_volume_changed(self, value: int):
        """Handle volume slider change."""
        self.volume_changed.emit(value)
    
    def _on_volume_button_clicked(self):
        """Handle volume button click (toggle mute)."""
        if self.player.volume > 0:
            self.player.volume = 0
        else:
            self.player.volume = 50
    
    def _on_seek(self, value: int):
        """Handle seek request from progress slider."""
        # Scale the slider value to the actual duration
        if self.player.current_duration > 0:
            position = (value / 1000) * self.player.current_duration
            self.seek_requested.emit(position)
    
    def _on_state_changed(self, state: PlayerState):
        """Handle player state change."""
        self._update_state(state)
    
    def _on_track_changed(self, track: Track):
        """Handle track change."""
        if track:
            self.track_info_label.setText(f"{track.title} - {track.video_info.channel}")
        else:
            self.track_info_label.setText("No track selected")
    
    def _on_position_changed(self, position: float):
        """Handle position change."""
        self.current_time_label.setText(format_duration(int(position)))
        
        # Update progress slider
        if self.player.current_duration > 0:
            value = int((position / self.player.current_duration) * 1000)
            self.progress_slider.setValue(value)
    
    def _on_duration_changed(self, duration: float):
        """Handle duration change."""
        self.duration_label.setText(format_duration(int(duration)))
        self.progress_slider.setRange(0, 1000)
    
    def _on_volume_updated(self, volume: int):
        """Handle volume update from player."""
        self.volume_slider.setValue(volume)
    
    def _update_state(self, state: PlayerState):
        """Update the UI based on the player state."""
        if state == PlayerState.PLAYING:
            self.play_button.setIcon(self._create_icon("⏸"))
            self.play_button.setToolTip("Pause")
            self.play_button.clicked.disconnect(self._on_play_clicked)
            self.play_button.clicked.connect(self._on_pause_clicked)
        else:
            self.play_button.setIcon(self._create_icon("▶"))
            self.play_button.setToolTip("Play")
            self.play_button.clicked.disconnect(self._on_pause_clicked)
            self.play_button.clicked.connect(self._on_play_clicked)
    
    def set_progress(self, position: float, duration: float):
        """Manually set the progress."""
        self.current_time_label.setText(format_duration(int(position)))
        self.duration_label.setText(format_duration(int(duration)))
        
        if duration > 0:
            value = int((position / duration) * 1000)
            self.progress_slider.setValue(value)

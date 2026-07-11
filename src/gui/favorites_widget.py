"""
Favorites widget for displaying and managing favorite videos.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSizePolicy, QScrollArea, QInputDialog, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.favorites_manager import FavoritesManager, FavoriteEntry
from ..core.yt_client import VideoInfo
from ..utils.image_loader import ImageLoader
from .video_item import VideoItemWidget


class FavoritesWidget(QWidget):
    """
    Widget for displaying and managing favorite videos.
    """
    
    # Signals
    video_selected = pyqtSignal(VideoInfo)
    video_double_clicked = pyqtSignal(VideoInfo)
    
    def __init__(
        self,
        favorites_manager: FavoritesManager,
        image_loader: ImageLoader,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.favorites_manager = favorites_manager
        self.image_loader = image_loader
        self._favorite_entries: List[FavoriteEntry] = []
        self._video_widgets: List[VideoItemWidget] = []
        
        self._setup_ui()
        self._refresh_favorites()
    
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
        
        self.title_label = QLabel("⭐ Favorites")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(self.title_label)
        
        # Category selector
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 4px;
                color: #ffffff;
                padding: 4px;
                min-width: 120px;
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
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        header_layout.addWidget(self.category_combo)
        
        # Add category button
        self.add_category_button = QPushButton("➕")
        self.add_category_button.setFixedSize(28, 28)
        self.add_category_button.setStyleSheet(self._get_button_style())
        self.add_category_button.setToolTip("Add category")
        self.add_category_button.clicked.connect(self._on_add_category_clicked)
        header_layout.addWidget(self.add_category_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet(self._get_button_style())
        self.clear_button.clicked.connect(self._on_clear_clicked)
        header_layout.addWidget(self.clear_button)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Favorites list
        self.favorites_container = QWidget()
        self.favorites_layout = QVBoxLayout()
        self.favorites_layout.setContentsMargins(0, 0, 0, 0)
        self.favorites_layout.setSpacing(4)
        self.favorites_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.favorites_container.setLayout(self.favorites_layout)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.favorites_container)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e;")
        
        main_layout.addWidget(self.scroll_area, stretch=1)
        
        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #222222;")
        
        # Update categories
        self._update_categories()
    
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
    
    def _update_categories(self):
        """Update the category combo box."""
        categories = self.favorites_manager.get_categories()
        self.category_combo.clear()
        self.category_combo.addItem("All")
        self.category_combo.addItems(categories)
    
    def _refresh_favorites(self, category: str = "All"):
        """Refresh the favorites display."""
        # Clear existing widgets
        self._clear_widgets()
        
        # Get favorites
        if category == "All":
            self._favorite_entries = self.favorites_manager.get_favorites()
        else:
            self._favorite_entries = self.favorites_manager.get_favorites_by_category(category)
        
        # Add new widgets
        for entry in self._favorite_entries:
            video_info = VideoInfo(
                id=entry.video_id,
                title=entry.title,
                channel=entry.channel,
                channel_id=entry.channel_id,
                duration=entry.duration,
                thumbnail_url=entry.thumbnail_url,
                url=entry.url
            )
            self._add_video_widget(video_info, entry)
    
    def _clear_widgets(self):
        """Clear all video widgets."""
        for widget in self._video_widgets:
            widget.deleteLater()
        self._video_widgets = []
        
        # Clear layout
        while self.favorites_layout.count():
            item = self.favorites_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _add_video_widget(self, video_info: VideoInfo, entry: FavoriteEntry):
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
        
        # Add context menu
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, e=entry: self._show_context_menu(widget, e, pos)
        )
        
        self.favorites_layout.addWidget(widget)
        self._video_widgets.append(widget)
    
    def _show_context_menu(self, widget: VideoItemWidget, entry: FavoriteEntry, pos):
        """Show context menu for a favorite entry."""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        # Play action
        play_action = QAction("Play", menu)
        play_action.triggered.connect(lambda: self.video_double_clicked.emit(
            VideoInfo(
                id=entry.video_id,
                title=entry.title,
                channel=entry.channel,
                channel_id=entry.channel_id,
                duration=entry.duration,
                thumbnail_url=entry.thumbnail_url,
                url=entry.url
            )
        ))
        menu.addAction(play_action)
        
        # Remove from favorites action
        remove_action = QAction("Remove from favorites", menu)
        remove_action.triggered.connect(lambda: self._on_remove_favorite(entry.video_id))
        menu.addAction(remove_action)
        
        # Change category action
        change_category_action = QAction("Change category", menu)
        change_category_action.triggered.connect(lambda: self._on_change_category(entry))
        menu.addAction(change_category_action)
        
        # Add notes action
        add_notes_action = QAction("Add notes", menu)
        add_notes_action.triggered.connect(lambda: self._on_add_notes(entry))
        menu.addAction(add_notes_action)
        
        menu.exec(widget.mapToGlobal(pos))
    
    def _on_category_changed(self, category: str):
        """Handle category change."""
        self._refresh_favorites(category)
    
    def _on_add_category_clicked(self):
        """Handle add category button click."""
        text, ok = QInputDialog.getText(
            self,
            "Add Category",
            "Enter category name:"
        )
        
        if ok and text:
            # Add a video to the new category (if there are favorites)
            if self._favorite_entries:
                first_entry = self._favorite_entries[0]
                self.favorites_manager.update_category(first_entry.video_id, text)
                self._update_categories()
                self.category_combo.setCurrentText(text)
    
    def _on_clear_clicked(self):
        """Handle clear button click."""
        category = self.category_combo.currentText()
        
        if category == "All":
            reply = QMessageBox.question(
                self,
                "Clear All Favorites",
                "Are you sure you want to clear ALL favorites?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.favorites_manager.clear_favorites()
        else:
            reply = QMessageBox.question(
                self,
                "Clear Category",
                f"Are you sure you want to clear the '{category}' category?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.favorites_manager.clear_category(category)
        
        self._update_categories()
        self._refresh_favorites(category)
    
    def _on_remove_favorite(self, video_id: str):
        """Handle remove favorite."""
        self.favorites_manager.remove_favorite(video_id)
        self._refresh_favorites(self.category_combo.currentText())
    
    def _on_change_category(self, entry: FavoriteEntry):
        """Handle change category for a favorite."""
        categories = self.favorites_manager.get_categories()
        
        if not categories:
            QMessageBox.information(self, "No Categories", "No categories available.")
            return
        
        category, ok = QInputDialog.getItem(
            self,
            "Change Category",
            "Select a category:",
            categories,
            0,
            False
        )
        
        if ok and category:
            self.favorites_manager.update_category(entry.video_id, category)
            self._refresh_favorites(self.category_combo.currentText())
    
    def _on_add_notes(self, entry: FavoriteEntry):
        """Handle add notes for a favorite."""
        text, ok = QInputDialog.getText(
            self,
            "Add Notes",
            "Enter notes for this favorite:",
            QInputDialog.InputMode.Normal,
            entry.notes
        )
        
        if ok:
            self.favorites_manager.update_notes(entry.video_id, text)
    
    def add_to_favorites(self, video_info: VideoInfo, category: str = "General"):
        """
        Add a video to favorites and refresh display.
        
        Args:
            video_info: Video information
            category: Category for the favorite
        """
        if self.favorites_manager.add_favorite(video_info, category):
            self._update_categories()
            self._refresh_favorites(self.category_combo.currentText())
            return True
        return False
    
    def refresh(self):
        """Refresh the favorites display."""
        self._update_categories()
        self._refresh_favorites(self.category_combo.currentText())
    
    def is_favorite(self, video_id: str) -> bool:
        """
        Check if a video is in favorites.
        
        Args:
            video_id: Video ID
        
        Returns:
            True if the video is a favorite
        """
        return self.favorites_manager.is_favorite(video_id)

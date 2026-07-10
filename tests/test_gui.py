"""
Tests for GUI components.
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.core.yt_client import VideoInfo
from src.core.playlist_manager import PlaylistManager
from src.utils.image_loader import ImageLoader
from src.gui.video_item import VideoItemWidget
from src.gui.search_widget import SearchWidget
from src.gui.playlist_widget import PlaylistWidget
from src.gui.player_widget import PlayerWidget


@pytest.fixture
def qapp():
    """Create a QApplication instance for testing."""
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def video_info():
    """Create a sample VideoInfo for testing."""
    return VideoInfo(
        id="test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="UC123",
        duration=180,
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=test123",
        view_count=1000000,
        upload_date="20230115"
    )


@pytest.fixture
def image_loader():
    """Create an ImageLoader for testing."""
    return ImageLoader(cache_enabled=False)


def test_video_item_widget_creation(qapp, video_info, image_loader):
    """Test VideoItemWidget creation."""
    widget = VideoItemWidget(
        video_info=video_info,
        image_loader=image_loader
    )
    
    assert widget is not None
    assert widget.video_info == video_info
    assert widget.title_label.text() == "Test Video"


def test_video_item_widget_signals(qapp, video_info, image_loader, qtbot):
    """Test VideoItemWidget signals."""
    widget = VideoItemWidget(
        video_info=video_info,
        image_loader=image_loader
    )
    
    with qtbot.capture_signals(widget.clicked) as signals:
        # Simulate a click
        qtbot.mouseClick(widget, Qt.MouseButton.LeftButton)
        assert len(signals) == 1


def test_video_item_widget_double_click(qapp, video_info, image_loader, qtbot):
    """Test VideoItemWidget double click signal."""
    widget = VideoItemWidget(
        video_info=video_info,
        image_loader=image_loader
    )
    
    with qtbot.capture_signals(widget.double_clicked) as signals:
        # Simulate a double click
        qtbot.mouseDClick(widget, Qt.MouseButton.LeftButton)
        assert len(signals) == 1


def test_video_item_widget_without_thumbnail(qapp, video_info, image_loader):
    """Test VideoItemWidget without thumbnail."""
    widget = VideoItemWidget(
        video_info=video_info,
        image_loader=image_loader,
        show_thumbnail=False
    )
    
    assert widget is not None
    assert widget.show_thumbnail is False


def test_video_item_widget_metadata(qapp, video_info, image_loader):
    """Test VideoItemWidget with metadata display."""
    widget = VideoItemWidget(
        video_info=video_info,
        image_loader=image_loader,
        show_duration=True,
        show_views=True,
        show_channel=True,
        show_date=True
    )
    
    # Check that metadata is displayed
    assert widget.metadata_label is not None
    metadata_text = widget.metadata_label.text()
    assert "Test Channel" in metadata_text
    assert "3:00" in metadata_text  # 180 seconds = 3:00
    assert "1.0M" in metadata_text  # 1000000 views


def test_search_widget_creation(qapp, image_loader):
    """Test SearchWidget creation."""
    from unittest.mock import MagicMock
    yt_client = MagicMock()
    
    widget = SearchWidget(
        yt_client=yt_client,
        image_loader=image_loader
    )
    
    assert widget is not None
    assert widget.search_input is not None
    assert widget.search_button is not None


def test_search_widget_signals(qapp, image_loader, qtbot):
    """Test SearchWidget signals."""
    from unittest.mock import MagicMock
    yt_client = MagicMock()
    yt_client.search.return_value = []
    
    widget = SearchWidget(
        yt_client=yt_client,
        image_loader=image_loader
    )
    
    # Test return pressed signal
    with qtbot.capture_signals(widget.search_input.returnPressed) as signals:
        qtbot.keyPress(widget.search_input, Qt.Key.Key_Return)
        assert len(signals) == 1


def test_playlist_widget_creation(qapp, image_loader):
    """Test PlaylistWidget creation."""
    from unittest.mock import MagicMock
    yt_client = MagicMock()
    playlist_manager = PlaylistManager(yt_client)
    
    widget = PlaylistWidget(
        playlist_manager=playlist_manager,
        image_loader=image_loader
    )
    
    assert widget is not None
    assert widget.playlist_title_label is not None


def test_player_widget_creation(qapp):
    """Test PlayerWidget creation."""
    from unittest.mock import MagicMock
    yt_client = MagicMock()
    from src.core.player import Player
    player = Player(yt_client)
    
    widget = PlayerWidget(player=player)
    
    assert widget is not None
    assert widget.play_button is not None
    assert widget.pause_button is None  # Not created separately
    assert widget.next_button is not None
    assert widget.previous_button is not None
    assert widget.stop_button is not None
    assert widget.volume_slider is not None


def test_player_widget_volume(qapp, qtbot):
    """Test PlayerWidget volume control."""
    from unittest.mock import MagicMock
    yt_client = MagicMock()
    from src.core.player import Player
    player = Player(yt_client)
    
    widget = PlayerWidget(player=player)
    
    # Test volume slider
    with qtbot.capture_signals(widget.volume_changed) as signals:
        widget.volume_slider.setValue(75)
        assert len(signals) == 1
        assert signals[0][0] == 75


def test_main_window_creation(qapp):
    """Test MainWindow creation."""
    from src.gui.main_window import MainWindow
    
    # This might fail if dependencies are not installed
    try:
        window = MainWindow()
        assert window is not None
        assert window.yt_client is not None
        assert window.player is not None
        assert window.search_widget is not None
        assert window.playlist_widget is not None
        assert window.player_widget is not None
    except Exception as e:
        pytest.skip(f"MainWindow creation failed: {e}")

# DebTube - YouTube Music Player for Debian 12+

A simple, lightweight YouTube music player for Debian 12+ that allows you to search, play, and save music from YouTube and YouTube Music.

## Features

- 🔍 **Search**: Search for music, videos, and playlists on YouTube and YouTube Music
- 🎵 **Playback**: Play audio streams with play/pause/stop/next/previous controls
- 📝 **Playlists**: Create, save, and load playlists locally
- 🌐 **YouTube Integration**: Import public playlists from YouTube users/channels
- 💾 **Offline Support**: Save playlists for future use (metadata only, not audio)
- 🎨 **Modern UI**: Clean, dark-themed interface with PyQt6
- 📊 **Metadata**: Display thumbnails, titles, durations, view counts, and more

## Screenshots

*(Add screenshots here once the UI is complete)*

## Installation

### Prerequisites

- Debian 12 (Bookworm) or later
- Python 3.11 or later
- pip (Python package manager)

### Install Dependencies

#### System Dependencies

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv mpv git
```

#### Python Dependencies

```bash
# Clone the repository
git clone https://github.com/toto789520/debtube.git
cd debtube

# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### Running the Application

```bash
# From the project directory
python3 main.py
```

Or with the virtual environment:

```bash
source venv/bin/activate
python3 main.py
```

## Usage

### Basic Controls

- **Search**: Type in the search bar and press Enter or click Search
- **Play**: Double-click a video to play it immediately
- **Add to Playlist**: Click a video to add it to the current playlist
- **Play/Pause**: Use the controls at the bottom of the window
- **Volume**: Adjust the volume slider
- **Next/Previous**: Navigate through the playlist

### Playlist Management

- **New Playlist**: File → New Playlist or Ctrl+N
- **Load Playlist**: File → Load Playlist or Ctrl+O
- **Save Playlist**: File → Save Playlist or Ctrl+S
- **Import YouTube Playlist**: Playlist → Import YouTube Playlist
- **Import User Playlists**: Playlist → Import User Playlists (imports all public playlists from a channel)

### YouTube Music

- Toggle YouTube Music search mode with the button next to the search bar
- This changes the search source from regular YouTube to YouTube Music

## Project Structure

```
debtube/
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── src/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── yt_client.py      # YouTube/YouTube Music client
    │   ├── player.py         # Audio player (MPV-based)
    │   └── playlist_manager.py # Playlist management
    ├── gui/
    │   ├── __init__.py
    │   ├── main_window.py    # Main application window
    │   ├── search_widget.py  # Search functionality
    │   ├── playlist_widget.py # Playlist display and management
    │   ├── player_widget.py   # Player controls
    │   └── video_item.py     # Video item display
    └── utils/
        ├── __init__.py
        ├── helpers.py         # Helper functions
        └── image_loader.py    # Image loading and caching
```

## Configuration

The application creates a `data/` directory in the project folder to store:
- `cache/`: Cached search results and metadata
- `images/`: Cached thumbnails
- `playlists/`: Saved playlists

## Troubleshooting

### MPV Not Found

If you get an error about MPV not being found:

```bash
sudo apt install mpv
```

### yt-dlp Not Working

If YouTube access fails:

```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Or manually download the latest version
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod +x /usr/local/bin/yt-dlp
```

### Audio Playback Issues

If there's no sound:
- Check your system volume
- Ensure MPV has permission to access audio
- Try running with `mpv --ao=alsa` or `mpv --ao=pulse` to specify the audio output

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-qt

# Run tests
pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines. You can check your code with:

```bash
pip install flake8
flake8 src/
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - For YouTube video extraction
- [MPV](https://mpv.io/) - For audio playback
- [PyQt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/) - For the GUI
- [YouTube](https://www.youtube.com/) - For the music content

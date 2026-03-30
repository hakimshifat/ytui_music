# YTUI Music - Project Context

## Project Overview

**YTUI Music** is a terminal-based YouTube audio player built with Python. It provides a keyboard-first, resource-efficient alternative to browser-based YouTube playback.

### Core Technologies
- **Python 3.11+**
- **Textual** - TUI framework for the user interface
- **textual-image** - Image rendering in terminal (Sixel/Kitty/Block support)
- **yt-dlp** - YouTube stream extraction and search
- **python-mpv** - Audio playback via mpv
- **requests** - HTTP requests for thumbnail fetching

### Architecture

The application follows a modular structure centered around `yt.py`:

```
yt.py (Main Application)
├── AudioPlayer - Singleton MPV wrapper for playback control
├── YTPlayerApp - Main Textual App (grid layout: sidebar + main area)
├── Widgets
│   ├── SearchResultItem - Custom ListItem with inline thumbnails
│   ├── PlayerControls - Button container (prev/play/pause/next/stop)
│   └── ThumbnailWidget - Async thumbnail downloader
└── Background Workers - Search, thumbnail fetch, stream resolution
```

### Key Features
- YouTube search with inline thumbnails (cached per session)
- Background workers for non-blocking operations
- Playback controls: play/pause, stop, next/prev, 10s seek, volume
- Progress bar with elapsed/remaining time
- Keyboard-first navigation

## Building and Running

### Prerequisites
- Python 3.11+
- `mpv` installed on the system (required for playback)

### Installation
```bash
pip install -r requirements.txt
```

### Running
```bash
python yt.py
```

### Debugging
- Logs are written to `player_debug.log` (ERROR level only)

## Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Play selected result |
| `Space` | Toggle play/pause |
| `Left` / `Right` | Seek -10s / +10s |
| `n` / `p` | Next / Previous result (auto-plays) |
| `s` | Stop playback |
| `0` / `9` | Volume up / down |
| `Ctrl+C` | Quit |
| Arrow keys | Navigate results list |

## Development Conventions

### Code Style
- Uses type hints throughout (`bytes | None`, `dict[str, bytes]`)
- Async/await pattern for all I/O operations
- Worker-based concurrency via `run_worker()` with `exit_on_error=False`
- Logging to file instead of console to avoid TUI pollution

### Testing Practices
- No formal test suite present
- Debug logging enabled in `player_debug.log`
- Non-fatal workers keep app alive on errors

### Project Structure
```
ytui_music/
├── yt.py              # Main application (single-file TUI)
├── requirements.txt   # Python dependencies
├── README.md          # User documentation
├── LICENSE            # GPL-3.0
├── .gitignore         # Python/IDE exclusions
└── assets/            # Screenshots
```

## Important Implementation Details

### AudioPlayer Class
- Singleton pattern wrapping `mpv.MPV`
- `vo='null'` prevents video window popup
- Volume clamped to 0-150 range
- Methods: `play()`, `pause()`, `stop()`, `seek()`, `get_time_pos()`, `get_duration()`, `change_volume()`

### Thumbnail Handling
- Thumbnails fetched from `https://i.ytimg.com/vi/{id}/hqdefault.jpg`
- Cached in `thumb_cache: dict[str, bytes]` per session
- Rendered via `TextualImage` widget with `BytesIO`
- Graceful fallback on download failure ("No thumb")

### Search Flow
1. User submits query via `Input` widget
2. `on_input_submitted()` triggers background worker
3. `yt-dlp` extracts flat metadata (`ytsearch15:{query}`)
4. `SearchResultItem` widgets created with async thumbnail loading
5. Results populated in `ListView`

### Playback Flow
1. User selects result → `on_list_view_selected()`
2. `play_video()` extracts video ID, updates UI
3. Background worker fetches audio stream URL via `yt-dlp`
4. `AudioPlayer.play()` streams URL to mpv
5. `update_progress()` polls mpv every 0.5s for progress

### CSS Layout
- Grid: 2 columns (32% sidebar, 68% main)
- Sidebar: Search input + results list (row-span: 2)
- Main: Thumbnail (60% height) + now playing + progress + controls

## Common Pitfalls

1. **mpv not installed**: Playback will fail silently; ensure `mpv` is in PATH
2. **DNS/Network errors**: App shows toast but continues running
3. **Thumbnail failures**: Gracefully handled with "No thumb" fallback
4. **Search concurrency**: `_search_busy` flag prevents duplicate searches

## License

GPL-3.0 (see `LICENSE`)

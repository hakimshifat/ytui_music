# YT TUI Player

My browser takes too much resources even when i just listen to audio. So i made this.

A terminal UI YouTube audio player built with Textual, mpv, and yt-dlp. Search YouTube, browse results with inline thumbnails, and play audio with familiar mpv-like controls (seek, volume, pause). Designed to stay keyboard-first and responsive in the terminal.

![](assets/Pasted%20image%2020251202161743.png)

![](assets/Pasted%20image%2020251202161838.png)

## Features
- YouTube search with inline thumbnails and caching to avoid re-downloads.
- Background workers for search, thumbnail fetch, and playback stream resolution.
- Playback controls: play/pause, stop, next/prev selection, 10s seek forward/back, volume up/down.
- Progress with elapsed/remaining time, percent, and playback state indicator.
- Toast/status messages for errors, seeks, and searches; non-fatal workers to keep the app alive.
- Keyboard-first: enter plays selection, space toggles, left/right seek, n/p navigate, s stops, +/- volume, ctrl+c quits.

## Requirements
- Python 3.11+
- mpv installed on your system (for playback)
- Dependencies listed in `requirements.txt`:
  - textual
  - textual-image
  - yt-dlp
  - requests
  - python-mpv

Install deps:
```bash
pip install -r requirements.txt
```

## Usage
```bash
python yt.py
```

### Keybindings
- `Enter` – play selected result
- `Space` – play/pause
- `Left` / `Right` – seek -10s / +10s
- `n` / `p` – next / previous result (auto-plays)
- `s` – stop
- `+` / `-` – volume up / down
- `Ctrl+C` – quit

### Tips
- Results list scrolls; use arrow keys or `n`/`p` to move.
- Network/DNS errors show in the status line and notifications; the app keeps running.
- Thumbnails are cached per video ID for this session.

## Notes
- The player fetches audio streams via yt-dlp; ensure your network/DNS can reach YouTube.
- If bandwidth is limited, consider adding a `--no-thumb` flag (not included by default).

#!/usr/bin/env python3
"""YTUI Music - Terminal YouTube Audio Player.

A lightweight, keyboard-first YouTube audio player for the terminal.
Built with Textual, mpv, and yt-dlp.

Usage:
    python yt.py
"""

import asyncio
import logging
from functools import partial
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Input,
    ListView,
    Label,
    Static,
    ProgressBar,
    Button,
)
from textual.reactive import reactive
from textual.worker import Worker

from player import AudioPlayer
from widgets import SearchResultItem, PlayerControls, ThumbnailWidget
from utils import YouTubeSearch, get_thumbnail_url

# --- Configuration ---
# Set logging to avoid polluting the TUI
logging.basicConfig(
    level=logging.ERROR,
    filename="player_debug.log"
)

# --- Main Application ---


class YTPlayerApp(App):
    """Main YouTube audio player application."""

    CSS_PATH = Path(__file__).parent / "css" / "styles.tcss"

    BINDINGS = [
        ("tab", "cycle_focus", "Cycle Focus"),
        ("space", "toggle_play_pause", "Play/Pause"),
        ("left", "seek_backward", "Seek -10s"),
        ("right", "seek_forward", "Seek +10s"),
        ("ctrl+c", "quit", "Quit"),
        ("enter", "play_selected", "Play Selection"),
        ("n", "next_item", "Next"),
        ("p", "prev_item", "Previous"),
        ("s", "stop_playback", "Stop"),
        ("0", "volume_up", "Vol +"),
        ("9", "volume_down", "Vol -"),
        # Vim-style navigation (when list focused)
        ("j", "list_down", "Down"),
        ("k", "list_up", "Up"),
        ("g", "list_top", "Top"),
        ("G", "list_bottom", "Bottom"),
        ("o", "play_selected", "Play Selection"),
        ("O", "play_selected", "Play Selection"),
    ]

    player = AudioPlayer()
    current_video_id = reactive("")
    current_title = reactive("No Media Playing")
    thumb_cache: dict[str, bytes] = {}
    _searcher: YouTubeSearch | None = None
    _allow_auto_play: bool = False

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        # Left Sidebar
        with Vertical(id="sidebar"):
            yield Label("[b]Search YouTube[/b]", classes="header_label")
            yield Input(placeholder="Query...", id="search_input")
            yield ListView(id="results_list")

        # Main Area
        with Vertical(id="main_area"):
            yield ThumbnailWidget(id="thumbnail_container")
            with Horizontal(id="now_playing_row"):
                yield Label("Not Playing", id="now_playing_label")
                yield Label("Stopped", id="state_label")
            with Horizontal(id="progress_container"):
                yield Label("00:00", id="elapsed_label")
                yield ProgressBar(
                    total=100,
                    show_eta=False,
                    show_percentage=False,
                    id="progress_bar"
                )
                yield Label("0%", id="progress_label")
                yield Label("-00:00", id="remaining_label")
            yield PlayerControls()
            yield Label("", id="status_line")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize app on mount."""
        self.set_interval(0.5, self.update_progress)
        self._searcher = YouTubeSearch(max_results=30)

    # --- Actions ---

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission."""
        query = event.value
        if not query:
            return

        if getattr(self, "_search_busy", False):
            self.notify("Search already in progress.", severity="warning")
            return

        self._search_busy = True

        list_view = self.query_one("#results_list", ListView)
        list_view.clear()
        self.query_one("#status_line", Label).update(f"Searching for '{query}'...")

        # Run search in background
        self.run_worker(
            partial(self.perform_search, query),
            exclusive=True,
            exit_on_error=False
        )

    async def perform_search(self, query: str) -> None:
        """Search YouTube and populate results."""
        try:
            assert self._searcher is not None
            results = await self._searcher.search(query)

            if results:
                list_view = self.query_one("#results_list", ListView)
                for item in results:
                    list_view.append(
                        SearchResultItem(
                            title=item['title'],
                            uploader=item['uploader'],
                            video_id=item['id'],
                            thumb_url=item['thumbnail']
                        )
                    )
                self.notify("Search completed.")
                self.query_one("#status_line", Label).update("")
            else:
                self.notify("No results found.", severity="warning")
                self.query_one("#status_line", Label).update("No results found.")

        except Exception as e:
            logging.error(f"Search error: {e}")
            self.notify(f"Search failed: {e}", severity="error")
            self.query_one("#status_line", Label).update(f"Search failed: {e}")
        finally:
            self._search_busy = False

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle result selection."""
        item = event.item
        if isinstance(item, SearchResultItem) and self._allow_auto_play:
            self.play_video(item)
            self._allow_auto_play = False

    def play_video(self, item: SearchResultItem) -> None:
        """Start playing a video."""
        self.current_title = item.title_text
        self.current_video_id = item.video_id

        # Update UI
        self.query_one("#now_playing_label", Label).update(
            f"[b]{item.title_text}[/b]"
        )
        self.query_one(
            "#thumbnail_container", ThumbnailWidget
        ).update_image(item.thumb_url)
        self.query_one("#state_label", Label).update("Loading")
        self.query_one("#status_line", Label).update("")

        # Get audio stream URL in background
        self.run_worker(
            partial(self.fetch_and_play, item.video_id),
            exit_on_error=False
        )

    async def fetch_and_play(self, video_id: str) -> None:
        """Fetch audio stream URL and start playback."""
        url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }

        try:
            import yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                loop = asyncio.get_running_loop()
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )
                play_url = info['url']
                self.player.play(play_url)
                self.query_one("#state_label", Label).update("Playing")
                self.query_one("#status_line", Label).update("")

        except Exception as e:
            self.notify(f"Error fetching stream: {e}", severity="error")
            self.query_one("#state_label", Label).update("Error")
            self.query_one("#status_line", Label).update(str(e))

    # --- Controls ---

    def action_cycle_focus(self) -> None:
        """Keybinding: Cycle focus between search input and results list."""
        input_widget = self.query_one("#search_input", Input)
        list_view = self.query_one("#results_list", ListView)
        
        # Cycle between input and list only
        if self.focused == input_widget:
            list_view.focus()
        else:
            input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id
        if btn_id == "btn_play_pause":
            self.toggle_play_pause()
        elif btn_id == "btn_stop":
            self.stop_playback()
        elif btn_id == "btn_next":
            self.next_item()

    def toggle_play_pause(self) -> None:
        """Toggle play/pause state."""
        paused = self.player.pause()
        try:
            self.query_one("#btn_play_pause", Button).label = (
                "▶" if paused else "⏸"
            )
            self.query_one("#state_label", Label).update(
                "Paused" if paused else "Playing"
            )
        except Exception:
            pass

    def action_toggle_play_pause(self) -> None:
        """Keybinding: Toggle play/pause."""
        self.toggle_play_pause()

    def action_seek_forward(self) -> None:
        """Keybinding: Seek forward 10s."""
        self.player.seek(10)
        self.notify("Seek +10s", timeout=1)

    def action_seek_backward(self) -> None:
        """Keybinding: Seek backward 10s."""
        self.player.seek(-10)
        self.notify("Seek -10s", timeout=1)

    def action_volume_up(self) -> None:
        """Keybinding: Increase volume."""
        vol = self.player.change_volume(5)
        self.notify(f"Volume {int(vol)}", timeout=1)

    def action_volume_down(self) -> None:
        """Keybinding: Decrease volume."""
        vol = self.player.change_volume(-5)
        self.notify(f"Volume {int(vol)}", timeout=1)

    def action_play_selected(self) -> None:
        """Keybinding: Play selected item."""
        self.play_selected()

    def action_next_item(self) -> None:
        """Keybinding: Next item."""
        self.next_item()

    def action_prev_item(self) -> None:
        """Keybinding: Previous item."""
        self.prev_item()

    def action_stop_playback(self) -> None:
        """Keybinding: Stop playback."""
        self.stop_playback()

    def action_list_down(self) -> None:
        """Keybinding: Move selection down (vim j)."""
        self.shift_selection(1, autoplay=False)

    def action_list_up(self) -> None:
        """Keybinding: Move selection up (vim k)."""
        self.shift_selection(-1, autoplay=False)

    def action_list_top(self) -> None:
        """Keybinding: Jump to first result (vim g)."""
        list_view = self.query_one("#results_list", ListView)
        if list_view.children:
            list_view.index = 0
            list_view.action_select_cursor()

    def action_list_bottom(self) -> None:
        """Keybinding: Jump to last result (vim G)."""
        list_view = self.query_one("#results_list", ListView)
        if list_view.children:
            list_view.index = len(list_view.children) - 1
            list_view.action_select_cursor()

    def play_selected(self) -> None:
        """Play the currently selected item."""
        list_view = self.query_one("#results_list", ListView)
        if list_view.index is None and list_view.children:
            list_view.index = 0
        if list_view.index is not None:
            self._allow_auto_play = True
            list_view.action_select_cursor()

    def next_item(self) -> None:
        """Move to next item and autoplay."""
        self.shift_selection(1, autoplay=True)

    def prev_item(self) -> None:
        """Move to previous item and autoplay."""
        self.shift_selection(-1, autoplay=True)

    def shift_selection(self, delta: int, autoplay: bool = False) -> None:
        """Shift selection by delta."""
        list_view = self.query_one("#results_list", ListView)
        if list_view.children:
            idx = list_view.index or 0
            new_idx = max(0, min(len(list_view.children) - 1, idx + delta))
            list_view.index = new_idx
            if autoplay:
                self._allow_auto_play = True
            list_view.action_select_cursor()

    def stop_playback(self) -> None:
        """Stop playback and reset UI."""
        self.player.stop()
        self.query_one("#progress_bar", ProgressBar).update(progress=0)
        self.query_one("#progress_label", Label).update("0%")
        self.query_one("#elapsed_label", Label).update("00:00")
        self.query_one("#remaining_label", Label).update("-00:00")
        self.query_one("#now_playing_label", Label).update("Stopped")
        self.query_one("#state_label", Label).update("Stopped")

    def _fmt_time(self, seconds: float | None) -> str:
        """Format seconds as MM:SS or HH:MM:SS."""
        if seconds is None or seconds < 0:
            return "00:00"
        secs = int(seconds)
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def update_progress(self) -> None:
        """Update progress bar and time labels."""
        try:
            if getattr(self.player.mpv, "core_idle", False):
                return

            curr = self.player.get_time_pos()
            total = self.player.get_duration()

            if not total or total <= 0:
                total = max(curr, 1)

            if total > 0:
                percent = int((curr / total) * 100)
                remaining = max(total - curr, 0)

                self.query_one("#progress_bar", ProgressBar).update(
                    total=total,
                    progress=curr
                )
                self.query_one("#progress_label", Label).update(f"{percent}%")
                self.query_one("#elapsed_label", Label).update(
                    self._fmt_time(curr)
                )
                self.query_one("#remaining_label", Label).update(
                    f"-{self._fmt_time(remaining)}"
                )

        except Exception:
            pass


def main() -> None:
    """Entry point."""
    app = YTPlayerApp()
    app.run()


if __name__ == "__main__":
    main()

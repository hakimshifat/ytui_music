import sys
import shutil
import asyncio
from functools import partial
import logging
from functools import partial
from io import BytesIO

import mpv
import requests
import yt_dlp
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, ListView, ListItem, Label, Static, ProgressBar, Button
from textual.reactive import reactive
from textual.message import Message
from textual.worker import Worker
from textual_image.widget import Image as TextualImage

# --- Configuration ---
# Set logging to avoid polluting the TUI
logging.basicConfig(level=logging.ERROR, filename="player_debug.log")

class AudioPlayer:
    """Singleton wrapper for MPV."""
    def __init__(self):
        # vo='null' ensures no video window pops up
        # ytdl=True allows mpv to directly handle some URLs if needed, 
        # but we will feed it direct play URLs from yt-dlp for speed.
        self.mpv = mpv.MPV(vo='null', ytdl=True)
        self.mpv.volume = 80
    
    def play(self, url):
        self.mpv.play(url)
    
    def pause(self):
        self.mpv.pause = not self.mpv.pause
        return self.mpv.pause

    def stop(self):
        self.mpv.stop()
        
    def seek(self, seconds):
        if self.mpv.core_idle: return
        self.mpv.seek(seconds)

    def get_time_pos(self):
        return self.mpv.time_pos or 0

    def get_duration(self):
        return self.mpv.duration or 1

    def change_volume(self, delta: int):
        """Adjust volume by delta and clamp to 0-150."""
        current = self.mpv.volume or 0
        new_val = max(0, min(150, current + delta))
        self.mpv.volume = new_val
        return new_val

# --- Widgets ---

class SearchResultItem(ListItem):
    """Custom List Item to store video metadata."""
    def __init__(self, title: str, uploader: str, video_id: str, thumb_url: str):
        super().__init__()
        self.add_class("result_item")
        self.title_text = title
        self.uploader = uploader
        self.video_id = video_id
        self.thumb_url = thumb_url
        self.thumb_box = Static("Loading...", classes="thumb_box")

    def compose(self) -> ComposeResult:
        with Horizontal(classes="list_item_row"):
            yield self.thumb_box
            yield Label(f"[b]{self.title_text}[/b]\n[dim]{self.uploader}[/dim]", classes="list_item_label")

    async def on_mount(self) -> None:
        # Load thumbnail per search result in the background
        self.run_worker(partial(self._download_thumb), exit_on_error=False)

    async def _download_thumb(self):
        if not self.thumb_url:
            self.thumb_box.update("No thumb")
            return
        try:
            cache = getattr(self.app, "thumb_cache", {})
            content: bytes | None = cache.get(self.video_id)
            if content is None:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(None, lambda: requests.get(self.thumb_url, timeout=10))
                if response.status_code == 200:
                    content = response.content
                    cache[self.video_id] = content
            if content:
                img_data = BytesIO(content)
                img_widget = TextualImage(img_data)
                img_widget.styles.width = 12
                img_widget.styles.height = 7

                for child in list(self.thumb_box.children):
                    await child.remove()
                self.thumb_box.update("")
                await self.thumb_box.mount(img_widget)
            else:
                self.thumb_box.update("No thumb")
        except Exception as e:
            logging.error(f"Inline thumbnail error: {e}")
            self.thumb_box.update("No thumb")

class PlayerControls(Static):
    """Container for player buttons."""
    def compose(self) -> ComposeResult:
        with Horizontal(classes="controls_bar"):
            yield Button("⏮", id="btn_prev", variant="primary")
            yield Button("⏯", id="btn_play_pause", variant="warning")
            yield Button("⏭", id="btn_next", variant="primary")
            yield Button("Stop", id="btn_stop", variant="error")

class ThumbnailWidget(Container):
    """Handles downloading and displaying the thumbnail."""
    
    def update_image(self, url: str):
        # Run in a worker to avoid freezing UI during download
        # exit_on_error=False so a failed download doesn't kill the app
        self.app.run_worker(partial(self._download_and_set, url), exit_on_error=False)

    async def _download_and_set(self, url: str):
        if not url:
            return
        
        try:
            # Fetch image
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, requests.get, url)
            
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                
                # Clear existing image
                for child in self.children:
                    await child.remove()
                
                # Create new Image widget from textual-image
                # It automatically detects Sixel/Kitty/Block support
                img_widget = TextualImage(img_data)
                img_widget.styles.width = "100%"
                img_widget.styles.height = "100%"
                
                await self.mount(img_widget)
        except Exception as e:
            logging.error(f"Thumbnail error: {e}")

# --- Main Application ---

class YTPlayerApp(App):
    BINDINGS = [
        ("space", "toggle_play_pause", "Play/Pause"),
        ("left", "seek_backward", "Seek -10s"),
        ("right", "seek_forward", "Seek +10s"),
    ]

    CSS = """
    Screen { layout: grid; grid-size: 2; grid-columns: 32% 68%; }
    
    /* Left Sidebar: Search */
    #sidebar { row-span: 2; background: $surface; border-right: solid $primary; min-width: 36; max-width: 48; }
    #search_input { dock: top; margin: 1; }
    #results_list { height: 1fr; align: left top; padding: 0 1; overflow-y: auto; }
    .result_item { height: auto; min-height: 5; max-height: 7; padding: 0; border-bottom: solid $background 10%; }
    .result_item:hover { background: $background 20%; }
    .result_item:focus { outline: solid $accent; }
    .list_item_row { align: left top; padding: 1 0; width: 100%; }
    .thumb_box { width: 12; min-width: 12; height: 7; border: solid $accent 10%; align: center middle; overflow: hidden; margin-right: 1; }
    .list_item_label { padding: 0 1; }
    
    /* Right Content: Player */
    #main_area { layout: vertical; padding: 2; align: center middle; }
    
    #thumbnail_container { 
        height: 60%; 
        width: 100%; 
        border: solid $accent; 
        margin-bottom: 2;
        align: center middle;
    }
    
    #now_playing_row { width: 100%; align: left middle; }
    #now_playing_label { text-align: left; margin-bottom: 0; color: $secondary-lighten-2; width: 1fr; }
    #state_label { color: $primary; }

    #progress_container { width: 100%; margin-bottom: 2; align: center middle; }
    #progress_bar { width: 1fr; }
    #progress_label { min-width: 6; text-align: right; }
    #elapsed_label { min-width: 6; text-align: left; }
    #remaining_label { min-width: 7; text-align: right; }
    
    .controls_bar { align: center middle; height: auto; }
    Button { margin: 0 1; }
    #status_line { width: 100%; color: $warning; min-height: 1; }
    """

    player = AudioPlayer()
    current_video_id = reactive("")
    current_title = reactive("No Media Playing")
    thumb_cache: dict[str, bytes] = {}
    BINDINGS = [
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
    ]
    
    def compose(self) -> ComposeResult:
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
                yield ProgressBar(total=100, show_eta=False, show_percentage=False, id="progress_bar")
                yield Label("0%", id="progress_label")
                yield Label("-00:00", id="remaining_label")
            yield PlayerControls()
            yield Label("", id="status_line")
        
        yield Footer()

    def on_mount(self):
        self.set_interval(0.5, self.update_progress)

    # --- Actions ---

    async def on_input_submitted(self, event: Input.Submitted):
        """Handle Search."""
        query = event.value
        if not query: return
        if getattr(self, "_search_busy", False):
            self.notify("Search already in progress.", severity="warning")
            return
        self._search_busy = True
        
        list_view = self.query_one("#results_list", ListView)
        list_view.clear()
        self.query_one("#status_line", Label).update(f"Searching for '{query}'...")
        
        # Run search in background
        # exit_on_error=False so search errors surface via notify without exiting
        self.run_worker(partial(self.perform_search, query), exclusive=True, exit_on_error=False)

    async def perform_search(self, query):
        """Uses yt-dlp to fetch JSON metadata."""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,          # Don't download video, just metadata
            'skip_download': True,
        }
        search_term = f"ytsearch15:{query}"
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Running synchronous ydl in a thread
                loop = asyncio.get_running_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_term, download=False))
                
                if info.get('entries'):
                    list_view = self.query_one("#results_list", ListView)
                    
                    for entry in info['entries']:
                        title = entry.get('title', 'Unknown')
                        uploader = entry.get('uploader', 'Unknown')
                        vid_id = entry.get('id')
                        
                        # yt-dlp flat extraction sometimes lacks thumbnails, construct high-res URL manually
                        thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                        
                        list_view.append(SearchResultItem(title, uploader, vid_id, thumb))
                    
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

    async def on_list_view_selected(self, event: ListView.Selected):
        """Play selected item."""
        item = event.item
        if isinstance(item, SearchResultItem):
            self.play_video(item)

    def play_video(self, item: SearchResultItem):
        self.current_title = item.title_text
        self.current_video_id = item.video_id
        
        # Update UI
        self.query_one("#now_playing_label", Label).update(f"[b]{item.title_text}[/b]")
        self.query_one("#thumbnail_container", ThumbnailWidget).update_image(item.thumb_url)
        self.query_one("#state_label", Label).update("Loading")
        self.query_one("#status_line", Label).update("")
        
        # Get Audio Stream URL
        # exit_on_error=False so playback failures don't exit the app
        self.run_worker(partial(self.fetch_and_play, item.video_id), exit_on_error=False)

    async def fetch_and_play(self, video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                loop = asyncio.get_running_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                play_url = info['url']
                self.player.play(play_url)
                self.query_one("#state_label", Label).update("Playing")
                self.query_one("#status_line", Label).update("")
        except Exception as e:
            self.notify(f"Error fetching stream: {e}", severity="error")
            self.query_one("#state_label", Label).update("Error")
            self.query_one("#status_line", Label).update(str(e))

    # --- Controls ---

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "btn_play_pause":
            self.toggle_play_pause()
        elif btn_id == "btn_stop":
            self.stop_playback()
        elif btn_id == "btn_next":
            self.next_item()

    def toggle_play_pause(self):
        paused = self.player.pause()
        try:
            self.query_one("#btn_play_pause", Button).label = "▶" if paused else "⏸"
            self.query_one("#state_label", Label).update("Paused" if paused else "Playing")
        except Exception:
            pass

    def action_toggle_play_pause(self):
        self.toggle_play_pause()

    def action_seek_forward(self):
        self.player.seek(10)
        self.notify("Seek +10s", timeout=1)

    def action_seek_backward(self):
        self.player.seek(-10)
        self.notify("Seek -10s", timeout=1)

    def action_volume_up(self):
        vol = self.player.change_volume(5)
        self.notify(f"Volume {int(vol)}", timeout=1)

    def action_volume_down(self):
        vol = self.player.change_volume(-5)
        self.notify(f"Volume {int(vol)}", timeout=1)

    def action_play_selected(self):
        self.play_selected()

    def action_next_item(self):
        self.next_item()

    def action_prev_item(self):
        self.prev_item()

    def action_stop_playback(self):
        self.stop_playback()

    def play_selected(self):
        list_view = self.query_one("#results_list", ListView)
        if list_view.index is None and list_view.children:
            list_view.index = 0
        if list_view.index is not None:
            list_view.action_select_cursor()

    def next_item(self):
        self.shift_selection(1, autoplay=True)

    def prev_item(self):
        self.shift_selection(-1, autoplay=True)

    def shift_selection(self, delta: int, autoplay: bool = False):
        list_view = self.query_one("#results_list", ListView)
        if list_view.children:
            idx = list_view.index or 0
            new_idx = max(0, min(len(list_view.children) - 1, idx + delta))
            list_view.index = new_idx
            list_view.action_select_cursor()
            if autoplay:
                item = list_view.children[new_idx]
                if isinstance(item, SearchResultItem):
                    self.play_video(item)

    def stop_playback(self):
        self.player.stop()
        self.query_one("#progress_bar", ProgressBar).update(progress=0)
        self.query_one("#progress_label", Label).update("0%")
        self.query_one("#elapsed_label", Label).update("00:00")
        self.query_one("#remaining_label", Label).update("-00:00")
        self.query_one("#now_playing_label", Label).update("Stopped")
        self.query_one("#state_label", Label).update("Stopped")

    def _fmt_time(self, seconds: float | None) -> str:
        if seconds is None or seconds < 0:
            return "00:00"
        secs = int(seconds)
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def update_progress(self):
        """Updates progress bar."""
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
                self.query_one("#progress_bar", ProgressBar).update(total=total, progress=curr)
                self.query_one("#progress_label", Label).update(f"{percent}%")
                self.query_one("#elapsed_label", Label).update(self._fmt_time(curr))
                self.query_one("#remaining_label", Label).update(f"-{self._fmt_time(remaining)}")
        except Exception:
            pass

if __name__ == "__main__":
    app = YTPlayerApp()
    app.run()

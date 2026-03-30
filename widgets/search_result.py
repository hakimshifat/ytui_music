"""Search result list item widget with thumbnail support."""

from functools import partial
from io import BytesIO

from textual.widgets import Static, Label, ListView, ListItem
from textual.containers import Horizontal
from textual_image.widget import Image as TextualImage


class SearchResultItem(ListItem):
    """Custom List Item to store video metadata and display thumbnail.
    
    Attributes:
        title_text: Video title
        uploader: Channel name
        video_id: YouTube video ID
        thumb_url: Thumbnail image URL
    """
    
    def __init__(self, title: str, uploader: str, video_id: str, thumb_url: str):
        super().__init__()
        self.add_class("result_item")
        self.title_text = title
        self.uploader = uploader
        self.video_id = video_id
        self.thumb_url = thumb_url
        self.thumb_box = Static("Loading...", classes="thumb_box")

    def compose(self) -> ListView.ComposeResult:
        with Horizontal(classes="list_item_row"):
            yield self.thumb_box
            yield Label(f"[b]{self.title_text}[/b]\n[dim]{self.uploader}[/dim]", classes="list_item_label")

    async def on_mount(self) -> None:
        # Load thumbnail per search result in the background
        self.run_worker(partial(self._download_thumb), exit_on_error=False)

    async def _download_thumb(self):
        """Download and display thumbnail with caching."""
        if not self.thumb_url:
            self.thumb_box.update("No thumb")
            return
        
        try:
            cache = getattr(self.app, "thumb_cache", {})
            content: bytes | None = cache.get(self.video_id)
            
            if content is None:
                import asyncio
                import requests
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.get(self.thumb_url, timeout=10)
                )
                if response.status_code == 200:
                    content = response.content
                    cache[self.video_id] = content
            
            if content:
                img_data = BytesIO(content)
                img_widget = TextualImage(img_data)
                img_widget.styles.width = 8
                img_widget.styles.height = 3

                for child in list(self.thumb_box.children):
                    await child.remove()
                self.thumb_box.update("")
                await self.thumb_box.mount(img_widget)
            else:
                self.thumb_box.update("No thumb")
        except Exception as e:
            import logging
            logging.error(f"Inline thumbnail error: {e}")
            self.thumb_box.update("No thumb")

"""Thumbnail widget for displaying video thumbnails."""

from functools import partial
from io import BytesIO

from textual.widgets import Static
from textual.containers import Container
from textual_image.widget import Image as TextualImage


class ThumbnailWidget(Container):
    """Handles downloading and displaying the thumbnail.
    
    Downloads thumbnails asynchronously to avoid blocking the UI.
    """

    def update_image(self, url: str) -> None:
        """Start async thumbnail download.
        
        Args:
            url: Thumbnail image URL
        """
        self.app.run_worker(partial(self._download_and_set, url), exit_on_error=False)

    async def _download_and_set(self, url: str):
        """Download and display thumbnail."""
        if not url:
            return

        try:
            import asyncio
            import requests
            
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, requests.get, url)

            if response.status_code == 200:
                img_data = BytesIO(response.content)

                # Clear existing image
                for child in self.children:
                    await child.remove()

                # Create new Image widget from textual-image
                img_widget = TextualImage(img_data)
                img_widget.styles.width = "100%"
                img_widget.styles.height = "100%"

                await self.mount(img_widget)
        except Exception as e:
            import logging
            logging.error(f"Thumbnail error: {e}")

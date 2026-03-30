"""Thumbnail fetching and caching utilities."""

import asyncio
from io import BytesIO

import requests


class ThumbnailCache:
    """In-memory cache for video thumbnails.
    
    Caches thumbnail bytes by video ID for the session duration.
    """
    
    def __init__(self):
        self._cache: dict[str, bytes] = {}

    def get(self, video_id: str) -> bytes | None:
        """Get cached thumbnail for video ID."""
        return self._cache.get(video_id)

    def set(self, video_id: str, content: bytes) -> None:
        """Cache thumbnail content."""
        self._cache[video_id] = content

    def clear(self) -> None:
        """Clear all cached thumbnails."""
        self._cache.clear()


async def fetch_thumbnail(url: str, timeout: int = 10) -> bytes | None:
    """Fetch thumbnail image from URL.
    
    Args:
        url: Thumbnail image URL
        timeout: Request timeout in seconds
        
    Returns:
        Image bytes or None if fetch fails
    """
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(url, timeout=timeout)
        )
        
        if response.status_code == 200:
            return response.content
    except Exception:
        pass
    
    return None


def get_thumbnail_url(video_id: str) -> str:
    """Generate YouTube thumbnail URL for video ID.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        High-quality thumbnail URL
    """
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

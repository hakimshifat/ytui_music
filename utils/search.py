"""YouTube search functionality using yt-dlp."""

import asyncio
from typing import Any

import yt_dlp


class YouTubeSearch:
    """YouTube search using yt-dlp.
    
    Provides methods to search YouTube and extract video metadata.
    """
    
    def __init__(self, max_results: int = 30):
        """Initialize search with result limit.
        
        Args:
            max_results: Maximum number of results to fetch (default: 30)
        """
        self.max_results = max_results
        self._opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
        }

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search YouTube for videos.
        
        Args:
            query: Search query string
            
        Returns:
            List of video metadata dicts with keys:
                - title: Video title
                - uploader: Channel name
                - id: YouTube video ID
                - thumbnail: Thumbnail URL
                
        Raises:
            Exception: If search fails
        """
        search_term = f"ytsearch{self.max_results}:{query}"
        
        loop = asyncio.get_running_loop()
        
        def _extract():
            with yt_dlp.YoutubeDL(self._opts) as ydl:
                return ydl.extract_info(search_term, download=False)
        
        info = await loop.run_in_executor(None, _extract)
        
        results = []
        if info.get('entries'):
            for entry in info['entries']:
                vid_id = entry.get('id')
                results.append({
                    'title': entry.get('title', 'Unknown'),
                    'uploader': entry.get('uploader', 'Unknown'),
                    'id': vid_id,
                    'thumbnail': get_thumbnail_url(vid_id),
                })
        
        return results


def get_thumbnail_url(video_id: str) -> str:
    """Generate YouTube thumbnail URL for video ID.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        High-quality thumbnail URL
    """
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

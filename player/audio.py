"""Audio player implementation using python-mpv."""

import mpv


class AudioPlayer:
    """Singleton wrapper for MPV audio playback.
    
    Provides a simple interface for playing, pausing, stopping,
    seeking, and volume control for YouTube audio streams.
    """
    
    def __init__(self):
        # vo='null' ensures no video window pops up
        # ytdl=True allows mpv to directly handle some URLs if needed
        self.mpv = mpv.MPV(vo='null', ytdl=True)
        self.mpv.volume = 80

    def play(self, url: str) -> None:
        """Play audio from URL."""
        self.mpv.play(url)

    def pause(self) -> bool:
        """Toggle pause state. Returns True if paused."""
        self.mpv.pause = not self.mpv.pause
        return self.mpv.pause

    def stop(self) -> None:
        """Stop playback."""
        self.mpv.stop()

    def seek(self, seconds: int) -> None:
        """Seek forward/backward by seconds."""
        if self.mpv.core_idle:
            return
        self.mpv.seek(seconds)

    def get_time_pos(self) -> float:
        """Get current playback position in seconds."""
        return self.mpv.time_pos or 0

    def get_duration(self) -> float:
        """Get total duration in seconds."""
        return self.mpv.duration or 1

    def change_volume(self, delta: int) -> float:
        """Adjust volume by delta and clamp to 0-150.
        
        Args:
            delta: Volume change amount (+/-)
            
        Returns:
            New volume level
        """
        current = self.mpv.volume or 0
        new_val = max(0, min(150, current + delta))
        self.mpv.volume = new_val
        return new_val

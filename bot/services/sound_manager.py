import os
from typing import Optional

from bot.utils.constants import SOUND_FORMATS


class SoundManager:
    """Manages sound files and caching."""

    def __init__(self, sounds_dir: str):
        self.sounds_dir = sounds_dir
        self._cached_sounds: Optional[dict] = None

    def find_sound(self, filename: str) -> Optional[str]:
        """
        Find a sound file by name (without extension).
        
        Args:
            filename: Name of the sound file without extension
            
        Returns:
            Full path to the sound file if found, None otherwise
        """
        return next(
            (os.path.join(self.sounds_dir, file) for file in os.listdir(self.sounds_dir)
             if os.path.splitext(file)[0] == filename), None)

    def get_sounds_dict(self, use_cache: bool = True) -> dict:
        """
        Get dictionary of all available sounds.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary mapping sound names to their file paths
        """
        if use_cache and self._cached_sounds is not None:
            return self._cached_sounds

        if not os.path.isdir(self.sounds_dir):
            raise ValueError(f"Path is not valid: {self.sounds_dir}")

        sound_dict = {}
        files = [f for f in os.listdir(self.sounds_dir) if os.path.isfile(os.path.join(self.sounds_dir, f))]
        sorted_files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(self.sounds_dir, f)))
        for sound in sorted_files:
            name_without_extension, _ = os.path.splitext(sound)
            sound_dict[name_without_extension] = os.path.join(self.sounds_dir, sound)
        self._cached_sounds = sound_dict
        return sound_dict

    def invalidate_cache(self) -> None:
        """Invalidate the sounds cache."""
        self._cached_sounds = None

    def sound_size(self, sound_name: str) -> int:
        """
        Get the size of a sound file.
        
        Args:
            sound_name: Name of the sound
            
        Returns:
            Size in bytes
        """
        sound_path = self.find_sound(sound_name)
        return os.path.getsize(sound_path)

    @staticmethod
    def is_supported_format(filename: str) -> bool:
        """
        Check if a file format is supported.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if format is supported
        """
        return filename.lower().endswith(tuple(SOUND_FORMATS))

import os
import math
from typing import Optional

import yt_dlp
from pydub import AudioSegment

from bot.utils.time_parser import time_to_seconds


class AudioProcessor:
    """Handles audio processing operations."""

    def __init__(self, sounds_dir: str):
        self.sounds_dir = sounds_dir

    def cut_audio(self, save_path: str, start_time: Optional[str] = None,
                  end_time: Optional[str] = None) -> None:
        """
        Cut audio file to specified time range.
        
        Args:
            save_path: Path to the audio file
            start_time: Start time (hh:mm:ss, mm:ss or ss)
            end_time: End time (hh:mm:ss, mm:ss or ss)
        """
        audio = AudioSegment.from_file(save_path)

        start_ms = int(time_to_seconds(start_time) * 1000) if start_time is not None else 0
        end_ms = int(time_to_seconds(end_time) * 1000) if end_time is not None else len(audio)

        cut_audio = audio[start_ms:end_ms]
        cut_audio.export(save_path, format=save_path.rsplit('.', 1)[-1])

    def download_youtube_audio(self, url: str, sound_name: str, start_time: Optional[str],
                               end_time: Optional[str], extension: str = "opus",
                               output_dir: Optional[str] = None) -> str:
        """
        Download audio from YouTube video.
        
        Args:
            url: YouTube video URL
            sound_name: Name for the saved sound
            start_time: Start time for extraction (hh:mm:ss, mm:ss or ss)
            end_time: End time for extraction (hh:mm:ss, mm:ss or ss)
            extension: Audio format extension
            output_dir: Directory to save the file (defaults to sounds_dir)

        Returns:
            Path to the downloaded audio file
        """
        dest_dir = output_dir or self.sounds_dir
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(dest_dir, f"{sound_name}.%(ext)s"),
            "download_ranges": lambda info_dict, yt_instance: [
                {'start_time': time_to_seconds(start_time) if start_time else 0,
                 'end_time': time_to_seconds(end_time) if end_time else 1e6,
                 'title': 'first_section'},
            ],
            "force_keyframes_at_cuts": True,
            "noplaylist": True,
            "playlist_items": "1",
            "socket_timeout": 30,
            "retries": 2,
            "extractor_retries": 2,
            "file_access_retries": 2,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": extension,
                "preferredquality": "6",
            }],
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return os.path.join(dest_dir, f"{sound_name}.{extension}")

    def apply_volume(self, output_path: str, volume_percentage: int, source_path: Optional[str] = None) -> None:
        """Apply absolute volume percentage and export to output path.

        Args:
            output_path: Destination path to overwrite with new volume
            volume_percentage: Target volume in percentage (0 = mute, 100 = unchanged)
            source_path: Optional source path. If omitted, output_path is used as source.
        """
        volume_percentage = max(0, volume_percentage)
        source = source_path or output_path

        audio = AudioSegment.from_file(source)
        if volume_percentage == 0:
            processed = audio - 120
        else:
            gain_db = 20 * math.log10(volume_percentage / 100.0)
            processed = audio.apply_gain(gain_db)

        extension = os.path.splitext(output_path)[1].lstrip(".")
        processed.export(output_path, format=extension)


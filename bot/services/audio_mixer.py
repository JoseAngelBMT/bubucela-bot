import audioop
import logging
import threading

import discord

logger = logging.getLogger(__name__)


class AudioMixer(discord.AudioSource):
    """Mixes up to MAX_SOURCES PCM AudioSources simultaneously into one stream.

    All sources must produce raw 16-bit little-endian stereo PCM at 48 kHz,
    which is exactly what discord.FFmpegPCMAudio returns.
    """

    MAX_SOURCES: int = 5

    def __init__(self) -> None:
        self._sources: list[discord.AudioSource] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_source(self, source: discord.AudioSource) -> bool:
        """Add a source to the mix.

        Returns True if added, False if the limit has been reached.
        """
        with self._lock:
            if len(self._sources) >= self.MAX_SOURCES:
                return False
            self._sources.append(source)
            return True

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._sources)

    # ------------------------------------------------------------------
    # discord.AudioSource interface
    # ------------------------------------------------------------------

    def read(self) -> bytes:
        with self._lock:
            if not self._sources:
                return b""

            finished: list[discord.AudioSource] = []
            buffers: list[bytes] = []

            for source in self._sources:
                data = source.read()
                if not data:
                    finished.append(source)
                else:
                    buffers.append(data)

            for s in finished:
                self._sources.remove(s)
                try:
                    s.cleanup()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

            if not buffers:
                return b""

            # Mix all PCM buffers using audioop (C-backed, fast).
            # audioop.add uses signed 16-bit arithmetic (width=2).
            mixed = buffers[0]
            for buf in buffers[1:]:
                # Pad to same length in the unlikely case of size mismatch
                if len(buf) != len(mixed):
                    length = max(len(mixed), len(buf))
                    mixed = mixed.ljust(length, b"\x00")
                    buf = buf.ljust(length, b"\x00")
                mixed = audioop.add(mixed, buf, 2)

            return mixed

    def is_opus(self) -> bool:
        return False

    def cleanup(self) -> None:
        with self._lock:
            for source in self._sources:
                try:
                    source.cleanup()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
            self._sources.clear()


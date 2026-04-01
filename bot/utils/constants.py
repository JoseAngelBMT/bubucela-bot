"""Constants used throughout the bot."""

import os
from pathlib import Path

# Audio formats supported
SOUND_FORMATS = [".mp3", ".wav", ".ogg", ".opus"]

# Base static directory.
# Priority: STATIC_DIR env var -> /static (Docker volume) -> local ./static.
_STATIC_DIR = Path(os.getenv("STATIC_DIR") or ("/static" if Path("/static").exists() else "static"))

# User sounds JSON path
USER_SOUNDS_JSON_PATH = str(_STATIC_DIR / "user_sounds.json")

# Non-destructive volume modifications metadata/backups
MODIFIED_SOUNDS_JSON_PATH = str(_STATIC_DIR / "modified_sounds.json")
MODIFIED_SOUNDS_BACKUP_DIR = str(_STATIC_DIR / "backups")

# Sound groups metadata
SOUND_GROUPS_JSON_PATH = str(_STATIC_DIR / "sound_groups.json")

# Soundboard configuration
SOUNDS_PER_PAGE = 20

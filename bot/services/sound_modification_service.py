import json
import os
import shutil
from datetime import datetime, timezone

from bot.utils.constants import MODIFIED_SOUNDS_BACKUP_DIR, MODIFIED_SOUNDS_JSON_PATH


class SoundModificationService:
    """Tracks non-destructive sound modifications and backup/restore operations."""

    def __init__(self, metadata_path: str = MODIFIED_SOUNDS_JSON_PATH, backup_dir: str = MODIFIED_SOUNDS_BACKUP_DIR):
        self.metadata_path = metadata_path
        self.backup_dir = backup_dir

    def _load_metadata(self) -> dict:
        if not os.path.exists(self.metadata_path):
            return {}

        with open(self.metadata_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}

        if isinstance(data, dict):
            return data
        return {}

    def _save_metadata(self, data: dict) -> None:
        os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
        with open(self.metadata_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def ensure_backup(self, sound_name: str, sound_path: str) -> str:
        """Create the original backup once and return backup path."""
        metadata = self._load_metadata()
        existing = metadata.get(sound_name)
        if existing and os.path.exists(existing.get("backup_path", "")):
            return existing["backup_path"]

        os.makedirs(self.backup_dir, exist_ok=True)
        extension = os.path.splitext(sound_path)[1]
        backup_filename = f"{sound_name}{extension}"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        # Avoid collisions if a backup file with same name already exists.
        if os.path.exists(backup_path):
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            backup_filename = f"{sound_name}_{timestamp}{extension}"
            backup_path = os.path.join(self.backup_dir, backup_filename)

        shutil.copy2(sound_path, backup_path)
        metadata[sound_name] = {
            "sound_path": sound_path,
            "backup_path": backup_path,
            "modified_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_metadata(metadata)
        return backup_path

    def mark_modified(self, sound_name: str, sound_path: str) -> None:
        """Ensure metadata exists and update timestamp after applying a modification."""
        metadata = self._load_metadata()
        entry = metadata.get(sound_name)
        if not entry:
            return

        entry["sound_path"] = sound_path
        entry["modified_at"] = datetime.now(timezone.utc).isoformat()
        metadata[sound_name] = entry
        self._save_metadata(metadata)

    def list_modified_sounds(self) -> dict:
        """Return modified sounds as {sound_name: sound_path} and prune broken entries."""
        metadata = self._load_metadata()
        modified_sounds = {}
        dirty = False

        for sound_name, entry in metadata.items():
            sound_path = entry.get("sound_path")
            backup_path = entry.get("backup_path")
            if sound_path and backup_path and os.path.exists(sound_path) and os.path.exists(backup_path):
                modified_sounds[sound_name] = sound_path
            else:
                dirty = True

        if dirty:
            valid = {
                name: metadata[name]
                for name in modified_sounds
            }
            self._save_metadata(valid)

        return modified_sounds

    def restore_sound(self, sound_name: str) -> bool:
        """Restore one sound from backup and clear its metadata/backup."""
        metadata = self._load_metadata()
        entry = metadata.get(sound_name)
        if not entry:
            return False

        sound_path = entry.get("sound_path")
        backup_path = entry.get("backup_path")
        if not sound_path or not backup_path or not os.path.exists(backup_path):
            return False

        os.makedirs(os.path.dirname(sound_path), exist_ok=True)
        shutil.copy2(backup_path, sound_path)
        if os.path.exists(backup_path):
            os.remove(backup_path)

        del metadata[sound_name]
        self._save_metadata(metadata)
        return True

    def clear_sound_tracking(self, sound_name: str) -> None:
        """Remove tracking and backup for a sound (used when deleting/replacing sounds)."""
        metadata = self._load_metadata()
        entry = metadata.pop(sound_name, None)
        if entry:
            backup_path = entry.get("backup_path")
            if backup_path and os.path.exists(backup_path):
                os.remove(backup_path)
            self._save_metadata(metadata)


import json
import os

from bot.utils.constants import SOUND_GROUPS_JSON_PATH


class SoundGroupService:
    """Persists named groups of sound names."""

    @staticmethod
    def load_groups() -> dict[str, list[str]]:
        if os.path.exists(SOUND_GROUPS_JSON_PATH):
            with open(SOUND_GROUPS_JSON_PATH, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                    if isinstance(data, dict):
                        return {
                            str(group): [str(sound) for sound in sounds]
                            for group, sounds in data.items()
                            if isinstance(sounds, list)
                        }
                except json.JSONDecodeError:
                    return {}
        return {}

    @staticmethod
    def save_group(group_name: str, sound_names: list[str]) -> None:
        groups = SoundGroupService.load_groups()
        groups[group_name] = sound_names
        SoundGroupService._write_groups(groups)

    @staticmethod
    def delete_group(group_name: str) -> bool:
        groups = SoundGroupService.load_groups()
        if group_name not in groups:
            return False
        del groups[group_name]
        SoundGroupService._write_groups(groups)
        return True

    @staticmethod
    def list_groups() -> list[str]:
        return sorted(SoundGroupService.load_groups().keys())

    @staticmethod
    def _write_groups(groups: dict[str, list[str]]) -> None:
        os.makedirs(os.path.dirname(SOUND_GROUPS_JSON_PATH), exist_ok=True)
        with open(SOUND_GROUPS_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(groups, file, indent=4, ensure_ascii=False)


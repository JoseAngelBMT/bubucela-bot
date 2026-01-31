import json
import os

from bot.utils.constants import USER_SOUNDS_JSON_PATH


class UserSoundService:
    """Manages user sound preferences persistence."""

    @staticmethod
    def load_user_sounds() -> dict:
        """
        Load user sound preferences from JSON file.
        
        Returns:
            Dictionary mapping user IDs to their chosen sounds
        """
        if os.path.exists(USER_SOUNDS_JSON_PATH):
            with open(USER_SOUNDS_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_user_sound(user_id: str, sound_name: str) -> None:
        """
        Save a user's sound preference.
        
        Args:
            user_id: Discord user ID
            sound_name: Name of the sound to associate with the user
        """
        data = {}
        if os.path.exists(USER_SOUNDS_JSON_PATH):
            with open(USER_SOUNDS_JSON_PATH, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data[user_id] = sound_name
        with open(USER_SOUNDS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def clear_user_sound(user_id: str) -> bool:
        """
        Clear a user's sound preference.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if sound was cleared, False if user had no sound set
        """
        user_sounds = UserSoundService.load_user_sounds()
        if user_id in user_sounds:
            del user_sounds[user_id]
            with open(USER_SOUNDS_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(user_sounds, f, indent=4)
            return True
        return False

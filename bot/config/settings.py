from dotenv import dotenv_values


class Settings:
    """Configuration manager for the bot."""

    def __init__(self, env_path: str = ".env"):
        self._config = dotenv_values(env_path)

    @property
    def discord_token(self) -> str:
        return self._config["DISCORD_TOKEN"]

    @property
    def discord_prefix(self) -> str:
        return self._config["DISCORD_PREFIX"]

    @property
    def sounds_dir(self) -> str:
        return self._config["SOUNDS_DIR"]

    @property
    def max_sounds(self) -> int:
        return int(self._config["MAX_SOUNDS"])

    @property
    def max_file_size_mb(self) -> int:
        return int(self._config["MAX_FILE_SIZE_MB"])

    def get(self, key: str, default=None):
        return self._config.get(key, default)


settings = Settings()

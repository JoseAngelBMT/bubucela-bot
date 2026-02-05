"""Main entry point for the Discord bot."""
from bot.bot import DiscordBot
from bot.config.settings import settings
import logging.config
import json

def set_logger():
    """Configure logger for the application."""

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "estandar": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "consola": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "estandar",
            },
            "archivo": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "estandar",
                "filename": "app.log",
                "maxBytes": 10485760, # 10MB
                "backupCount": 3,
            },
        },
        "root": {
            "handlers": ["consola", "archivo"],
            "level": "DEBUG",
        },
    }
    logging.config.dictConfig(config)


def main():
    """Run the bot."""
    try:
        bot = DiscordBot()
        bot.run(settings.discord_token)
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    set_logger()
    main()

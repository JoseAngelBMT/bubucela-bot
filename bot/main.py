import logging.config

from bot.bot import DiscordBot
from bot.config.settings import settings


def set_logger():
    """Configure logger for the application."""

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": "app.log",
                "maxBytes": 10485760, # 10MB
                "backupCount": 3,
            },
        },
        "root": {
            "handlers": ["console", "file"],
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

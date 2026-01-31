"""Main entry point for the Discord bot."""
from bot.bot import DiscordBot
from bot.config.settings import settings


def main():
    """Run the bot."""
    try:
        bot = DiscordBot()
        bot.run(settings.discord_token)
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()

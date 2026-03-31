import logging

import discord
from discord.ext import commands, tasks

from bot.commands.delete import register_delete_commands
from bot.commands.sound_groups import register_sound_groups_commands
from bot.commands.soundboard import register_soundboard_commands
from bot.commands.upload import register_upload_commands
from bot.commands.user_sounds import register_user_sounds_commands
from bot.commands.voice import register_voice_commands
from bot.config.settings import settings
from bot.services.audio_processor import AudioProcessor
from bot.services.sound_modification_service import SoundModificationService
from bot.services.sound_manager import SoundManager
from bot.services.user_sound_service import UserSoundService
from bot.services.audio_mixer import AudioMixer

logger = logging.getLogger(__name__)


class DiscordBot(commands.Bot):
    """Main bot class with soundboard functionality."""

    def __init__(self) -> None:
        super().__init__(command_prefix=settings.discord_prefix,
                         intents=discord.Intents.all())

        # Initialize services
        self.sound_manager = SoundManager(settings.sounds_dir)
        self.audio_processor = AudioProcessor(settings.sounds_dir)
        self.sound_modification_service = SoundModificationService()
        self.user_sound_service = UserSoundService()
        self.guild_mixers: dict[int, AudioMixer] = {}

        # Register all commands
        self.register_commands()

    def get_mixer(self, guild_id: int) -> AudioMixer:
        """Return existing mixer for the guild or create a fresh one."""
        if guild_id not in self.guild_mixers:
            self.guild_mixers[guild_id] = AudioMixer()
        return self.guild_mixers[guild_id]

    def replace_mixer(self, guild_id: int) -> AudioMixer:
        """Replace (and cleanup) the mixer for a guild and return the new one."""
        old = self.guild_mixers.pop(guild_id, None)
        if old:
            old.cleanup()
        mixer = AudioMixer()
        self.guild_mixers[guild_id] = mixer
        return mixer

    async def setup_hook(self):
        return await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")
        if not self.check_voice_channel.is_running():
            self.check_voice_channel.start()

    @tasks.loop(minutes=5)
    async def check_voice_channel(self) -> None:
        for vc in self.voice_clients:
            channel = vc.channel
            if channel is not None:
                non_bot_members = [m for m in channel.members if not m.bot]
                if len(non_bot_members) == 0:
                    await vc.disconnect(force=True)

    async def on_voice_state_update(self, member, before, after):
        """Handle user joining voice channels with personal sounds."""
        user_sounds = UserSoundService.load_user_sounds()
        sound_name = user_sounds.get(str(member.id))
        if sound_name is None:
            return

        sound_path = self.sound_manager.find_sound(sound_name)
        if not sound_path:
            return

        if before.channel != after.channel and after.channel is not None:
            voice_client = member.guild.voice_client
            if voice_client and voice_client.channel == after.channel:
                if not voice_client.is_playing():
                    source = discord.FFmpegPCMAudio(sound_path)
                    voice_client.play(source)
            else:
                channel = after.channel
                voice_client = await channel.connect()
                source = discord.FFmpegPCMAudio(sound_path)
                voice_client.play(source)

    async def cleanup_soundboard_messages(self, channel: discord.TextChannel, board_type: str = "general") -> None:
        """Delete previous soundboard messages of the requested type from the bot in the channel."""
        try:
            async for message in channel.history(limit=100):
                is_general_board = message.content == "Soundboard activated:"
                is_group_board = message.content.startswith("Soundboard activated (group:")
                should_delete = (board_type == "general" and is_general_board) or (
                    board_type == "group" and is_group_board
                )

                if message.author == self.user and should_delete and message.components:
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        logger.error(f"Soundboard cleanup: "
                                     f"Message {message.id} already deleted in channel {channel.name}")
                    except discord.errors.Forbidden:
                        logger.error(f"Soundboard cleanup: "
                                     f"No permission to delete message {message.id} in channel {channel.name}")
                    except discord.errors.HTTPException as e:
                        logger.error(f"Soundboard cleanup: "
                                     f"HTTP error deleting message {message.id} in channel {channel.name}: {e}")
        except discord.errors.Forbidden:
            logger.error(f"Soundboard cleanup: "
                         f"No permission to read history in channel {channel.name}")
        except discord.errors.HTTPException as e:
            logger.error(f"Soundboard cleanup: "
                         f"HTTP error reading history in channel {channel.name}: {e}")

    def register_commands(self) -> None:
        """Register all bot commands."""
        register_voice_commands(self.tree)
        register_soundboard_commands(self.tree, self)
        register_sound_groups_commands(self.tree, self)
        register_upload_commands(self.tree, self)
        register_delete_commands(self.tree, self)
        register_user_sounds_commands(self.tree, self)

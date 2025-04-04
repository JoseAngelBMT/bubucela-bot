from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import View, Button
import os

SOUNDS_DIR: str = "sounds/"


class SoundboardView(View):
    def __init__(self, bot: commands.Bot, sounds: dict):
        super().__init__(timeout=None)
        self.bot = bot
        self.sounds = sounds

        for sound_name in sounds.keys():
            button = Button(label=sound_name, custom_id=sound_name)
            button.callback = self.create_callback(sound_name)
            self.add_item(button)

    def create_callback(self, sound_name):
        async def callback(interaction: discord.Interaction):
            if interaction.guild.voice_client is None:
                if interaction.user.voice and interaction.user.voice.channel:
                    channel = interaction.user.voice.channel
                    await channel.connect()

            sound_path = self.sounds.get(sound_name)
            if not sound_path:
                await interaction.response.send_message("Sound does not exist.", ephemeral=True)
                return

            if not interaction.guild.voice_client:
                if interaction.user.voice:
                    channel = interaction.user.voice.channel
                    await channel.connect()
                else:
                    await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
                    return

            source = discord.FFmpegPCMAudio(sound_path)
            if not interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.play(source)
                await interaction.response.defer()
            else:
                await interaction.response.send_message(
                    "Playing a sound, wait for it to finish.", ephemeral=True
                )

        return callback


class DiscordBot(commands.Bot):
    config: dict

    def __init__(self, config: dict) -> None:
        super().__init__(command_prefix="/",
                         intents=discord.Intents.all())
        self.config = config
        self.register_commands()

    async def setup_hook(self):
        return await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    def register_commands(self) -> None:

        @self.tree.command(name="join", description="Joins a Discord chat voice")
        async def join(interaction: discord.Interaction) -> None:
            if interaction.user.voice:
                channel = interaction.user.voice.channel

                await channel.connect()
                await interaction.response.send_message("Connected!", ephemeral=True)
            else:
                await interaction.response.send_message("You're not connected to a voice channel", ephemeral=True)

        @self.tree.command(name="leave", description="Leave a Discord chat voice")
        async def leave(interaction: discord.Interaction) -> None:
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.disconnect()
                await interaction.response.send_message("Disconnected!", ephemeral=True)
            else:
                await interaction.response.send_message("Not in a voice channel", ephemeral=True)

        @self.tree.command(name="play", description="Play a saved sound")
        async def play(interaction: discord.Interaction, sound: str) -> None:
            if not interaction.guild.voice_client:
                await join(interaction)

            sound_path = self.find_sound(sound)
            if sound_path:
                source = discord.FFmpegPCMAudio(sound_path)
                interaction.guild.voice_client.play(source)
                await interaction.response.send_message(f"Playing: {sound}", ephemeral=True)
            else:
                await interaction.response.send_message("Sound not found", ephemeral=True)

        @self.tree.command(name="stop", description="Stop playing sound")
        async def stop(interaction: discord.Interaction):
            voice_client = interaction.guild.voice_client
            if voice_client and voice_client.is_playing():
                voice_client.stop()
                await interaction.response.send_message("Stopped.", ephemeral=True)
            elif voice_client:
                await interaction.response.send_message("Nothing playing.", ephemeral=True)
            else:
                await interaction.response.send_message("Bot not in a voice channel.", ephemeral=True)

        @self.tree.command(name="upload", description="Upload a sound file (optional: give a name")
        async def upload(interaction: discord.Interaction, attachment: discord.Attachment,
                         sound_name: str = None) -> None:
            if not attachment.filename.lower().endswith((".mp3", ".wav", ".ogg")):
                await interaction.response.send_message("Unsupported format (.mp3, .wav, .ogg)", ephemeral=True)
                return

            if sound_name:
                extension = attachment.filename.rsplit(".", maxsplit=1)[-1]
                save_path = os.path.join(SOUNDS_DIR, f"{sound_name}.{extension}")
            else:
                save_path = os.path.join(SOUNDS_DIR, attachment.filename)
            await attachment.save(save_path)
            await interaction.response.send_message(f"Saved: {attachment.filename}", ephemeral=True)

        @self.tree.command(name="soundboard", description="Open a soundboard")
        async def soundboard(interaction: discord.Interaction) -> None:
            sounds = self.get_sounds_dict(SOUNDS_DIR)

            view = SoundboardView(self, sounds)
            await interaction.response.send_message("Soundboard activado:", view=view)

    @staticmethod
    def find_sound(filename: str) -> Optional[str]:
        return next(
            (os.path.join(SOUNDS_DIR, file) for file in os.listdir(SOUNDS_DIR)
             if os.path.splitext(file)[0] == filename), None)

    @staticmethod
    def get_sounds_dict(path: str) -> dict:
        if not os.path.isdir(path):
            raise ValueError(f"Path is not valid: {path}")

        sound_dict = {}
        for sound in os.listdir(path):
            ruta_completa = os.path.join(path, sound)
            if os.path.isfile(ruta_completa):
                nombre_sin_extension, _ = os.path.splitext(sound)
                sound_dict[nombre_sin_extension] = ruta_completa
        return sound_dict

    def remove_sound(self, sound_name: str) -> None:
        path = self.find_sound(sound_name)
        os.remove(path)


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv()

    TOKEN = str(os.getenv("DISCORD_TOKEN"))
    PREFIX = os.getenv("DISCORD_PREFIX")
    MODEL = os.getenv("MODEL_NAME")
    PROMPT = os.getenv("PROMPT")

    try:
        bot = DiscordBot(PREFIX)
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error: {e}")
        raise

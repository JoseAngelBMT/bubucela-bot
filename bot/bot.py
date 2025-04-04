from typing import Optional
from dotenv import dotenv_values
import os

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import View, Button


class SoundboardView(View):
    def __init__(self, bot: commands.Bot, sounds: dict, mode: str = "play"):
        super().__init__(timeout=None)
        self.bot = bot
        self.sounds = sounds
        self.mode = mode

        for sound_name in sounds.keys():
            button = Button(label=sound_name, custom_id=sound_name,
                            style=discord.ButtonStyle.danger if mode == "delete" else discord.ButtonStyle.secondary)
            button.callback = self.create_callback(sound_name)
            self.add_item(button)

    def create_callback(self, sound_name: str):
        async def callback(interaction: discord.Interaction):
            if self.mode == "play":
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
            elif self.mode == "delete":
                sound_path = self.sounds.get(sound_name)
                if sound_path and os.path.exists(sound_path):
                    os.remove(sound_path)
                    await interaction.response.send_message(f"Removed sound {sound_name}.", ephemeral=True)
                else:
                    interaction.response.send_message(f"Sound {sound_name} does not exist or already eliminated.",
                                                      ephemeral=True)

        return callback


class DiscordBot(commands.Bot):
    config: dict

    def __init__(self, config: dict) -> None:
        super().__init__(command_prefix=config["DISCORD_PREFIX"],
                         intents=discord.Intents.all())
        self.config = config
        self.sounds_dir = config["SOUNDS_DIR"]
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
                await interaction.guild.voice_client.disconnect(force=True)
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
            sounds = self.get_sounds_dict(self.sounds_dir)
            if len(sounds) >= int(self.config["MAX_SOUNDS"]):
                await interaction.response.send_message("Max sounds reached.", ephemeral=True)
                return

            if not attachment.filename.lower().endswith((".mp3", ".wav", ".ogg")):
                await interaction.response.send_message("Unsupported format (.mp3, .wav, .ogg)", ephemeral=True)
                return

            if sound_name:
                extension = attachment.filename.rsplit(".", maxsplit=1)[-1]
                save_path = os.path.join(self.sounds_dir, f"{sound_name}.{extension}")
            else:
                save_path = os.path.join(self.sounds_dir, attachment.filename)
            await attachment.save(save_path)
            await interaction.response.send_message(f"Saved: {attachment.filename}", ephemeral=True)

        @self.tree.command(name="soundboard", description="Open a soundboard")
        async def soundboard(interaction: discord.Interaction) -> None:
            sounds = self.get_sounds_dict(self.sounds_dir)
            if not sounds:
                await interaction.response.send_message("No sounds found.", ephemeral=True)
                return
            view = SoundboardView(self, sounds)
            await interaction.response.send_message("Soundboard activated:", view=view)

        @self.tree.command(name="delete", description="Delete a sound")
        async def delete(interaction: discord.Interaction) -> None:
            sounds = self.get_sounds_dict(self.sounds_dir)

            if not sounds:
                await interaction.response.send_message("No sounds found.", ephemeral=True)
                return

            view = SoundboardView(self, sounds, mode="delete")
            await interaction.response.send_message("Select a sound:", view=view, ephemeral=True)

    @staticmethod
    def find_sound(filename: str) -> Optional[str]:
        return next(
            (os.path.join(self.sounds_dir, file) for file in os.listdir(self.sounds_dir)
             if os.path.splitext(file)[0] == filename), None)

    @staticmethod
    def get_sounds_dict(path: str) -> dict:
        if not os.path.isdir(path):
            raise ValueError(f"Path is not valid: {path}")

        sound_dict = {}
        for sound in os.listdir(path):
            root = os.path.join(path, sound)
            if os.path.isfile(root):
                nombre_sin_extension, _ = os.path.splitext(sound)
                sound_dict[nombre_sin_extension] = root
        return sound_dict


if __name__ == '__main__':
    config = dotenv_values(".env")

    try:
        bot = DiscordBot(config)
        bot.run(config["DISCORD_TOKEN"])
    except Exception as e:
        print(f"Error: {e}")
        raise

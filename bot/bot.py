import os
from typing import Optional
from dotenv import dotenv_values

import discord
from discord.ext import commands, tasks
from discord.ui import View
from pydub import AudioSegment


class SoundboardView(View):
    sounds_per_page: int = 20

    def __init__(self, discord_bot: commands.Bot, sounds: dict, mode: str = "play", page: int = 0):
        super().__init__(timeout=None)
        self.bot = discord_bot
        self.sounds = sounds
        self.mode = mode
        self.page = page
        self.total_pages = (len(sounds) - 1) // self.sounds_per_page

        self.update_buttons()

    def get_current_page_sounds(self) -> list:
        start = self.page * self.sounds_per_page
        end = start + self.sounds_per_page
        return list(self.sounds.keys())[start:end]

    def update_buttons(self):
        self.clear_items()

        current_sounds = self.get_current_page_sounds()
        for sound_name in current_sounds:
            button = discord.ui.Button(label=sound_name[:self.sounds_per_page],
                                       custom_id=sound_name[:self.sounds_per_page],
                                       style=discord.ButtonStyle.danger if self.mode == "delete"
                                       else discord.ButtonStyle.gray)
            button.callback = self.create_callback(sound_name)
            self.add_item(button)

        if self.total_pages > 0:
            nav_buttons = [
                ("◀️", self.previous_page),
                (f"Page {self.page + 1}/{self.total_pages + 1}", self.noop),
                ("▶️", self.next_page)
            ]

            for (emoji, action) in nav_buttons:
                button = discord.ui.Button(label=emoji,
                                           style=discord.ButtonStyle.primary)
                button.callback = action
                self.add_item(button)

    async def noop(self, interaction: discord.Interaction):
        await interaction.response.defer()

    async def previous_page(self, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        self.update_buttons()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.page = min(self.total_pages, self.page + 1)
        self.update_buttons()
        await interaction.response.edit_message(view=self)

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
                else:
                    interaction.guild.voice_client.stop()
                    interaction.guild.voice_client.play(source)
                await interaction.response.defer()
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
    sound_formats: list[str] = [".mp3", ".wav", ".ogg", ".opus"]

    def __init__(self, config_venv: dict) -> None:
        super().__init__(command_prefix=config_venv["DISCORD_PREFIX"],
                         intents=discord.Intents.all())
        self.config = config_venv
        self.sounds_dir = config_venv["SOUNDS_DIR"]
        self.register_commands()

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

    def register_commands(self) -> None:  # pylint: disable=too-many-statements

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
                         sound_name: Optional[str] = None, start_time: Optional[float] = None,
                         end_time: Optional[float] = None) -> None:
            sounds = self.get_sounds_dict(self.sounds_dir)
            if len(sounds) >= int(self.config["MAX_SOUNDS"]):
                await interaction.response.send_message("Max sounds reached.", ephemeral=True)
                return

            if attachment.size / (1024 * 1024) > int(self.config["MAX_FILE_SIZE_MB"]):
                await interaction.response.send_message(
                    f"File exceeds max size of {self.config['MAX_FILE_SIZE_MB']} MB.", ephemeral=True)
                return

            if not attachment.filename.lower().endswith(tuple(self.sound_formats)):
                await interaction.response.send_message(f"Unsupported format {self.sound_formats}", ephemeral=True)
                return

            if sound_name:
                extension = attachment.filename.rsplit(".", maxsplit=1)[-1]
                save_path = os.path.join(self.sounds_dir, f"{sound_name}.{extension}")
            else:
                save_path = os.path.join(self.sounds_dir, attachment.filename)
            await attachment.save(save_path)

            if start_time is not None or end_time is not None:
                self.cut_audio(save_path, start_time, end_time)

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

    def find_sound(self, filename: str) -> Optional[str]:
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

    @staticmethod
    def cut_audio(save_path: str, start_time: Optional[float] = None, end_time: Optional[float] = None) -> None:
        audio = AudioSegment.from_file(save_path)
        start_ms = int(start_time * 1000) if start_time is not None else 0
        end_ms = int(end_time * 1000) if end_time is not None else len(audio)
        cut_audio = audio[start_ms:end_ms]
        cut_audio.export(save_path, format=save_path.rsplit('.', 1)[-1])


if __name__ == '__main__':
    config = dotenv_values(".env")

    try:
        bot = DiscordBot(config)
        bot.run(config["DISCORD_TOKEN"])
    except Exception as e:
        print(f"Error: {e}")
        raise

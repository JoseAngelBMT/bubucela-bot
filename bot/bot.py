import json
import os
from typing import Optional

import discord
import yt_dlp
from discord import ButtonStyle, app_commands
from discord.ext import commands, tasks
from discord.ui import View
from dotenv import dotenv_values
from pydub import AudioSegment


class SoundboardView(View):
    sounds_per_page: int = 20

    def __init__(self, sounds: dict, mode: str = "play", multi_select: bool = False) -> None:
        super().__init__(timeout=None)
        self.sounds = sounds
        self.mode = mode
        self.multi_select = multi_select
        self.page = 0
        self.total_pages = (len(sounds) - 1) // self.sounds_per_page
        self.selected_sounds = set()

        self.update_buttons()

    def get_current_page_sounds(self) -> list:
        start = self.page * self.sounds_per_page
        end = start + self.sounds_per_page
        return list(self.sounds.keys())[start:end]

    def update_buttons(self):
        self.clear_items()

        current_sounds = self.get_current_page_sounds()
        for sound_name in current_sounds:
            selected = sound_name in self.selected_sounds
            if selected:
                style = ButtonStyle.success
            elif self.mode == "delete":
                style = ButtonStyle.danger
            else:
                style = ButtonStyle.gray
            button = discord.ui.Button(label=sound_name[:self.sounds_per_page],
                                       custom_id=sound_name[:self.sounds_per_page],
                                       style=style)
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
                                           style=ButtonStyle.primary)
                button.callback = action
                self.add_item(button)

        if self.mode == "select":
            confirm_button = discord.ui.Button(label="Confirm", style=ButtonStyle.primary)
            confirm_button.callback = self.confirm_selection
            self.add_item(confirm_button)

    async def noop(self, interaction: discord.Interaction):
        await interaction.response.defer()

    async def previous_page(self, interaction: discord.Interaction):
        self.page = self.page - 1 if self.page > 0 else self.total_pages
        self.update_buttons()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.page = self.page + 1 if self.page < self.total_pages else 0
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
            elif self.mode == "select":
                if self.multi_select:
                    if sound_name in self.selected_sounds:
                        self.selected_sounds.remove(sound_name)
                    else:
                        self.selected_sounds.add(sound_name)
                else:
                    self.selected_sounds = {sound_name}
                self.update_buttons()
                await interaction.response.edit_message(view=self)

        return callback

    async def confirm_selection(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.stop()

    def get_selected_sounds(self) -> list:
        return list(self.selected_sounds)


class DiscordBot(commands.Bot):
    config: dict
    sound_formats: list[str] = [".mp3", ".wav", ".ogg", ".opus"]
    cached_sounds: Optional[dict]

    def __init__(self, config_venv: dict) -> None:
        super().__init__(command_prefix=config_venv["DISCORD_PREFIX"],
                         intents=discord.Intents.all())
        self.config = config_venv
        self.sounds_dir = config_venv["SOUNDS_DIR"]
        self.cached_sounds = None
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

    async def on_voice_state_update(self, member, before, after):
        user_sounds = self.load_user_sounds()
        sound_name = user_sounds.get(str(member.id))
        if sound_name is None:
            return

        sound_path = self.find_sound(sound_name)
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
                         sound_name: Optional[str] = None, start_time: Optional[str] = None,
                         end_time: Optional[str] = None) -> None:
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
            self.get_sounds_dict(self.sounds_dir, False)

        @self.tree.command(name="soundboard", description="Open a soundboard")
        async def soundboard(interaction: discord.Interaction) -> None:
            sounds = self.get_sounds_dict(self.sounds_dir)
            if not sounds:
                await interaction.response.send_message("No sounds found.", ephemeral=True)
                return
            view = SoundboardView(sounds)
            await interaction.response.send_message("Soundboard activated:", view=view)

        @self.tree.command(name="delete", description="Delete a sound")
        async def delete(interaction: discord.Interaction) -> None:
            sounds = self.get_sounds_dict(self.sounds_dir)

            if not sounds:
                await interaction.response.send_message("No sounds found.", ephemeral=True)
                return

            view = SoundboardView(sounds, mode="delete")
            await interaction.response.send_message("Select a sound:", view=view, ephemeral=True)
            self.get_sounds_dict(self.sounds_dir, False)

        @self.tree.command(name="set_user_sound", description="Set a personal sound")
        async def set_user_sound(interaction: discord.Interaction):
            sounds = self.get_sounds_dict(self.sounds_dir)
            if not sounds:
                await interaction.response.send_message("No sounds.", ephemeral=True)
                return

            view = SoundboardView(sounds, mode="select", multi_select=False)
            await interaction.response.send_message("Select your sound:", view=view, ephemeral=True)

            await view.wait()
            selected = view.get_selected_sounds()
            if selected:
                self.save_user_sounds(str(interaction.user.id), selected[0])
                await interaction.followup.send(f"Set {selected} sound as personal", ephemeral=True)
            else:
                await interaction.followup.send("No sound selected.", ephemeral=True)

        @self.tree.command(name="clear_user_sound", description="Clear your personal sound")
        async def clear_user_sound(interaction: discord.Interaction):
            user_sounds = self.load_user_sounds()
            if str(interaction.user.id) in user_sounds:
                del user_sounds[str(interaction.user.id)]
                with open("static/user_sounds.json", "w") as f:
                    json.dump(user_sounds, f, indent=4)
                await interaction.response.send_message("Cleared your personal sound.", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have a personal sound set.", ephemeral=True)

        @self.tree.command(name="upload_youtube",
                           description="Upload a sound file from a YouTube video")
        @app_commands.describe(
            start_time="Start time (hh:mm:ss, mm:ss or ss)",
            end_time="End time (hh:mm:ss, mm:ss or ss)"
        )
        async def upload(interaction: discord.Interaction, youtube_url: str,
                         sound_name: str, start_time: Optional[str] = None,
                         end_time: Optional[str] = None) -> None:
            sounds = self.get_sounds_dict(self.sounds_dir)
            if len(sounds) >= int(self.config["MAX_SOUNDS"]):
                await interaction.response.send_message("Max sounds reached.", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)
            try:
                sound_path = self.save_youtube_audio(youtube_url, sound_name, start_time, end_time)
                sound_size = self.sound_size(sound_name)

                if sound_size / (1024 * 1024) > int(self.config["MAX_FILE_SIZE_MB"]):
                    await interaction.followup.send(
                        f"File exceeds max size of {self.config['MAX_FILE_SIZE_MB']} MB.", ephemeral=True)
                    os.remove(sound_path)
                    return

                await interaction.followup.send(f"Saved: {sound_name}", ephemeral=True)
                self.get_sounds_dict(self.sounds_dir, False)
            except Exception as e:
                await interaction.followup.send(f"❌ Error downloading the sound {str(e)}", ephemeral=True)

    def find_sound(self, filename: str) -> Optional[str]:
        return next(
            (os.path.join(self.sounds_dir, file) for file in os.listdir(self.sounds_dir)
             if os.path.splitext(file)[0] == filename), None)

    def get_sounds_dict(self, path: str, use_cache: bool = True) -> dict:

        if use_cache and self.cached_sounds is not None:
            return self.cached_sounds

        if not os.path.isdir(path):
            raise ValueError(f"Path is not valid: {path}")

        sound_dict = {}
        for sound in os.listdir(path):
            root = os.path.join(path, sound)
            if os.path.isfile(root):
                nombre_sin_extension, _ = os.path.splitext(sound)
                sound_dict[nombre_sin_extension] = root
        self.cached_sounds = sound_dict
        return sound_dict

    def cut_audio(self, save_path: str, start_time: Optional[str] = None,
                  end_time: Optional[str] = None) -> None:
        audio = AudioSegment.from_file(save_path)

        start_ms = int(self.time_to_seconds(start_time) * 1000) if start_time is not None else 0
        end_ms = int(self.time_to_seconds(end_time) * 1000) if end_time is not None else len(audio)

        cut_audio = audio[start_ms:end_ms]
        cut_audio.export(save_path, format=save_path.rsplit('.', 1)[-1])

    @staticmethod
    def load_user_sounds() -> dict:
        path = "static/user_sounds.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_user_sounds(user_id: str, sound_name: str) -> None:
        data = {}
        path = "static/user_sounds.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data[user_id] = sound_name
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def save_youtube_audio(self, url: str, sound_name: str, start_time: Optional[str], end_time: Optional[str],
                           extension: str = "opus") -> str:

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(self.sounds_dir, f"{sound_name}.%(ext)s"),
            "download_ranges": lambda info_dict, yt_instance: [
                {'start_time': self.time_to_seconds(start_time) if start_time else 0,
                 'end_time': self.time_to_seconds(end_time) if end_time else 1e6,
                 'title': 'first_section'},
            ],
            "force_keyframes_at_cuts": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": extension,
                "preferredquality": "6",
            }],
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return os.path.join(self.sounds_dir, f"{sound_name}.{extension}")

    @staticmethod
    def time_to_seconds(time: str) -> float:
        match [int(p) for p in time.strip().split(":")]:
            case [h, m, s]:
                return h * 3600 + m * 60 + s
            case [m, s]:
                return m * 60 + s
            case [s]:
                return s
            case _:
                raise ValueError(f"Time format not valid: {tiempo}")

    def sound_size(self, sound_name: str) -> int:
        sound_path = self.find_sound(sound_name)
        return os.path.getsize(sound_path)


if __name__ == '__main__':
    config = dotenv_values(".env")

    try:
        bot = DiscordBot(config)
        bot.run(config["DISCORD_TOKEN"])
    except Exception as e:
        print(f"Error: {e}")
        raise

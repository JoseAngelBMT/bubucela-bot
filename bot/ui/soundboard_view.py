import logging
import os

import discord
from discord import ButtonStyle
from discord.ui import View

from bot.services.audio_mixer import AudioMixer
from bot.utils.constants import SOUNDS_PER_PAGE

logger = logging.getLogger(__name__)


class SoundboardView(View):
    """Interactive soundboard view with pagination."""

    sounds_per_page: int = SOUNDS_PER_PAGE

    def __init__(self, sounds: dict, mode: str = "play", multi_select: bool = False,
                 sound_modification_service=None, bot=None) -> None:
        super().__init__(timeout=None)
        self.sounds = sounds
        self.mode = mode
        self.multi_select = multi_select
        self.sound_modification_service = sound_modification_service
        self.bot = bot
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

        if self.mode == "play":
            stop_button = discord.ui.Button(label="⏹ STOP", style=ButtonStyle.danger)
            stop_button.callback = self.stop_all
            self.add_item(stop_button)

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

    # pylint: disable=too-many-branches
    def create_callback(self, sound_name: str):
        async def callback(interaction: discord.Interaction):
            if self.mode == "play":
                vc = interaction.guild.voice_client
                if vc is None:
                    if interaction.user.voice and interaction.user.voice.channel:
                        vc = await interaction.user.voice.channel.connect()
                    else:
                        await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
                        return

                sound_path = self.sounds.get(sound_name)
                if not sound_path:
                    await interaction.response.send_message("Sound does not exist.", ephemeral=True)
                    return

                source = discord.FFmpegPCMAudio(sound_path, executable="ffmpeg")

                if self.bot is not None:
                    # --- Overlapping playback via AudioMixer ---
                    if vc.is_playing():
                        mixer = self.bot.get_mixer(interaction.guild.id)
                    else:
                        mixer = self.bot.replace_mixer(interaction.guild.id)

                    if not mixer.add_source(source):
                        await interaction.response.send_message(
                            f"Max {AudioMixer.MAX_SOURCES} simultaneous sounds reached.", ephemeral=True
                        )
                        return

                    if not vc.is_playing():
                        def after_mixer(error):
                            if error:
                                logger.error(f"[soundboard mixer] Playback error: {error}")
                            self.bot.guild_mixers.pop(interaction.guild.id, None)

                        vc.play(mixer, after=after_mixer)
                else:
                    # Fallback: single sound (no bot reference)
                    if vc.is_playing():
                        vc.stop()
                    vc.play(source)

                await interaction.response.defer()
            elif self.mode == "delete":
                sound_path = self.sounds.get(sound_name)
                if sound_path and os.path.exists(sound_path):
                    os.remove(sound_path)
                    if self.sound_modification_service:
                        self.sound_modification_service.clear_sound_tracking(sound_name)
                    await interaction.response.send_message(f"Removed sound {sound_name}.", ephemeral=True)
                else:
                    await interaction.response.send_message(
                        f"Sound {sound_name} does not exist or already eliminated.",
                        ephemeral=True,
                    )
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

    async def stop_all(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            if self.bot is not None:
                self.bot.guild_mixers.pop(interaction.guild.id, None)
            await interaction.response.defer()
        else:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)

    def get_selected_sounds(self) -> list:
        return list(self.selected_sounds)

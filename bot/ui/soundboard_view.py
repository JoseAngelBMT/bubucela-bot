import os

import discord
from discord import ButtonStyle
from discord.ui import View

from bot.utils.constants import SOUNDS_PER_PAGE


class SoundboardView(View):
    """Interactive soundboard view with pagination."""

    sounds_per_page: int = SOUNDS_PER_PAGE

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

    # pylint: disable=too-many-branches
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

import os
from typing import Optional

import discord
from discord import app_commands

from bot.config.settings import settings
from bot.utils.constants import SOUND_FORMATS


def register_upload_commands(tree: app_commands.CommandTree, bot) -> None:
    """Register upload-related commands."""

    @tree.command(name="upload", description="Upload a sound file (optional: give a name")
    async def upload(interaction: discord.Interaction, attachment: discord.Attachment,
                     sound_name: Optional[str] = None, start_time: Optional[str] = None,
                     end_time: Optional[str] = None) -> None:
        sounds = bot.sound_manager.get_sounds_dict()
        if len(sounds) >= settings.max_sounds:
            await interaction.response.send_message("Max sounds reached.", ephemeral=True)
            return

        if attachment.size / (1024 * 1024) > settings.max_file_size_mb:
            await interaction.response.send_message(
                f"File exceeds max size of {settings.max_file_size_mb} MB.", ephemeral=True)
            return

        if not attachment.filename.lower().endswith(tuple(SOUND_FORMATS)):
            await interaction.response.send_message(f"Unsupported format {SOUND_FORMATS}", ephemeral=True)
            return

        if sound_name:
            extension = attachment.filename.rsplit(".", maxsplit=1)[-1]
            save_path = os.path.join(settings.sounds_dir, f"{sound_name}.{extension}")
        else:
            save_path = os.path.join(settings.sounds_dir, attachment.filename)
        await attachment.save(save_path)

        if start_time is not None or end_time is not None:
            bot.audio_processor.cut_audio(save_path, start_time, end_time)

        await interaction.response.send_message(f"Saved: {attachment.filename}", ephemeral=True)
        bot.sound_manager.invalidate_cache()

    @tree.command(name="upload_youtube",
                  description="Upload a sound file from a YouTube video")
    @app_commands.describe(
        start_time="Start time (hh:mm:ss, mm:ss or ss)",
        end_time="End time (hh:mm:ss, mm:ss or ss)"
    )
    async def upload_youtube(interaction: discord.Interaction, youtube_url: str,
                             sound_name: str, start_time: Optional[str] = None,
                             end_time: Optional[str] = None) -> None:
        sounds = bot.sound_manager.get_sounds_dict()
        if len(sounds) >= settings.max_sounds:
            await interaction.response.send_message("Max sounds reached.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            sound_path = bot.audio_processor.download_youtube_audio(youtube_url, sound_name, start_time, end_time)
            sound_size = bot.sound_manager.sound_size(sound_name)

            if sound_size / (1024 * 1024) > settings.max_file_size_mb:
                await interaction.followup.send(
                    f"File exceeds max size of {settings.max_file_size_mb} MB.", ephemeral=True)
                os.remove(sound_path)
                return

            await interaction.followup.send(f"Saved: {sound_name}", ephemeral=True)
            bot.sound_manager.invalidate_cache()
        except Exception as e:
            await interaction.followup.send(f"❌ Error downloading the sound {str(e)}", ephemeral=True)

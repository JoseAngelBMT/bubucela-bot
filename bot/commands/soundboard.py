import asyncio
import logging
import os
import tempfile
from typing import Optional

import discord
from discord import app_commands

from bot.ui.soundboard_view import SoundboardView

logger = logging.getLogger(__name__)


def register_soundboard_commands(tree: app_commands.CommandTree, bot) -> None:
    """Register soundboard-related commands."""

    @tree.command(name="play", description="Play a saved sound")
    @app_commands.describe(
        volume="Volume % of the sound"
    )
    async def play(interaction: discord.Interaction, sound: str, volume: int = 100) -> None:
        if not interaction.guild.voice_client:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                await channel.connect()
            else:
                await interaction.response.send_message("You're not connected to a voice channel", ephemeral=True)
                return

        sound_path = bot.sound_manager.find_sound(sound)
        if not sound_path:
            await interaction.response.send_message("Sound not found", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            source = discord.FFmpegPCMAudio(sound_path, executable='ffmpeg', options=f'-af "volume={volume / 100.0}"')
            interaction.guild.voice_client.play(source)
            await interaction.followup.send(f"Playing: `{sound}`", ephemeral=True)
        except (discord.errors.InteractionResponded, discord.errors.NotFound) as e:
            logger.error(f"[/play] Error playing the sound: {e}")
            await interaction.followup.send("Error playing the sound...", ephemeral=True)

    @tree.command(name="soundboard", description="Open a soundboard")
    async def soundboard(interaction: discord.Interaction) -> None:
        sounds = await asyncio.to_thread(bot.sound_manager.get_sounds_dict)
        if not sounds:
            await interaction.response.send_message("No sounds found.", ephemeral=True)
            return

        await bot.cleanup_soundboard_messages(interaction.channel, board_type="general")

        view = SoundboardView(sounds, bot=bot)
        await interaction.response.send_message("Soundboard activated:", view=view)

    @tree.command(name="modify_volume", description="Modify a sound volume and keep a backup")
    @app_commands.describe(volume="Target volume percentage (0-200)")
    async def modify_volume(interaction: discord.Interaction, volume: app_commands.Range[int, 0, 200]) -> None:
        sounds = bot.sound_manager.get_sounds_dict()
        if not sounds:
            await interaction.response.send_message("No sounds found.", ephemeral=True)
            return

        view = SoundboardView(sounds, mode="select", multi_select=False)
        await interaction.response.send_message(
            "Select one sound to modify:",
            view=view,
            ephemeral=True,
        )

        await view.wait()
        selected = view.get_selected_sounds()
        await interaction.delete_original_response()

        if not selected:
            await interaction.followup.send("No sound selected.", ephemeral=True)
            return

        sound_name = selected[0]
        sound_path = bot.sound_manager.find_sound(sound_name)
        if not sound_path:
            await interaction.followup.send("Sound not found.", ephemeral=True)
            return

        try:
            backup_path = bot.sound_modification_service.ensure_backup(sound_name, sound_path)
            bot.audio_processor.apply_volume(output_path=sound_path, volume_percentage=volume, source_path=backup_path)
            bot.sound_modification_service.mark_modified(sound_name, sound_path)
            bot.sound_manager.invalidate_cache()
            await interaction.followup.send(
                f"Updated `{sound_name}` volume to `{volume}%` (backup saved).",
                ephemeral=True,
            )
        except Exception as error:
            await interaction.followup.send(f"Error modifying volume: `{error}`", ephemeral=True)

    @tree.command(name="restore", description="Restore modified sounds from backup")
    async def restore(interaction: discord.Interaction) -> None:
        modified_sounds = bot.sound_modification_service.list_modified_sounds()
        if not modified_sounds:
            await interaction.response.send_message("No modified sounds to restore.", ephemeral=True)
            return

        view = SoundboardView(modified_sounds, mode="select", multi_select=True)
        await interaction.response.send_message(
            "Select one or more modified sounds to restore:",
            view=view,
            ephemeral=True,
        )

        await view.wait()
        selected = view.get_selected_sounds()
        await interaction.delete_original_response()

        if not selected:
            await interaction.followup.send("No sound selected.", ephemeral=True)
            return

        restored = []
        failed = []
        for sound_name in selected:
            if bot.sound_modification_service.restore_sound(sound_name):
                restored.append(sound_name)
            else:
                failed.append(sound_name)

        bot.sound_manager.invalidate_cache()

        if restored:
            restored_text = ", ".join(f"`{name}`" for name in restored)
            await interaction.followup.send(f"Restored: {restored_text}", ephemeral=True)
        if failed:
            failed_text = ", ".join(f"`{name}`" for name in failed)
            await interaction.followup.send(f"Could not restore: {failed_text}", ephemeral=True)

    @tree.command(name="play_youtube", description="Play audio from a YouTube video without saving it")
    @app_commands.describe(
        youtube_url="YouTube video URL",
        start_time="Start time (hh:mm:ss, mm:ss or ss)",
        end_time="End time (hh:mm:ss, mm:ss or ss)",
        volume="Volume % of the sound",
    )
    async def play_youtube(interaction: discord.Interaction, youtube_url: str,
                           start_time: Optional[str] = None, end_time: Optional[str] = None,
                           volume: int = 100) -> None:
        if not interaction.guild.voice_client:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                await channel.connect()
            else:
                await interaction.response.send_message("You're not connected to a voice channel.", ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)
        tmp_dir = tempfile.mkdtemp()
        try:
            sound_path = await asyncio.to_thread(
                bot.audio_processor.download_youtube_audio,
                youtube_url, "play_tmp", start_time, end_time, "opus", tmp_dir,
            )

            def after_play(error):
                if error:
                    logger.error(f"[/play_youtube] Playback error: {error}")
                try:
                    os.remove(sound_path)
                    os.rmdir(tmp_dir)
                except OSError:
                    pass

            source = discord.FFmpegPCMAudio(
                sound_path, executable="ffmpeg", options=f'-af "volume={volume / 100.0}"'
            )
            vc = interaction.guild.voice_client
            if vc.is_playing():
                vc.stop()
            vc.play(source, after=after_play)
            await interaction.followup.send("▶️ Playing YouTube audio...", ephemeral=True)
        except Exception as error:
            logger.error(f"[/play_youtube] Error: {error}")
            try:
                os.rmdir(tmp_dir)
            except OSError:
                pass
            await interaction.followup.send(f"❌ Error: {error}", ephemeral=True)


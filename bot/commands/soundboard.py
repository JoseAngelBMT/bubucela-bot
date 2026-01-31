import discord
from discord import app_commands

from bot.ui.soundboard_view import SoundboardView


def register_soundboard_commands(tree: app_commands.CommandTree, bot) -> None:
    """Register soundboard-related commands."""

    @tree.command(name="play", description="Play a saved sound")
    async def play(interaction: discord.Interaction, sound: str) -> None:
        if not interaction.guild.voice_client:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                await channel.connect()
            else:
                await interaction.response.send_message("You're not connected to a voice channel", ephemeral=True)
                return

        sound_path = bot.sound_manager.find_sound(sound)
        if sound_path:
            source = discord.FFmpegPCMAudio(sound_path)
            interaction.guild.voice_client.play(source)
            await interaction.response.send_message(f"Playing: {sound}", ephemeral=True)
        else:
            await interaction.response.send_message("Sound not found", ephemeral=True)

    @tree.command(name="soundboard", description="Open a soundboard")
    async def soundboard(interaction: discord.Interaction) -> None:
        sounds = bot.sound_manager.get_sounds_dict()
        if not sounds:
            await interaction.response.send_message("No sounds found.", ephemeral=True)
            return

        await bot.cleanup_soundboard_messages(interaction.channel)

        view = SoundboardView(sounds)
        await interaction.response.send_message("Soundboard activated:", view=view)

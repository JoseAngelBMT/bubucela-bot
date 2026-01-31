import discord
from discord import app_commands


def register_voice_commands(tree: app_commands.CommandTree) -> None:
    """Register voice-related commands."""

    @tree.command(name="join", description="Joins a Discord chat voice")
    async def join(interaction: discord.Interaction) -> None:
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            await channel.connect()
            await interaction.response.send_message("Connected!", ephemeral=True)
        else:
            await interaction.response.send_message("You're not connected to a voice channel", ephemeral=True)

    @tree.command(name="leave", description="Leave a Discord chat voice")
    async def leave(interaction: discord.Interaction) -> None:
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect(force=True)
            await interaction.response.send_message("Disconnected!", ephemeral=True)
        else:
            await interaction.response.send_message("Not in a voice channel", ephemeral=True)

    @tree.command(name="stop", description="Stop playing sound")
    async def stop(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("Stopped.", ephemeral=True)
        elif voice_client:
            await interaction.response.send_message("Nothing playing.", ephemeral=True)
        else:
            await interaction.response.send_message("Bot not in a voice channel.", ephemeral=True)

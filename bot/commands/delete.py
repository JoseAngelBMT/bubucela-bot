import discord
from discord import app_commands

from bot.ui.soundboard_view import SoundboardView


def register_delete_commands(tree: app_commands.CommandTree, bot) -> None:
    """Register delete-related commands."""

    @tree.command(name="delete", description="Delete a sound")
    async def delete(interaction: discord.Interaction) -> None:
        sounds = bot.sound_manager.get_sounds_dict()

        if not sounds:
            await interaction.response.send_message("No sounds found.", ephemeral=True)
            return

        view = SoundboardView(
            sounds,
            mode="delete",
            sound_modification_service=bot.sound_modification_service,
        )
        await interaction.response.send_message("Select a sound:", view=view, ephemeral=True)
        bot.sound_manager.invalidate_cache()

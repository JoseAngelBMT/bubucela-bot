import discord
from discord import app_commands

from bot.services.user_sound_service import UserSoundService
from bot.ui.soundboard_view import SoundboardView


def register_user_sounds_commands(tree: app_commands.CommandTree, bot) -> None:
    """Register user sound preference commands."""

    @tree.command(name="set_user_sound", description="Set a personal sound")
    async def set_user_sound(interaction: discord.Interaction):
        sounds = bot.sound_manager.get_sounds_dict()
        if not sounds:
            await interaction.response.send_message("No sounds.", ephemeral=True)
            return

        view = SoundboardView(sounds, mode="select", multi_select=False)
        await interaction.response.send_message("Select your sound:", view=view, ephemeral=True)

        await view.wait()
        selected = view.get_selected_sounds()
        await interaction.delete_original_response()
        if selected:
            UserSoundService.save_user_sound(str(interaction.user.id), selected[0])
            await interaction.followup.send(f"Set `{selected[0]}` sound as personal", ephemeral=True)
        else:
            await interaction.followup.send("No sound selected.", ephemeral=True)

    @tree.command(name="clear_user_sound", description="Clear your personal sound")
    async def clear_user_sound(interaction: discord.Interaction):
        if UserSoundService.clear_user_sound(str(interaction.user.id)):
            await interaction.response.send_message("Cleared your personal sound.", ephemeral=True)
        else:
            await interaction.response.send_message("You don't have a personal sound set.", ephemeral=True)

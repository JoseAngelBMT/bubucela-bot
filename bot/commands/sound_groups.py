import asyncio

import discord
from discord import app_commands

from bot.services.sound_group_service import SoundGroupService
from bot.ui.soundboard_view import SoundboardView


def register_sound_groups_commands(tree: app_commands.CommandTree, bot) -> None:
    """Register sound-group commands."""

    async def group_name_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        _ = interaction
        groups = SoundGroupService.list_groups()
        return [
            app_commands.Choice(name=group_name, value=group_name)
            for group_name in groups
            if current.lower() in group_name.lower()
        ][:25]

    @tree.command(name="group_set", description="Create or replace a sound group")
    async def group_set(interaction: discord.Interaction, group_name: str) -> None:
        sounds = await asyncio.to_thread(bot.sound_manager.get_sounds_dict)
        if not sounds:
            await interaction.response.send_message("No sounds found.", ephemeral=True)
            return

        view = SoundboardView(sounds, mode="select", multi_select=True)
        await interaction.response.send_message(
            f"Select sounds for group `{group_name}`:",
            view=view,
            ephemeral=True,
        )

        await view.wait()
        selected = sorted(view.get_selected_sounds())
        await interaction.delete_original_response()

        if not selected:
            await interaction.followup.send("No sounds selected.", ephemeral=True)
            return

        SoundGroupService.save_group(group_name, selected)
        await interaction.followup.send(
            f"Group `{group_name}` saved with `{len(selected)}` sounds.",
            ephemeral=True,
        )

    @tree.command(name="group_soundboard", description="Open a group soundboard")
    @app_commands.autocomplete(group_name=group_name_autocomplete)
    async def group_soundboard(interaction: discord.Interaction, group_name: str) -> None:
        groups = SoundGroupService.load_groups()
        selected_group = groups.get(group_name)
        if not selected_group:
            await interaction.response.send_message(f"Group `{group_name}` not found.", ephemeral=True)
            return

        sounds = await asyncio.to_thread(bot.sound_manager.get_sounds_dict)
        group_sounds = {name: sounds[name] for name in selected_group if name in sounds}
        if not group_sounds:
            await interaction.response.send_message(
                f"Group `{group_name}` has no available sounds.",
                ephemeral=True,
            )
            return

        await bot.cleanup_soundboard_messages(interaction.channel, board_type="group")

        view = SoundboardView(group_sounds, bot=bot)
        await interaction.response.send_message(f"Soundboard activated (group: `{group_name}`):", view=view)

    @tree.command(name="group_delete", description="Delete a sound group")
    @app_commands.autocomplete(group_name=group_name_autocomplete)
    async def group_delete(interaction: discord.Interaction, group_name: str) -> None:
        if SoundGroupService.delete_group(group_name):
            await interaction.response.send_message(f"Group `{group_name}` deleted.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Group `{group_name}` not found.", ephemeral=True)

    @tree.command(name="group_list", description="List all sound groups")
    async def group_list(interaction: discord.Interaction) -> None:
        groups = SoundGroupService.load_groups()
        if not groups:
            await interaction.response.send_message("No groups found.", ephemeral=True)
            return

        lines = [f"- `{group_name}` (`{len(sound_names)}` sounds)" for group_name, sound_names in sorted(groups.items())]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)



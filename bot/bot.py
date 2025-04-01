from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Context
import os

SOUNDS_DIR: str = "sounds/"

class DiscordBot(commands.Bot):
    config: dict

    def __init__(self, config: dict) -> None:
        super().__init__(command_prefix="/",
                         intents=discord.Intents.all())
        self.config = config
        self.register_commands()

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")


    def register_commands(self) -> None:

        @commands.command(name="join")
        async def join(ctx: Context) -> None:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                await channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")

        @commands.command(name="leave")
        async def leave(ctx: Context) -> None:
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            else:
                await ctx.send("No estoy en un canal de voz.")

        @commands.command(name="play")
        async def play(ctx: Context, sound: str) -> None:
            if not ctx.voice_client:
                await join(ctx)
            sound_path = self.find_sound(sound)
            if sound_path:
                source = discord.FFmpegPCMAudio(sound_path)
                ctx.voice_client.play(source)
            else:
                await ctx.send("Ese sonido no existe.")

        @commands.command(name="upload")
        async def upload(ctx: Context) -> None:
            if not ctx.message.attachments:
                await ctx.send("Attach audio file.")
                return

            for attachment in ctx.message.attachments:
                if attachment.filename.endswith((".mp3", ".wav", ".ogg")):
                    save_path = os.path.join(SOUNDS_DIR, attachment.filename)
                    await attachment.save(save_path)
                else:
                    await ctx.send("Audio file not supported -> (.mp3, .wav, .ogg).")

        self.add_command(join)
        self.add_command(leave)
        self.add_command(play)

    @staticmethod
    def find_sound(filename: str) -> Optional[str]:
        return next(
            (os.path.join(SOUNDS_DIR, file) for file in os.listdir(SOUNDS_DIR)
             if os.path.splitext(file)[0] == filename), None)

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    TOKEN = str(os.getenv("DISCORD_TOKEN"))
    PREFIX = os.getenv("DISCORD_PREFIX")
    MODEL = os.getenv("MODEL_NAME")
    PROMPT = os.getenv("PROMPT")

    try:
        bot = DiscordBot(PREFIX)
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error: {e}")
        raise

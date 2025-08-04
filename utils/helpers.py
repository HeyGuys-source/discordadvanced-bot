import discord
from datetime import datetime

def create_embed(title: str, description: str = None, color: discord.Color = discord.Color.blurple()) -> discord.Embed:
    embed = discord.Embed(title=title, color=color)
    if description:
        embed.description = description
    return embed

def create_success_embed(message: str) -> discord.Embed:
    return discord.Embed(description=message, color=discord.Color.green())

def create_error_embed(message: str) -> discord.Embed:
    return discord.Embed(description=message, color=discord.Color.red())

def format_relative_time(dt: datetime) -> str:
    return f"<t:{int(dt.timestamp())}:R>"

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

import re

def parse_time(time_str: str) -> int:
    """
    Parses time strings like '1d2h30m45s' into total seconds.
    Supports days (d), hours (h), minutes (m), and seconds (s).
    Example: '1h30m' -> 5400 seconds

    Returns total seconds as int.
    """
    time_units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    pattern = re.compile(r'(\d+)([dhms])', re.IGNORECASE)
    total_seconds = 0

    for amount, unit in pattern.findall(time_str):
        total_seconds += int(amount) * time_units[unit.lower()]
    return total_seconds

import discord
from datetime import datetime, timedelta

def create_embed(title: str, description: str, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.timestamp = datetime.utcnow()
    return embed

def create_success_embed(description: str):
    return create_embed("Success", description, discord.Color.green())

def create_error_embed(description: str):
    return create_embed("Error", description, discord.Color.red())

def format_relative_time(timestamp: datetime) -> str:
    now = datetime.utcnow()
    diff = now - timestamp
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        return f"{seconds // 60} minutes ago"
    elif seconds < 86400:
        return f"{seconds // 3600} hours ago"
    else:
        return f"{seconds // 86400} days ago"

def parse_time(time_str: str) -> int:
    """
    Converts a string like '1h30m' to total seconds.
    Supports d (days), h (hours), m (minutes), s (seconds).
    """
    time_str = time_str.lower()
    total_seconds = 0
    number = ''
    units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    for char in time_str:
        if char.isdigit():
            number += char
        elif char in units and number:
            total_seconds += int(number) * units[char]
            number = ''
        else:
            # Ignore or raise error if invalid char
            pass
    return total_seconds

def format_time(seconds: int) -> str:
    """
    Formats seconds into string like '1d 2h 3m 4s'
    """
    periods = [
        ('d', 86400),
        ('h', 3600),
        ('m', 60),
        ('s', 1)
    ]

    parts = []
    for suffix, length in periods:
        value, seconds = divmod(seconds, length)
        if value > 0:
            parts.append(f"{value}{suffix}")
    return ' '.join(parts) if parts else "0s"

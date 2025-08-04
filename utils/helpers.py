import discord

def create_embed(title: str, description: str, color: discord.Color = discord.Color.blurple()):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

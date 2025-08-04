# cogs/logging.py

import discord
from discord.ext import commands

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Optional: Add some real logging logic here

async def setup(bot):
    await bot.add_cog(Logging(bot))

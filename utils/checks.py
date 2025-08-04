import discord
from discord.ext import commands

def has_permissions(**perms):
    async def predicate(ctx):
        if not ctx.guild:
            return False
        return ctx.author.guild_permissions.is_superset(discord.Permissions(**perms))
    return commands.check(predicate)

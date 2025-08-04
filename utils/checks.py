import discord
from discord.ext import commands

def has_permissions(**perms):
    async def predicate(ctx):
        if not ctx.guild:
            return False
        return ctx.author.guild_permissions >= discord.Permissions(**perms)
    return commands.check(predicate)

def bot_has_permissions(**perms):
    async def predicate(ctx):
        if not ctx.guild:
            return False
        return ctx.me.guild_permissions >= discord.Permissions(**perms)
    return commands.check(predicate)

"""
Discord.py checks and permission utilities for advanced moderation
"""

import discord
from discord.ext import commands

def has_permissions(**perms):
    """Check if user has specific permissions"""
    def predicate(ctx):
        if not ctx.guild:
            return False
        return all(getattr(ctx.author.guild_permissions, perm, None) == value 
                  for perm, value in perms.items())
    return commands.check(predicate)

def is_owner():
    """Check if user is bot owner"""
    def predicate(ctx):
        return ctx.author.id == ctx.bot.owner_id
    return commands.check(predicate)

def is_mod():
    """Check if user is moderator"""
    def predicate(ctx):
        if not ctx.guild:
            return False
        
        # Check if server owner
        if ctx.author == ctx.guild.owner:
            return True
        
        # Check for admin permissions
        if ctx.author.guild_permissions.administrator:
            return True
        
        # Check for moderation permissions
        mod_perms = [
            ctx.author.guild_permissions.kick_members,
            ctx.author.guild_permissions.ban_members,
            ctx.author.guild_permissions.manage_messages,
            ctx.author.guild_permissions.manage_roles
        ]
        
        if any(mod_perms):
            return True
        
        # Check for mod roles
        mod_roles = ['moderator', 'mod', 'staff', 'admin']
        return any(role.name.lower() in mod_roles for role in ctx.author.roles)
    
    return commands.check(predicate)

def has_manage_guild():
    """Check if user can manage guild"""
    return has_permissions(manage_guild=True)

def has_ban_members():
    """Check if user can ban members"""
    return has_permissions(ban_members=True)

def has_kick_members():
    """Check if user can kick members"""
    return has_permissions(kick_members=True)

def has_manage_roles():
    """Check if user can manage roles"""
    return has_permissions(manage_roles=True)

def has_manage_messages():
    """Check if user can manage messages"""
    return has_permissions(manage_messages=True)
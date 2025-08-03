import discord
from discord.ext import commands
from functools import wraps

def has_permissions(**perms):
    """Check if user has required permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                user = interaction_or_ctx.user
                guild = interaction_or_ctx.guild
            else:
                user = interaction_or_ctx.author
                guild = interaction_or_ctx.guild
            
            if not guild:
                return await interaction_or_ctx.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            
            user_perms = user.guild_permissions
            
            missing_perms = []
            for perm, value in perms.items():
                if getattr(user_perms, perm) != value:
                    missing_perms.append(perm.replace('_', ' ').title())
            
            if missing_perms:
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message(
                        f"❌ You need the following permissions: {', '.join(missing_perms)}", 
                        ephemeral=True
                    )
                else:
                    await interaction_or_ctx.send(f"❌ You need the following permissions: {', '.join(missing_perms)}")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

def bot_has_permissions(**perms):
    """Check if bot has required permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                guild = interaction_or_ctx.guild
                bot_member = guild.me
            else:
                guild = interaction_or_ctx.guild
                bot_member = guild.me
            
            if not guild:
                return await interaction_or_ctx.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            
            bot_perms = bot_member.guild_permissions
            
            missing_perms = []
            for perm, value in perms.items():
                if getattr(bot_perms, perm) != value:
                    missing_perms.append(perm.replace('_', ' ').title())
            
            if missing_perms:
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message(
                        f"❌ I need the following permissions: {', '.join(missing_perms)}", 
                        ephemeral=True
                    )
                else:
                    await interaction_or_ctx.send(f"❌ I need the following permissions: {', '.join(missing_perms)}")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

def is_owner():
    """Check if user is bot owner"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                user = interaction_or_ctx.user
                bot = interaction_or_ctx.client
            else:
                user = interaction_or_ctx.author
                bot = interaction_or_ctx.bot
            
            app_info = await bot.application_info()
            
            if user.id != app_info.owner.id:
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
                else:
                    await interaction_or_ctx.send("❌ Only the bot owner can use this command.")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

def is_admin():
    """Check if user is server administrator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                user = interaction_or_ctx.user
                guild = interaction_or_ctx.guild
            else:
                user = interaction_or_ctx.author
                guild = interaction_or_ctx.guild
            
            if not guild:
                return await interaction_or_ctx.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            
            if not user.guild_permissions.administrator and user.id != guild.owner_id:
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message("❌ You need Administrator permission to use this command.", ephemeral=True)
                else:
                    await interaction_or_ctx.send("❌ You need Administrator permission to use this command.")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

def is_moderator():
    """Check if user is a moderator (has kick/ban permissions)"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                user = interaction_or_ctx.user
                guild = interaction_or_ctx.guild
            else:
                user = interaction_or_ctx.author
                guild = interaction_or_ctx.guild
            
            if not guild:
                return await interaction_or_ctx.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            
            user_perms = user.guild_permissions
            is_mod = (user_perms.kick_members or user_perms.ban_members or 
                     user_perms.manage_messages or user_perms.administrator or
                     user.id == guild.owner_id)
            
            if not is_mod:
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message("❌ You need moderation permissions to use this command.", ephemeral=True)
                else:
                    await interaction_or_ctx.send("❌ You need moderation permissions to use this command.")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

def cooldown(rate: int, per: float, type=commands.BucketType.user):
    """Apply cooldown to commands"""
    def decorator(func):
        if hasattr(func, '__commands_cooldown__'):
            func.__commands_cooldown__ = commands.Cooldown(rate, per)
        else:
            func = commands.cooldown(rate, per, type)(func)
        return func
    return decorator

def guild_only():
    """Ensure command is only used in guilds"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                guild = interaction_or_ctx.guild
            else:
                guild = interaction_or_ctx.guild
            
            if not guild:
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
                else:
                    await interaction_or_ctx.send("❌ This command can only be used in a server.")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

def dm_only():
    """Ensure command is only used in DMs"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                guild = interaction_or_ctx.guild
            else:
                guild = interaction_or_ctx.guild
            
            if guild:
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message("❌ This command can only be used in DMs.", ephemeral=True)
                else:
                    await interaction_or_ctx.send("❌ This command can only be used in DMs.")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

def has_role(*role_names):
    """Check if user has any of the specified roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                user = interaction_or_ctx.user
                guild = interaction_or_ctx.guild
            else:
                user = interaction_or_ctx.author
                guild = interaction_or_ctx.guild
            
            if not guild:
                return await interaction_or_ctx.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            
            user_roles = [role.name.lower() for role in user.roles]
            required_roles = [name.lower() for name in role_names]
            
            if not any(role in user_roles for role in required_roles):
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message(
                        f"❌ You need one of the following roles: {', '.join(role_names)}", 
                        ephemeral=True
                    )
                else:
                    await interaction_or_ctx.send(f"❌ You need one of the following roles: {', '.join(role_names)}")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

def in_channel(*channel_names):
    """Check if command is used in specific channels"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction_or_ctx, *args, **kwargs):
            if isinstance(interaction_or_ctx, discord.Interaction):
                channel = interaction_or_ctx.channel
            else:
                channel = interaction_or_ctx.channel
            
            channel_names_lower = [name.lower() for name in channel_names]
            
            if channel.name.lower() not in channel_names_lower:
                if isinstance(interaction_or_ctx, discord.Interaction):
                    await interaction_or_ctx.response.send_message(
                        f"❌ This command can only be used in: {', '.join(channel_names)}", 
                        ephemeral=True
                    )
                else:
                    await interaction_or_ctx.send(f"❌ This command can only be used in: {', '.join(channel_names)}")
                return
            
            return await func(self, interaction_or_ctx, *args, **kwargs)
        return wrapper
    return decorator

"""
Mute command for Discord moderation bot.
"""

import discord
from discord.ext import commands
from utils.permissions import has_moderation_permissions
from utils.logging_config import setup_logging

logger = setup_logging()

class MuteCommand(commands.Cog):
    """Mute command cog."""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def get_or_create_muted_role(self, guild):
        """Get or create the muted role."""
        # Look for existing muted role
        muted_role = discord.utils.get(guild.roles, name="Muted")
        
        if muted_role is None:
            # Create muted role
            try:
                muted_role = await guild.create_role(
                    name="Muted",
                    color=discord.Color(0x818386),
                    reason="Auto-created muted role for moderation"
                )
                
                # Set permissions for all channels
                for channel in guild.channels:
                    try:
                        if isinstance(channel, discord.TextChannel):
                            await channel.set_permissions(
                                muted_role,
                                send_messages=False,
                                add_reactions=False,
                                speak=False,
                                reason="Setting up muted role permissions"
                            )
                        elif isinstance(channel, discord.VoiceChannel):
                            await channel.set_permissions(
                                muted_role,
                                speak=False,
                                stream=False,
                                reason="Setting up muted role permissions"
                            )
                    except discord.Forbidden:
                        continue
                        
            except discord.Forbidden:
                return None
        
        return muted_role
    
    @commands.command(name='mute')
    @commands.guild_only()
    async def mute_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Mute a user in the server.
        
        Usage: !mute @user [reason]
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to mute members.")
            return
        
        # Check if bot has manage roles permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("❌ I don't have permission to manage roles.")
            return
        
        # Can't mute yourself
        if member == ctx.author:
            await ctx.send("❌ You cannot mute yourself.")
            return
        
        # Can't mute the bot
        if member == ctx.guild.me:
            await ctx.send("❌ I cannot mute myself.")
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot mute someone with a higher or equal role.")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot mute someone with a higher or equal role than me.")
            return
        
        try:
            # Get or create muted role
            muted_role = await self.get_or_create_muted_role(ctx.guild)
            
            if muted_role is None:
                await ctx.send("❌ I couldn't create or find the muted role. Please check my permissions.")
                return
            
            # Check if user is already muted
            if muted_role in member.roles:
                await ctx.send(f"❌ **{member}** is already muted.")
                return
            
            # Add muted role
            await member.add_roles(muted_role, reason=f"{reason} | Muted by {ctx.author}")
            
            # Try to send DM to user
            try:
                embed = discord.Embed(
                    title="🔇 You have been muted",
                    description=f"You have been muted in **{ctx.guild.name}**",
                    color=0x808080
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Muted",
                description=f"**{member}** has been muted",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} muted {member} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to mute user: {e}")
        except Exception as e:
            logger.error(f"Error in mute command: {e}")
            await ctx.send("❌ An error occurred while trying to mute the user.")
    
    @commands.command(name='unmute')
    @commands.guild_only()
    async def unmute_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Unmute a user in the server.
        
        Usage: !unmute @user [reason]
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to unmute members.")
            return
        
        # Check if bot has manage roles permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("❌ I don't have permission to manage roles.")
            return
        
        try:
            # Get muted role
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            
            if muted_role is None:
                await ctx.send("❌ No muted role found in this server.")
                return
            
            # Check if user is actually muted
            if muted_role not in member.roles:
                await ctx.send(f"❌ **{member}** is not muted.")
                return
            
            # Remove muted role
            await member.remove_roles(muted_role, reason=f"{reason} | Unmuted by {ctx.author}")
            
            # Try to send DM to user
            try:
                embed = discord.Embed(
                    title="🔊 You have been unmuted",
                    description=f"You have been unmuted in **{ctx.guild.name}**",
                    color=0x00ff00
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Unmuted",
                description=f"**{member}** has been unmuted",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} unmuted {member} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unmute this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to unmute user: {e}")
        except Exception as e:
            logger.error(f"Error in unmute command: {e}")
            await ctx.send("❌ An error occurred while trying to unmute the user.")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(MuteCommand(bot))

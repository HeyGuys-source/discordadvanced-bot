"""
Ban command for Discord moderation bot.
"""

import discord
from discord.ext import commands
from utils.permissions import has_moderation_permissions
from utils.logging_config import setup_logging

logger = setup_logging()

class BanCommand(commands.Cog):
    """Ban command cog."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='ban')
    @commands.guild_only()
    async def ban_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Ban a user from the server.
        
        Usage: !ban @user [reason]
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to ban members.")
            return
        
        # Check if bot has ban permissions
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("❌ I don't have permission to ban members.")
            return
        
        # Can't ban yourself
        if member == ctx.author:
            await ctx.send("❌ You cannot ban yourself.")
            return
        
        # Can't ban the bot
        if member == ctx.guild.me:
            await ctx.send("❌ I cannot ban myself.")
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot ban someone with a higher or equal role.")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot ban someone with a higher or equal role than me.")
            return
        
        try:
            # Try to send DM to user before banning
            try:
                embed = discord.Embed(
                    title="🔨 You have been banned",
                    description=f"You have been banned from **{ctx.guild.name}**",
                    color=0xff0000
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Ban the user
            await member.ban(reason=f"{reason} | Banned by {ctx.author}")
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Banned",
                description=f"**{member}** has been banned",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} banned {member} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to ban user: {e}")
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await ctx.send("❌ An error occurred while trying to ban the user.")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(BanCommand(bot))

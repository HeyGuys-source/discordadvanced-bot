"""
Kick command for Discord moderation bot.
"""

import discord
from discord.ext import commands
from utils.permissions import has_moderation_permissions
from utils.logging_config import setup_logging

logger = setup_logging()

class KickCommand(commands.Cog):
    """Kick command cog."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='kick')
    @commands.guild_only()
    async def kick_user(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Kick a user from the server.
        
        Usage: !kick @user [reason]
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to kick members.")
            return
        
        # Check if bot has kick permissions
        if not ctx.guild.me.guild_permissions.kick_members:
            await ctx.send("❌ I don't have permission to kick members.")
            return
        
        # Can't kick yourself
        if member == ctx.author:
            await ctx.send("❌ You cannot kick yourself.")
            return
        
        # Can't kick the bot
        if member == ctx.guild.me:
            await ctx.send("❌ I cannot kick myself.")
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot kick someone with a higher or equal role.")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot kick someone with a higher or equal role than me.")
            return
        
        try:
            # Try to send DM to user before kicking
            try:
                embed = discord.Embed(
                    title="👢 You have been kicked",
                    description=f"You have been kicked from **{ctx.guild.name}**",
                    color=0xffa500
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Kick the user
            await member.kick(reason=f"{reason} | Kicked by {ctx.author}")
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Kicked",
                description=f"**{member}** has been kicked",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} kicked {member} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to kick user: {e}")
        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            await ctx.send("❌ An error occurred while trying to kick the user.")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(KickCommand(bot))

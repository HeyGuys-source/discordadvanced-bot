"""
Unban command for Discord moderation bot.
"""

import discord
from discord.ext import commands
from utils.permissions import has_moderation_permissions
from utils.logging_config import setup_logging

logger = setup_logging()

class UnbanCommand(commands.Cog):
    """Unban command cog."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='unban')
    @commands.guild_only()
    async def unban_user(self, ctx, user_id: int, *, reason="No reason provided"):
        """
        Unban a user from the server.
        
        Usage: !unban <user_id> [reason]
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to unban members.")
            return
        
        # Check if bot has ban permissions
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("❌ I don't have permission to unban members.")
            return
        
        try:
            # Get user object
            user = await self.bot.fetch_user(user_id)
            
            # Check if user is actually banned
            try:
                ban_entry = await ctx.guild.fetch_ban(user)
            except discord.NotFound:
                await ctx.send(f"❌ **{user}** is not banned from this server.")
                return
            
            # Unban the user
            await ctx.guild.unban(user, reason=f"{reason} | Unbanned by {ctx.author}")
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"**{user}** has been unbanned",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} unbanned {user} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.NotFound:
            await ctx.send("❌ User not found. Please provide a valid user ID.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unban this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to unban user: {e}")
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            await ctx.send("❌ An error occurred while trying to unban the user.")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(UnbanCommand(bot))

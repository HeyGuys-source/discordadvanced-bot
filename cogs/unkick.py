"""
Unkick command for Discord moderation bot.
Note: Unkick is essentially sending an invite to rejoin the server.
"""

import discord
from discord.ext import commands
from utils.permissions import has_moderation_permissions
from utils.logging_config import setup_logging

logger = setup_logging()

class UnkickCommand(commands.Cog):
    """Unkick command cog."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='unkick')
    @commands.guild_only()
    async def unkick_user(self, ctx, user_id: int, *, reason="No reason provided"):
        """
        Create an invite for a previously kicked user.
        
        Usage: !unkick <user_id> [reason]
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to unkick members.")
            return
        
        # Check if bot has invite permissions
        if not ctx.guild.me.guild_permissions.create_instant_invite:
            await ctx.send("❌ I don't have permission to create invites.")
            return
        
        try:
            # Get user object
            user = await self.bot.fetch_user(user_id)
            
            # Check if user is in the server
            member = ctx.guild.get_member(user_id)
            if member:
                await ctx.send(f"❌ **{user}** is already in the server.")
                return
            
            # Create an invite
            invite = await ctx.channel.create_invite(
                max_uses=1,
                max_age=86400,  # 24 hours
                unique=True,
                reason=f"Unkick invite for {user} | Created by {ctx.author}"
            )
            
            # Try to send DM to user with invite
            try:
                embed = discord.Embed(
                    title="🔄 You've been invited back",
                    description=f"You have been invited back to **{ctx.guild.name}**",
                    color=0x00ff00
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                embed.add_field(name="Invite Link", value=invite.url, inline=False)
                embed.add_field(name="Expires", value="24 hours", inline=False)
                
                await user.send(embed=embed)
                dm_sent = True
            except discord.Forbidden:
                dm_sent = False
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Unkick Invite Created",
                description=f"Invite created for **{user}**",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            embed.add_field(name="Invite Link", value=invite.url, inline=False)
            embed.add_field(name="DM Sent", value="✅ Yes" if dm_sent else "❌ No (DMs disabled)", inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} created unkick invite for {user} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.NotFound:
            await ctx.send("❌ User not found. Please provide a valid user ID.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create invites or contact this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to create invite: {e}")
        except Exception as e:
            logger.error(f"Error in unkick command: {e}")
            await ctx.send("❌ An error occurred while trying to create the unkick invite.")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(UnkickCommand(bot))

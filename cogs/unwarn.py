"""
Unwarn command for Discord moderation bot.
"""

import discord
from discord.ext import commands
import json
from utils.permissions import has_moderation_permissions
from utils.logging_config import setup_logging

logger = setup_logging()

class UnwarnCommand(commands.Cog):
    """Unwarn command cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = 'data/warnings.json'
    
    def load_warnings(self):
        """Load warnings from JSON file."""
        try:
            with open(self.warnings_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_warnings(self, warnings):
        """Save warnings to JSON file."""
        with open(self.warnings_file, 'w') as f:
            json.dump(warnings, f, indent=2)
    
    @commands.command(name='unwarn')
    @commands.guild_only()
    async def unwarn_user(self, ctx, member: discord.Member, warning_id: int, *, reason="No reason provided"):
        """
        Remove a specific warning from a user.
        
        Usage: !unwarn @user <warning_id> [reason]
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to remove warnings.")
            return
        
        try:
            # Load warnings
            warnings = self.load_warnings()
            
            guild_id = str(ctx.guild.id)
            user_id = str(member.id)
            
            # Check if guild and user have warnings
            if guild_id not in warnings or user_id not in warnings[guild_id]:
                await ctx.send(f"❌ **{member}** has no warnings to remove.")
                return
            
            user_warnings = warnings[guild_id][user_id]
            
            # Find warning with the given ID
            warning_to_remove = None
            warning_index = None
            
            for index, warning in enumerate(user_warnings):
                if warning['id'] == warning_id:
                    warning_to_remove = warning
                    warning_index = index
                    break
            
            if warning_to_remove is None:
                await ctx.send(f"❌ Warning ID {warning_id} not found for **{member}**.")
                return
            
            # Remove the warning
            user_warnings.pop(warning_index)
            
            # If no warnings left, remove user entry
            if not user_warnings:
                del warnings[guild_id][user_id]
                
                # If no users left in guild, remove guild entry
                if not warnings[guild_id]:
                    del warnings[guild_id]
            
            # Save updated warnings
            self.save_warnings(warnings)
            
            # Try to send DM to user
            try:
                embed = discord.Embed(
                    title="✅ Warning Removed",
                    description=f"A warning has been removed from your record in **{ctx.guild.name}**",
                    color=0x00ff00
                )
                embed.add_field(name="Removed Warning", value=warning_to_remove['reason'], inline=False)
                embed.add_field(name="Removal Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Warning Removed",
                description=f"Warning #{warning_id} removed from **{member}**",
                color=0x00ff00
            )
            embed.add_field(name="Original Warning", value=warning_to_remove['reason'], inline=False)
            embed.add_field(name="Original Moderator", value=warning_to_remove.get('moderator_name', 'Unknown'), inline=False)
            embed.add_field(name="Removal Reason", value=reason, inline=False)
            embed.add_field(name="Removed by", value=ctx.author.mention, inline=False)
            
            # Show remaining warnings count
            remaining_warnings = len(warnings.get(guild_id, {}).get(user_id, []))
            embed.add_field(name="Remaining Warnings", value=remaining_warnings, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} removed warning #{warning_id} from {member} in {ctx.guild.name}. Reason: {reason}")
            
        except ValueError:
            await ctx.send("❌ Warning ID must be a number.")
        except Exception as e:
            logger.error(f"Error in unwarn command: {e}")
            await ctx.send("❌ An error occurred while trying to remove the warning.")
    
    @commands.command(name='clearwarnings')
    @commands.guild_only()
    async def clear_warnings(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Clear all warnings for a user.
        
        Usage: !clearwarnings @user [reason]
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to clear warnings.")
            return
        
        try:
            # Load warnings
            warnings = self.load_warnings()
            
            guild_id = str(ctx.guild.id)
            user_id = str(member.id)
            
            # Check if guild and user have warnings
            if guild_id not in warnings or user_id not in warnings[guild_id]:
                await ctx.send(f"❌ **{member}** has no warnings to clear.")
                return
            
            user_warnings = warnings[guild_id][user_id]
            warning_count = len(user_warnings)
            
            # Remove all warnings for the user
            del warnings[guild_id][user_id]
            
            # If no users left in guild, remove guild entry
            if not warnings[guild_id]:
                del warnings[guild_id]
            
            # Save updated warnings
            self.save_warnings(warnings)
            
            # Try to send DM to user
            try:
                embed = discord.Embed(
                    title="✅ All Warnings Cleared",
                    description=f"All your warnings have been cleared in **{ctx.guild.name}**",
                    color=0x00ff00
                )
                embed.add_field(name="Cleared Warnings", value=warning_count, inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ All Warnings Cleared",
                description=f"All warnings cleared for **{member}**",
                color=0x00ff00
            )
            embed.add_field(name="Cleared Warnings", value=warning_count, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} cleared all {warning_count} warnings from {member} in {ctx.guild.name}. Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error in clearwarnings command: {e}")
            await ctx.send("❌ An error occurred while trying to clear warnings.")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(UnwarnCommand(bot))

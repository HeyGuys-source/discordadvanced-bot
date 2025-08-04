"""
Warn command for Discord moderation bot.
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from utils.permissions import has_moderation_permissions
from utils.logging_config import setup_logging

logger = setup_logging()

class WarnCommand(commands.Cog):
    """Warn command cog."""
    
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
        os.makedirs('data', exist_ok=True)
        with open(self.warnings_file, 'w') as f:
            json.dump(warnings, f, indent=2)
    
    @commands.command(name='warn')
    @commands.guild_only()
    async def warn_user(self, ctx, member: discord.Member, *, reason):
        """
        Warn a user with a required reason.
        
        Usage: !warn @user <reason>
        """
        
        # Check if the command user has moderation permissions
        if not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to warn members.")
            return
        
        # Can't warn yourself
        if member == ctx.author:
            await ctx.send("❌ You cannot warn yourself.")
            return
        
        # Can't warn the bot
        if member == ctx.guild.me:
            await ctx.send("❌ I cannot warn myself.")
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot warn someone with a higher or equal role.")
            return
        
        try:
            # Load existing warnings
            warnings = self.load_warnings()
            
            # Initialize guild and user data if not exists
            guild_id = str(ctx.guild.id)
            user_id = str(member.id)
            
            if guild_id not in warnings:
                warnings[guild_id] = {}
            
            if user_id not in warnings[guild_id]:
                warnings[guild_id][user_id] = []
            
            # Create warning entry
            warning_data = {
                'id': len(warnings[guild_id][user_id]) + 1,
                'reason': reason,
                'moderator': str(ctx.author.id),
                'moderator_name': str(ctx.author),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add warning
            warnings[guild_id][user_id].append(warning_data)
            
            # Save warnings
            self.save_warnings(warnings)
            
            # Get total warnings count
            total_warnings = len(warnings[guild_id][user_id])
            
            # Try to send DM to user
            try:
                embed = discord.Embed(
                    title="⚠️ You have been warned",
                    description=f"You have been warned in **{ctx.guild.name}**",
                    color=0xffff00
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                embed.add_field(name="Total Warnings", value=total_warnings, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Warned",
                description=f"**{member}** has been warned",
                color=0x00ff00
            )
            embed.add_field(name="Warning ID", value=warning_data['id'], inline=True)
            embed.add_field(name="Total Warnings", value=total_warnings, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} warned {member} in {ctx.guild.name}. Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error in warn command: {e}")
            await ctx.send("❌ An error occurred while trying to warn the user.")
    
    @commands.command(name='warnings')
    @commands.guild_only()
    async def list_warnings(self, ctx, member: discord.Member | None = None):
        """
        List warnings for a user.
        
        Usage: !warnings [@user]
        """
        
        if member is None:
            member = ctx.author
        
        # Check permissions if checking someone else's warnings
        if member != ctx.author and not has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to view other members' warnings.")
            return
        
        try:
            # Load warnings
            warnings = self.load_warnings()
            
            guild_id = str(ctx.guild.id)
            user_id = str(member.id)
            
            # Get user warnings
            user_warnings = warnings.get(guild_id, {}).get(user_id, [])
            
            if not user_warnings:
                await ctx.send(f"✅ **{member}** has no warnings.")
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"⚠️ Warnings for {member}",
                description=f"Total warnings: {len(user_warnings)}",
                color=0xffff00
            )
            
            # Add warning fields (limit to last 10)
            for warning in user_warnings[-10:]:
                moderator_name = warning.get('moderator_name', 'Unknown')
                timestamp = warning.get('timestamp', 'Unknown')
                
                # Parse timestamp for better display
                try:
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except:
                    formatted_time = timestamp
                
                embed.add_field(
                    name=f"Warning #{warning['id']}",
                    value=f"**Reason:** {warning['reason']}\n**Moderator:** {moderator_name}\n**Date:** {formatted_time}",
                    inline=False
                )
            
            if len(user_warnings) > 10:
                embed.set_footer(text="Showing last 10 warnings only")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in warnings command: {e}")
            await ctx.send("❌ An error occurred while retrieving warnings.")

async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(WarnCommand(bot))

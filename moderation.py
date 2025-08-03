import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import asyncio
from datetime import datetime, timedelta
from utils.checks import has_permissions, bot_has_permissions
from utils.helpers import parse_time, format_time

class Moderation(commands.Cog):
    """Moderation commands for managing server members"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for the kick"
    )
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ You don't have permission to kick members.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message("❌ I don't have permission to kick members.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You can't kick someone with a higher or equal role.", ephemeral=True)
            return
        
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I can't kick someone with a higher or equal role.", ephemeral=True)
            return
        
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't kick yourself.", ephemeral=True)
            return
        
        try:
            # Send DM to user before kicking
            try:
                embed = discord.Embed(
                    title="You have been kicked",
                    description=f"You were kicked from **{interaction.guild.name}**",
                    color=0xED4245
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                await member.send(embed=embed)
            except:
                pass  # User has DMs disabled
            
            await member.kick(reason=f"{reason} | Moderator: {interaction.user}")
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                member.id,
                interaction.user.id,
                "kick",
                reason
            )
            
            embed = discord.Embed(
                title="Member Kicked",
                description=f"**{member}** has been kicked from the server.",
                color=0xED4245
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for the ban",
        delete_days="Number of days of messages to delete (0-7)"
    )
    async def ban(self, interaction: discord.Interaction, member: discord.Member, 
                  reason: str = "No reason provided", delete_days: int = 0):
        """Ban a member from the server"""
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You don't have permission to ban members.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("❌ I don't have permission to ban members.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You can't ban someone with a higher or equal role.", ephemeral=True)
            return
        
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I can't ban someone with a higher or equal role.", ephemeral=True)
            return
        
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't ban yourself.", ephemeral=True)
            return
        
        if delete_days < 0 or delete_days > 7:
            await interaction.response.send_message("❌ Delete days must be between 0 and 7.", ephemeral=True)
            return
        
        try:
            # Send DM to user before banning
            try:
                embed = discord.Embed(
                    title="You have been banned",
                    description=f"You were banned from **{interaction.guild.name}**",
                    color=0xED4245
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                await member.send(embed=embed)
            except:
                pass  # User has DMs disabled
            
            await member.ban(reason=f"{reason} | Moderator: {interaction.user}", delete_message_days=delete_days)
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                member.id,
                interaction.user.id,
                "ban",
                reason
            )
            
            embed = discord.Embed(
                title="Member Banned",
                description=f"**{member}** has been banned from the server.",
                color=0xED4245
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            if delete_days > 0:
                embed.add_field(name="Messages Deleted", value=f"{delete_days} days", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(
        user_id="The ID of the user to unban",
        reason="Reason for the unban"
    )
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        """Unban a user from the server"""
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You don't have permission to unban members.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("❌ I don't have permission to unban members.", ephemeral=True)
            return
        
        try:
            user_id = int(user_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
            return
        
        try:
            user = await self.bot.fetch_user(user_id)
            await interaction.guild.unban(user, reason=f"{reason} | Moderator: {interaction.user}")
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                user.id,
                interaction.user.id,
                "unban",
                reason
            )
            
            embed = discord.Embed(
                title="Member Unbanned",
                description=f"**{user}** has been unbanned from the server.",
                color=0x57F287
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found or not banned.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unban users.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(
        member="The member to timeout",
        duration="Duration of the timeout (e.g., 10m, 1h, 1d)",
        reason="Reason for the timeout"
    )
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, 
                     duration: str, reason: str = "No reason provided"):
        """Timeout a member"""
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ You don't have permission to timeout members.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ I don't have permission to timeout members.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You can't timeout someone with a higher or equal role.", ephemeral=True)
            return
        
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I can't timeout someone with a higher or equal role.", ephemeral=True)
            return
        
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't timeout yourself.", ephemeral=True)
            return
        
        # Parse duration
        timeout_duration = parse_time(duration)
        if not timeout_duration:
            await interaction.response.send_message("❌ Invalid duration format. Use formats like `10m`, `1h`, `1d`.", ephemeral=True)
            return
        
        if timeout_duration > timedelta(days=28):
            await interaction.response.send_message("❌ Timeout duration cannot exceed 28 days.", ephemeral=True)
            return
        
        try:
            until = discord.utils.utcnow() + timeout_duration
            await member.timeout(until, reason=f"{reason} | Moderator: {interaction.user}")
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                member.id,
                interaction.user.id,
                "timeout",
                reason,
                int(timeout_duration.total_seconds())
            )
            
            embed = discord.Embed(
                title="Member Timed Out",
                description=f"**{member}** has been timed out.",
                color=0xFEE75C
            )
            embed.add_field(name="Duration", value=format_time(timeout_duration), inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to timeout this member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.describe(
        member="The member to remove timeout from",
        reason="Reason for removing the timeout"
    )
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Remove timeout from a member"""
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ You don't have permission to manage timeouts.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ I don't have permission to manage timeouts.", ephemeral=True)
            return
        
        if not member.is_timed_out():
            await interaction.response.send_message("❌ This member is not timed out.", ephemeral=True)
            return
        
        try:
            await member.timeout(None, reason=f"{reason} | Moderator: {interaction.user}")
            
            # Log to database
            await self.bot.db.add_moderation_log(
                interaction.guild.id,
                member.id,
                interaction.user.id,
                "untimeout",
                reason
            )
            
            embed = discord.Embed(
                title="Timeout Removed",
                description=f"**{member}**'s timeout has been removed.",
                color=0x57F287
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to remove timeout from this member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(
        member="The member to warn",
        reason="Reason for the warning"
    )
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        """Warn a member"""
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ You don't have permission to warn members.", ephemeral=True)
            return
        
        if member == interaction.user:
            await interaction.response.send_message("❌ You can't warn yourself.", ephemeral=True)
            return
        
        # Add warning to database
        await self.bot.db.add_warning(interaction.guild.id, member.id, interaction.user.id, reason)
        
        # Get total warnings for user
        warnings = await self.bot.db.get_user_warnings(interaction.guild.id, member.id)
        warning_count = len(warnings)
        
        # Send DM to user
        try:
            embed = discord.Embed(
                title="You have been warned",
                description=f"You received a warning in **{interaction.guild.name}**",
                color=0xFEE75C
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            embed.add_field(name="Total Warnings", value=str(warning_count), inline=False)
            await member.send(embed=embed)
        except:
            pass  # User has DMs disabled
        
        embed = discord.Embed(
            title="Member Warned",
            description=f"**{member}** has been warned.",
            color=0xFEE75C
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        embed.add_field(name="Total Warnings", value=str(warning_count), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="warnings", description="View warnings for a member")
    @app_commands.describe(member="The member to view warnings for")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        """View warnings for a member"""
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ You don't have permission to view warnings.", ephemeral=True)
            return
        
        warnings = await self.bot.db.get_user_warnings(interaction.guild.id, member.id)
        
        if not warnings:
            await interaction.response.send_message(f"**{member}** has no warnings.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"Warnings for {member}",
            description=f"Total warnings: **{len(warnings)}**",
            color=0xFEE75C
        )
        
        for i, warning in enumerate(warnings[:10], 1):  # Show last 10 warnings
            moderator = interaction.guild.get_member(warning['moderator_id'])
            moderator_name = moderator.mention if moderator else f"<@{warning['moderator_id']}>"
            
            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Reason:** {warning['reason']}\n**Moderator:** {moderator_name}\n**Date:** <t:{int(datetime.fromisoformat(warning['created_at']).timestamp())}:R>",
                inline=False
            )
        
        if len(warnings) > 10:
            embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="purge", description="Delete multiple messages")
    @app_commands.describe(
        amount="Number of messages to delete (1-100)",
        member="Only delete messages from this member"
    )
    async def purge(self, interaction: discord.Interaction, amount: int, member: Optional[discord.Member] = None):
        """Delete multiple messages"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You don't have permission to manage messages.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ I don't have permission to manage messages.", ephemeral=True)
            return
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            def check(message):
                if member:
                    return message.author == member
                return True
            
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            embed = discord.Embed(
                title="Messages Purged",
                description=f"Successfully deleted **{len(deleted)}** messages.",
                color=0x57F287
            )
            if member:
                embed.add_field(name="Target", value=member.mention, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to delete messages.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))

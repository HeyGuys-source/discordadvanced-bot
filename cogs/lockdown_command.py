import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging
import asyncio

class LockdownCommand(commands.Cog):
    """Advanced lockdown command with decorative elements and temporary lock functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        self.locked_channels = {}  # Store original permissions for restoration
        
    @app_commands.command(name="lockdown", description="🔒 Temporarily lock a channel with advanced controls")
    @app_commands.describe(
        channel="Channel to lock (defaults to current channel)",
        duration="Duration in minutes (optional - permanent if not specified)",
        reason="Reason for lockdown"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lockdown(
        self, 
        interaction: discord.Interaction, 
        channel: Optional[discord.TextChannel] = None,
        duration: Optional[int] = None,
        reason: Optional[str] = None
    ):
        """
        Advanced lockdown command with temporary lock functionality.
        
        Args:
            interaction: Discord interaction object
            channel: Target channel to lock
            duration: Optional duration in minutes
            reason: Optional reason for lockdown
        """
        try:
            # Use current channel if none specified
            target_channel = channel or interaction.channel
            
            # Validate permissions
            if not target_channel.permissions_for(interaction.guild.me).manage_channels:
                embed = discord.Embed(
                    title="❌ Permission Error",
                    description="I don't have permission to manage channels in the specified channel.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text="Missing: Manage Channels permission")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if channel is already locked
            if target_channel.id in self.locked_channels:
                embed = discord.Embed(
                    title="⚠️ Already Locked",
                    description=f"{target_channel.mention} is already in lockdown mode.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Tip",
                    value="Use `/unlock` to remove the lockdown first.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Validate duration if provided
            if duration is not None and (duration <= 0 or duration > 10080):  # Max 1 week
                embed = discord.Embed(
                    title="⚠️ Invalid Duration",
                    description="Duration must be between **1** and **10080** minutes (1 week).",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Quick Reference",
                    value="• **60** = 1 hour\n• **360** = 6 hours\n• **1440** = 1 day\n• **10080** = 1 week",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Store original permissions
            original_overwrites = {}
            for target, overwrite in target_channel.overwrites.items():
                original_overwrites[target] = overwrite
            
            self.locked_channels[target_channel.id] = {
                'original_overwrites': original_overwrites,
                'locked_by': interaction.user.id,
                'locked_at': discord.utils.utcnow(),
                'reason': reason,
                'duration': duration
            }
            
            # Apply lockdown - deny send_messages for @everyone
            everyone_role = interaction.guild.default_role
            overwrite = target_channel.overwrites_for(everyone_role)
            overwrite.send_messages = False
            overwrite.add_reactions = False
            overwrite.create_public_threads = False
            overwrite.create_private_threads = False
            
            await target_channel.set_permissions(
                everyone_role, 
                overwrite=overwrite,
                reason=f"Lockdown by {interaction.user} ({interaction.user.id})" + 
                       (f" - {reason}" if reason else "")
            )
            
            # Create lockdown embed
            embed = discord.Embed(
                title="🔒 Channel Locked Down",
                description=f"**{target_channel.mention}** has been secured and locked.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="🛡️ Security Level",
                value="**HIGH** - All message sending disabled",
                inline=True
            )
            
            if duration:
                embed.add_field(
                    name="⏱️ Duration",
                    value=f"**{duration}** minute{'s' if duration != 1 else ''}",
                    inline=True
                )
                embed.add_field(
                    name="🔓 Auto-Unlock",
                    value=f"<t:{int((discord.utils.utcnow().timestamp()) + (duration * 60))}:R>",
                    inline=True
                )
            else:
                embed.add_field(
                    name="⏱️ Duration",
                    value="**Permanent** (until manually unlocked)",
                    inline=True
                )
            
            embed.add_field(
                name="📋 Restrictions",
                value="• No sending messages\n• No adding reactions\n• No creating threads\n• Only staff can interact",
                inline=False
            )
            
            if reason:
                embed.add_field(name="📝 Reason", value=reason, inline=False)
            
            embed.set_footer(
                text=f"Locked by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Schedule auto-unlock if duration is specified
            if duration:
                await self._schedule_unlock(target_channel, duration)
            
            # Log the action
            logging.info(
                f"Channel locked by {interaction.user} ({interaction.user.id}) "
                f"in {target_channel.name} ({target_channel.id})" +
                (f" for {duration} minutes" if duration else " permanently")
            )
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="I don't have permission to modify channel permissions.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Required permission: Manage Channels")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An unexpected error occurred during lockdown.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Unexpected error in lockdown command: {e}", exc_info=True)
    
    @app_commands.command(name="unlock", description="🔓 Remove lockdown from a channel")
    @app_commands.describe(
        channel="Channel to unlock (defaults to current channel)",
        reason="Reason for unlocking"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(
        self, 
        interaction: discord.Interaction, 
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None
    ):
        """Unlock a previously locked channel."""
        try:
            target_channel = channel or interaction.channel
            
            if target_channel.id not in self.locked_channels:
                embed = discord.Embed(
                    title="⚠️ Not Locked",
                    description=f"{target_channel.mention} is not currently in lockdown.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Restore original permissions
            lock_data = self.locked_channels[target_channel.id]
            
            # Clear all overwrites and restore originals
            await target_channel.edit(overwrites=lock_data['original_overwrites'])
            
            # Remove from locked channels
            del self.locked_channels[target_channel.id]
            
            # Create unlock embed
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"**{target_channel.mention}** has been restored and unlocked.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="✅ Status",
                value="**RESTORED** - Normal permissions restored",
                inline=True
            )
            
            locked_duration = discord.utils.utcnow() - lock_data['locked_at']
            hours, remainder = divmod(int(locked_duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            duration_str = ""
            if hours > 0:
                duration_str += f"{hours}h "
            if minutes > 0:
                duration_str += f"{minutes}m "
            duration_str += f"{seconds}s"
            
            embed.add_field(
                name="⏱️ Was Locked For",
                value=duration_str,
                inline=True
            )
            
            if reason:
                embed.add_field(name="📝 Unlock Reason", value=reason, inline=False)
            
            embed.set_footer(
                text=f"Unlocked by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
            logging.info(f"Channel unlocked by {interaction.user} in {target_channel.name}")
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unlock Error",
                description="An error occurred while unlocking the channel.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in unlock command: {e}", exc_info=True)
    
    async def _schedule_unlock(self, channel: discord.TextChannel, duration_minutes: int):
        """Schedule automatic unlock after specified duration."""
        await asyncio.sleep(duration_minutes * 60)
        
        if channel.id in self.locked_channels:
            try:
                # Restore permissions
                lock_data = self.locked_channels[channel.id]
                await channel.edit(overwrites=lock_data['original_overwrites'])
                del self.locked_channels[channel.id]
                
                # Send auto-unlock notification
                embed = discord.Embed(
                    title="🔓 Automatic Unlock",
                    description=f"**{channel.mention}** has been automatically unlocked after {duration_minutes} minute{'s' if duration_minutes != 1 else ''}.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text="Scheduled unlock completed")
                
                await channel.send(embed=embed)
                logging.info(f"Channel {channel.name} automatically unlocked after {duration_minutes} minutes")
                
            except Exception as e:
                logging.error(f"Error during automatic unlock: {e}")

    @lockdown.error
    async def lockdown_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Error handler for lockdown command."""
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 Insufficient Permissions",
                description="You need the **Manage Channels** permission to use this command.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

# Setup function
async def setup(bot):
    """Setup function to add the LockdownCommand cog to the bot."""
    await bot.add_cog(LockdownCommand(bot))
    logging.info("Lockdown command loaded successfully")

def add_lockdown_command(bot):
    """Alternative setup function for manual integration."""
    lockdown_cog = LockdownCommand(bot)
    
    @bot.tree.command(name="lockdown", description="🔒 Temporarily lock a channel with advanced controls")
    @app_commands.describe(
        channel="Channel to lock (defaults to current channel)",
        duration="Duration in minutes (optional - permanent if not specified)",
        reason="Reason for lockdown"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lockdown(
        interaction: discord.Interaction, 
        channel: Optional[discord.TextChannel] = None,
        duration: Optional[int] = None,
        reason: Optional[str] = None
    ):
        await lockdown_cog.lockdown(interaction, channel, duration, reason)
    
    @bot.tree.command(name="unlock", description="🔓 Remove lockdown from a channel")
    @app_commands.describe(
        channel="Channel to unlock (defaults to current channel)",
        reason="Reason for unlocking"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(
        interaction: discord.Interaction, 
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None
    ):
        await lockdown_cog.unlock(interaction, channel, reason)
    
    logging.info("Lockdown commands added successfully")
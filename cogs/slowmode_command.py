import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

class SlowmodeCommand(commands.Cog):
    """Advanced slowmode command with decorative elements and comprehensive functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="slowmode", description="⏰ Set channel slowmode with advanced controls")
    @app_commands.describe(
        seconds="Duration in seconds (0-21600). Use 0 to disable slowmode.",
        channel="Optional: Channel to apply slowmode to (defaults to current channel)",
        reason="Optional: Reason for applying slowmode"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(
        self, 
        interaction: discord.Interaction, 
        seconds: int,
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None
    ):
        """
        Advanced slowmode command with validation and decorative feedback.
        
        Args:
            interaction: Discord interaction object
            seconds: Slowmode duration in seconds (0-21600)
            channel: Optional target channel
            reason: Optional reason for slowmode
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
            
            # Validate seconds range
            if seconds < 0 or seconds > 21600:
                embed = discord.Embed(
                    title="⚠️ Invalid Duration",
                    description="Slowmode duration must be between **0** and **21600** seconds (6 hours).",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Quick Reference",
                    value="• **0s** = Disabled\n• **30s** = Light moderation\n• **300s** = 5 minutes\n• **600s** = 10 minutes\n• **3600s** = 1 hour",
                    inline=False
                )
                embed.set_footer(text="Use a value between 0-21600 seconds")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Apply slowmode
            await target_channel.edit(
                slowmode_delay=seconds,
                reason=f"Slowmode set by {interaction.user} ({interaction.user.id})" + 
                       (f" - Reason: {reason}" if reason else "")
            )
            
            # Create success embed
            if seconds == 0:
                embed = discord.Embed(
                    title="🔓 Slowmode Disabled",
                    description=f"Slowmode has been **disabled** in {target_channel.mention}",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="📝 Details",
                    value=f"**Channel:** {target_channel.mention}\n**Action:** Slowmode removed\n**By:** {interaction.user.mention}",
                    inline=False
                )
            else:
                # Format time display
                if seconds < 60:
                    time_display = f"{seconds} second{'s' if seconds != 1 else ''}"
                elif seconds < 3600:
                    minutes = seconds // 60
                    remaining_seconds = seconds % 60
                    time_display = f"{minutes} minute{'s' if minutes != 1 else ''}"
                    if remaining_seconds > 0:
                        time_display += f" {remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
                else:
                    hours = seconds // 3600
                    remaining_minutes = (seconds % 3600) // 60
                    time_display = f"{hours} hour{'s' if hours != 1 else ''}"
                    if remaining_minutes > 0:
                        time_display += f" {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"
                
                embed = discord.Embed(
                    title="⏰ Slowmode Activated",
                    description=f"Slowmode set to **{time_display}** in {target_channel.mention}",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="📝 Details",
                    value=f"**Channel:** {target_channel.mention}\n**Duration:** {time_display}\n**By:** {interaction.user.mention}",
                    inline=True
                )
                embed.add_field(
                    name="ℹ️ Effect",
                    value=f"Users must wait **{time_display}** between messages",
                    inline=True
                )
            
            if reason:
                embed.add_field(name="📋 Reason", value=reason, inline=False)
            
            embed.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            logging.info(
                f"Slowmode set by {interaction.user} ({interaction.user.id}) "
                f"in {target_channel.name} ({target_channel.id}): {seconds}s"
            )
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="I don't have permission to modify slowmode in that channel.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Required permission: Manage Channels")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="⚠️ Discord Error",
                description=f"Failed to set slowmode: {str(e)}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Discord HTTP error in slowmode command: {e}")
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An unexpected error occurred while setting slowmode.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Unexpected error in slowmode command: {e}", exc_info=True)

    @slowmode.error
    async def slowmode_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Error handler for slowmode command."""
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 Insufficient Permissions",
                description="You need the **Manage Channels** permission to use this command.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="Required Permission",
                value="• Manage Channels",
                inline=False
            )
            embed.set_footer(text="Contact a server administrator for permissions")
            await interaction.response.send_message(embed=embed, ephemeral=True)

# Setup function to add the cog to the bot
async def setup(bot):
    """Setup function to add the SlowmodeCommand cog to the bot."""
    await bot.add_cog(SlowmodeCommand(bot))
    logging.info("Slowmode command loaded successfully")

# Alternative setup for manual integration
def add_slowmode_command(bot):
    """Alternative setup function for manual integration."""
    
    @bot.tree.command(name="slowmode", description="⏰ Set channel slowmode with advanced controls")
    @app_commands.describe(
        seconds="Duration in seconds (0-21600). Use 0 to disable slowmode.",
        channel="Optional: Channel to apply slowmode to (defaults to current channel)",
        reason="Optional: Reason for applying slowmode"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(
        interaction: discord.Interaction, 
        seconds: int,
        channel: Optional[discord.TextChannel] = None,
        reason: Optional[str] = None
    ):
        slowmode_cog = SlowmodeCommand(bot)
        await slowmode_cog.slowmode(interaction, seconds, channel, reason)
    
    logging.info("Slowmode command added successfully")
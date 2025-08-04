import discord
from discord.ext import commands
from discord import app_commands
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Channel IDs from the provided Discord links
        self.UPDATE_CHANNEL_ID = 1338315495782219836
        self.ANNOUNCEMENT_CHANNEL_ID = 1338312258685767723
        self.DEV_RESPONSE_CHANNEL_ID = 1397106345785954437
        
        # Guild ID extracted from the Discord links
        self.GUILD_ID = 1338306024582418503

    async def get_channel_safely(self, channel_id: int) -> discord.TextChannel:
        """Safely get a channel by ID with proper error handling"""
        try:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                channel = await self.bot.fetch_channel(channel_id)
            
            if not isinstance(channel, discord.TextChannel):
                raise ValueError(f"Channel {channel_id} is not a text channel")
                
            return channel
        except discord.NotFound:
            raise ValueError(f"Channel {channel_id} not found")
        except discord.Forbidden:
            raise ValueError(f"No permission to access channel {channel_id}")
        except Exception as e:
            raise ValueError(f"Error accessing channel {channel_id}: {str(e)}")

    @app_commands.command(name="updateannounce", description="Send an update message to the update channel")
    @app_commands.describe(message="The update message to send (supports long paragraphs)")
    async def update_announce(self, interaction: discord.Interaction, message: str):
        """Send an update announcement to the designated update channel"""
        try:
            # Defer the response since channel operations might take time
            await interaction.response.defer(ephemeral=True)
            
            # Validate message length (Discord's limit is 2000 characters per message)
            if len(message) > 2000:
                await interaction.followup.send(
                    "❌ Message is too long! Discord messages must be 2000 characters or less.\n"
                    f"Your message is {len(message)} characters.",
                    ephemeral=True
                )
                return
            
            # Get the update channel
            update_channel = await self.get_channel_safely(self.UPDATE_CHANNEL_ID)
            
            # Check if bot has permission to send messages in the channel
            permissions = update_channel.permissions_for(update_channel.guild.me)
            if not permissions.send_messages:
                await interaction.followup.send(
                    "❌ I don't have permission to send messages in the update channel.",
                    ephemeral=True
                )
                return
            
            # Create an embed for better formatting
            embed = discord.Embed(
                title="📢 Update Announcement",
                description=message,
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Posted by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            
            # Send the message to the update channel
            sent_message = await update_channel.send(embed=embed)
            
            await interaction.followup.send(
                f"✅ Update announcement sent successfully!\n"
                f"Message link: {sent_message.jump_url}",
                ephemeral=True
            )
            
        except ValueError as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in update_announce command: {str(e)}")
            await interaction.followup.send(
                "❌ An unexpected error occurred while sending the update announcement.",
                ephemeral=True
            )

    @app_commands.command(name="announcementmsg", description="Send an announcement message with ping options")
    @app_commands.describe(
        message="The announcement message to send",
        ping="Choose who to ping with this announcement"
    )
    @app_commands.choices(ping=[
        app_commands.Choice(name="@everyone", value="@everyone"),
        app_commands.Choice(name="@here", value="@here"),
        app_commands.Choice(name="No ping", value="none")
    ])
    async def announcement_msg(self, interaction: discord.Interaction, message: str, ping: str):
        """Send an announcement message to the designated announcement channel"""
        try:
            # Defer the response since channel operations might take time
            await interaction.response.defer(ephemeral=True)
            
            # Validate message length
            if len(message) > 1900:  # Leave room for ping and formatting
                await interaction.followup.send(
                    "❌ Message is too long! Please keep announcements under 1900 characters to allow for ping formatting.\n"
                    f"Your message is {len(message)} characters.",
                    ephemeral=True
                )
                return
            
            # Get the announcement channel
            announcement_channel = await self.get_channel_safely(self.ANNOUNCEMENT_CHANNEL_ID)
            
            # Check permissions
            permissions = announcement_channel.permissions_for(announcement_channel.guild.me)
            if not permissions.send_messages:
                await interaction.followup.send(
                    "❌ I don't have permission to send messages in the announcement channel.",
                    ephemeral=True
                )
                return
            
            # Check if bot can mention everyone/here if needed
            if ping in ["@everyone", "@here"] and not permissions.mention_everyone:
                await interaction.followup.send(
                    f"❌ I don't have permission to use {ping} in the announcement channel.",
                    ephemeral=True
                )
                return
            
            # Create the announcement embed
            embed = discord.Embed(
                title="🚨 Important Announcement",
                description=message,
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Announced by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            
            # Prepare the message content with ping
            content = ""
            if ping != "none":
                content = ping
            
            # Send the announcement
            sent_message = await announcement_channel.send(content=content, embed=embed)
            
            ping_text = f" with {ping}" if ping != "none" else ""
            await interaction.followup.send(
                f"✅ Announcement sent successfully{ping_text}!\n"
                f"Message link: {sent_message.jump_url}",
                ephemeral=True
            )
            
        except ValueError as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in announcement_msg command: {str(e)}")
            await interaction.followup.send(
                "❌ An unexpected error occurred while sending the announcement.",
                ephemeral=True
            )

    @app_commands.command(name="devresponsemsg", description="Forward and reply to a message in the dev response channel")
    @app_commands.describe(
        message="Your response message",
        message_id="The ID of the message you want to forward and reply to"
    )
    async def dev_response_msg(self, interaction: discord.Interaction, message: str, message_id: str):
        """Forward a message and reply to it in the dev response channel"""
        try:
            # Defer the response since this operation might take time
            await interaction.response.defer(ephemeral=True)
            
            # Validate message length
            if len(message) > 1800:  # Leave room for forwarded message formatting
                await interaction.followup.send(
                    "❌ Response message is too long! Please keep responses under 1800 characters.\n"
                    f"Your message is {len(message)} characters.",
                    ephemeral=True
                )
                return
            
            # Validate message ID format
            try:
                message_id_int = int(message_id)
            except ValueError:
                await interaction.followup.send(
                    "❌ Invalid message ID format. Please provide a valid Discord message ID (numbers only).",
                    ephemeral=True
                )
                return
            
            # Get the dev response channel
            dev_channel = await self.get_channel_safely(self.DEV_RESPONSE_CHANNEL_ID)
            
            # Check permissions
            permissions = dev_channel.permissions_for(dev_channel.guild.me)
            if not permissions.send_messages:
                await interaction.followup.send(
                    "❌ I don't have permission to send messages in the dev response channel.",
                    ephemeral=True
                )
                return
            
            # Try to find the original message across all channels the bot can access
            original_message = None
            guild = interaction.guild
            
            if guild is None:
                await interaction.followup.send(
                    "❌ This command can only be used in a server.",
                    ephemeral=True
                )
                return
            
            # Search through text channels in the guild
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).read_message_history:
                    try:
                        original_message = await channel.fetch_message(message_id_int)
                        break
                    except (discord.NotFound, discord.Forbidden):
                        continue
                    except Exception:
                        continue
            
            if original_message is None:
                await interaction.followup.send(
                    "❌ Could not find the specified message. Make sure:\n"
                    "• The message ID is correct\n"
                    "• The message exists in a channel I can access\n"
                    "• The message hasn't been deleted",
                    ephemeral=True
                )
                return
            
            # Create embed for the forwarded message
            forward_embed = discord.Embed(
                title="📨 Forwarded Message",
                description=original_message.content or "*[No text content]*",
                color=discord.Color.orange(),
                timestamp=original_message.created_at
            )
            
            # Add original message info
            forward_embed.add_field(
                name="Original Author",
                value=f"{original_message.author.mention} ({original_message.author})",
                inline=True
            )
            # Handle different channel types safely
            channel_display = str(original_message.channel)
            if hasattr(original_message.channel, 'name'):
                channel_display = f"#{original_message.channel.name}"
            elif hasattr(original_message.channel, 'recipient'):
                channel_display = f"DM with {original_message.channel.recipient}"
            
            forward_embed.add_field(
                name="Original Channel",
                value=channel_display,
                inline=True
            )
            forward_embed.add_field(
                name="Message Link",
                value=f"[Jump to Message]({original_message.jump_url})",
                inline=True
            )
            
            if original_message.author.display_avatar:
                forward_embed.set_thumbnail(url=original_message.author.display_avatar.url)
            
            # Create embed for the response
            response_embed = discord.Embed(
                title="💬 Developer Response",
                description=message,
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            response_embed.set_footer(
                text=f"Response by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Send both embeds to the dev response channel
            sent_message = await dev_channel.send(embeds=[forward_embed, response_embed])
            
            await interaction.followup.send(
                f"✅ Message forwarded and response sent successfully!\n"
                f"Dev response link: {sent_message.jump_url}",
                ephemeral=True
            )
            
        except ValueError as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in dev_response_msg command: {str(e)}")
            await interaction.followup.send(
                "❌ An unexpected error occurred while processing the dev response.",
                ephemeral=True
            )

# Function to setup the cog (for integration with existing bot.py)
async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))

# Alternative setup for direct integration into bot.py
def add_utility_commands(bot):
    """
    Add utility commands directly to your bot instance.
    Call this function in your bot.py after creating your bot instance.
    
    Usage in bot.py:
    from discord_commands import add_utility_commands
    add_utility_commands(bot)
    """
    
    # Create a single instance of the cog to share across commands
    cog_instance = UtilityCommands(bot)
    
    @bot.tree.command(name="updateannounce", description="Send an update message to the update channel")
    @app_commands.describe(message="The update message to send (supports long paragraphs)")
    async def update_announce(interaction: discord.Interaction, message: str):
        await cog_instance.update_announce(interaction, message)
    
    @bot.tree.command(name="announcementmsg", description="Send an announcement message with ping options")
    @app_commands.describe(
        message="The announcement message to send",
        ping="Choose who to ping with this announcement"
    )
    @app_commands.choices(ping=[
        app_commands.Choice(name="@everyone", value="@everyone"),
        app_commands.Choice(name="@here", value="@here"),
        app_commands.Choice(name="No ping", value="none")
    ])
    async def announcement_msg(interaction: discord.Interaction, message: str, ping: str):
        await cog_instance.announcement_msg(interaction, message, ping)
    
    @bot.tree.command(name="devresponsemsg", description="Forward and reply to a message in the dev response channel")
    @app_commands.describe(
        message="Your response message",
        message_id="The ID of the message you want to forward and reply to"
    )
    async def dev_response_msg(interaction: discord.Interaction, message: str, message_id: str):
        await cog_instance.dev_response_msg(interaction, message, message_id)

# Example usage in your main bot.py:
"""
import discord
from discord.ext import commands
from discord_commands import add_utility_commands

# Your existing bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Add the utility commands
add_utility_commands(bot)

# Your existing bot events and other code...

bot.run('YOUR_BOT_TOKEN')
"""

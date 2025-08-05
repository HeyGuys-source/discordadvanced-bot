import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

class EchoCommand(commands.Cog):
    """Discord bot utility command for echoing messages with embed/plain text options and reply functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="echo", description="Echo a message with optional embed formatting and reply functionality")
    @app_commands.describe(
        message="The message content to echo",
        format_type="Choose whether to format as embed or plain text",
        reply_to="Optional: Message ID to reply to"
    )
    @app_commands.choices(format_type=[
        app_commands.Choice(name="Plain Text", value="plain"),
        app_commands.Choice(name="Embed", value="embed")
    ])
    async def echo(
        self, 
        interaction: discord.Interaction, 
        message: str,
        format_type: str,
        reply_to: Optional[str] = None
    ):
        """
        Echo command implementation with embed/plain text options and reply functionality.
        
        Args:
            interaction: Discord interaction object
            message: The message content to echo
            format_type: Choice between "embed" and "plain" formatting
            reply_to: Optional message ID to reply to
        """
        try:
            # Validate message content
            if not message or len(message.strip()) == 0:
                await interaction.response.send_message(
                    "❌ Error: Message content cannot be empty.", 
                    ephemeral=True
                )
                return
            
            # Check message length limits
            if len(message) > 2000 and format_type == "plain":
                await interaction.response.send_message(
                    "❌ Error: Plain text messages cannot exceed 2000 characters.", 
                    ephemeral=True
                )
                return
            elif len(message) > 4096 and format_type == "embed":
                await interaction.response.send_message(
                    "❌ Error: Embed descriptions cannot exceed 4096 characters.", 
                    ephemeral=True
                )
                return
            
            # Handle reply functionality
            reference_message = None
            if reply_to:
                try:
                    # Validate message ID format
                    message_id = int(reply_to)
                    
                    # Try to fetch the message to reply to
                    try:
                        # Use the interaction channel directly to fetch the message
                        if interaction.channel and hasattr(interaction.channel, 'fetch_message'):
                            reference_message = await interaction.channel.fetch_message(message_id)
                        else:
                            await interaction.response.send_message(
                                "❌ Error: This channel type doesn't support message replies.", 
                                ephemeral=True
                            )
                            return
                    except discord.NotFound:
                        await interaction.response.send_message(
                            f"❌ Error: Message with ID `{reply_to}` not found in this channel.", 
                            ephemeral=True
                        )
                        return
                    except discord.Forbidden:
                        await interaction.response.send_message(
                            "❌ Error: I don't have permission to access that message.", 
                            ephemeral=True
                        )
                        return
                    except discord.HTTPException as e:
                        await interaction.response.send_message(
                            f"❌ Error: Failed to fetch message: {str(e)}", 
                            ephemeral=True
                        )
                        return
                        
                except ValueError:
                    await interaction.response.send_message(
                        f"❌ Error: Invalid message ID format `{reply_to}`. Message IDs must be numeric.", 
                        ephemeral=True
                    )
                    return
            
            # Prepare the response based on format type
            if format_type == "embed":
                # Create embed
                embed = discord.Embed(
                    description=message,
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(
                    text=f"Echoed by {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url
                )
                
                # Send embed response
                if reference_message:
                    # Use followup for replies since we can't use reference in interaction response
                    await interaction.response.send_message("Processing...", ephemeral=True)
                    await interaction.followup.send(
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                    # Send a reply to the original message
                    await reference_message.reply(embed=embed, mention_author=False)
                else:
                    await interaction.response.send_message(embed=embed)
                    
            else:  # Plain text
                # Send plain text response
                if reference_message:
                    # Use followup for replies since we can't use reference in interaction response
                    await interaction.response.send_message("Processing...", ephemeral=True)
                    await reference_message.reply(message, mention_author=False)
                else:
                    await interaction.response.send_message(message)
            
            # Log successful echo command usage
            logging.info(
                f"Echo command used by {interaction.user} ({interaction.user.id}) "
                f"in {interaction.guild.name if interaction.guild else 'DM'} - "
                f"Format: {format_type}, Reply: {'Yes' if reply_to else 'No'}"
            )
            
        except discord.HTTPException as e:
            # Handle Discord API errors
            await interaction.response.send_message(
                f"❌ Error: Failed to send message due to Discord API error: {str(e)}", 
                ephemeral=True
            )
            logging.error(f"Discord HTTP error in echo command: {e}")
            
        except Exception as e:
            # Handle unexpected errors
            await interaction.response.send_message(
                "❌ Error: An unexpected error occurred while processing the echo command.", 
                ephemeral=True
            )
            logging.error(f"Unexpected error in echo command: {e}", exc_info=True)



# Setup function to add the cog to the bot
async def setup(bot):
    """
    Setup function to add the EchoCommand cog to the bot.
    
    Usage in main bot file:
    await bot.load_extension('echo_command')
    """
    await bot.add_cog(EchoCommand(bot))
    logging.info("Echo command loaded successfully")

# Alternative setup for manual integration
def add_echo_command(bot):
    """
    Alternative setup function for manual integration.
    
    Usage in main bot file:
    from echo_command import add_echo_command
    add_echo_command(bot)
    """
    @bot.tree.command(name="echo", description="Echo a message with optional embed formatting and reply functionality")
    @app_commands.describe(
        message="The message content to echo",
        format_type="Choose whether to format as embed or plain text",
        reply_to="Optional: Message ID to reply to"
    )
    @app_commands.choices(format_type=[
        app_commands.Choice(name="Plain Text", value="plain"),
        app_commands.Choice(name="Embed", value="embed")
    ])
    async def echo(
        interaction: discord.Interaction, 
        message: str,
        format_type: str,
        reply_to: Optional[str] = None
    ):
        # Execute the echo functionality directly
        try:
            # Validate message content
            if not message or len(message.strip()) == 0:
                await interaction.response.send_message(
                    "❌ Error: Message content cannot be empty.", 
                    ephemeral=True
                )
                return
            
            # Check message length limits
            if len(message) > 2000 and format_type == "plain":
                await interaction.response.send_message(
                    "❌ Error: Plain text messages cannot exceed 2000 characters.", 
                    ephemeral=True
                )
                return
            elif len(message) > 4096 and format_type == "embed":
                await interaction.response.send_message(
                    "❌ Error: Embed descriptions cannot exceed 4096 characters.", 
                    ephemeral=True
                )
                return
            
            # Handle reply functionality
            reference_message = None
            if reply_to:
                try:
                    message_id = int(reply_to)
                    if interaction.channel and hasattr(interaction.channel, 'fetch_message'):
                        reference_message = await interaction.channel.fetch_message(message_id)
                    else:
                        await interaction.response.send_message(
                            "❌ Error: This channel type doesn't support message replies.", 
                            ephemeral=True
                        )
                        return
                except (ValueError, discord.NotFound, discord.Forbidden, discord.HTTPException, AttributeError):
                    await interaction.response.send_message(
                        f"❌ Error: Could not find or access message with ID `{reply_to}`.", 
                        ephemeral=True
                    )
                    return
            
            # Send response
            if format_type == "embed":
                embed = discord.Embed(
                    description=message,
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(
                    text=f"Echoed by {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url
                )
                
                if reference_message:
                    await interaction.response.send_message("Processing...", ephemeral=True)
                    await reference_message.reply(embed=embed, mention_author=False)
                else:
                    await interaction.response.send_message(embed=embed)
            else:
                if reference_message:
                    await interaction.response.send_message("Processing...", ephemeral=True)
                    await reference_message.reply(message, mention_author=False)
                else:
                    await interaction.response.send_message(message)
                    
        except Exception as e:
            await interaction.response.send_message(
                "❌ Error: An unexpected error occurred while processing the echo command.", 
                ephemeral=True
            )
            logging.error(f"Unexpected error in echo command: {e}", exc_info=True)
    
    logging.info("Echo command added successfully")

# Example usage documentation
"""
INTEGRATION EXAMPLES:

Method 1 - Using Cog Extension (Recommended):
1. Place this file in your bot's extensions/cogs directory
2. In your main bot file, add:
   await bot.load_extension('echo_command')

Method 2 - Manual Integration:
1. Import the function in your main bot file:
   from echo_command import add_echo_command
2. Call the function after bot initialization:
   add_echo_command(bot)

Method 3 - Direct Cog Addition:
1. Import the class in your main bot file:
   from echo_command import EchoCommand
2. Add the cog:
   await bot.add_cog(EchoCommand(bot))

COMMAND USAGE:
/echo message:"Hello World!" format_type:"Plain Text"
/echo message:"This is an embed" format_type:"Embed"
/echo message:"Reply to this message" format_type:"Plain Text" reply_to:"1234567890123456789"

PERMISSIONS REQUIRED:
- Send Messages
- Use Slash Commands
- Read Message History (for reply functionality)
- Embed Links (for embed formatting)
"""

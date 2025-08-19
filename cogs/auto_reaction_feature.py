import discord
from discord.ext import commands
import logging
import asyncio

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoReactionFeature(commands.Cog):
    """
    Discord bot cog that automatically reacts to messages in a specific channel
    with custom emojis.
    """
    
    def __init__(self, bot):
        self.bot = bot
        # Target channel ID where reactions should be added
        self.target_channel_id = 1397275881008791723
        self.target_channel_id = 1397276528873701448
        self.target_channel_id = 1397276442848395576
        
        
        
        # Custom emoji IDs - these will be converted to proper emoji objects
        self.thumbs_up_emoji_id = 1402566034510188636
        self.thumbs_down_emoji_id = 1402566082266529842
        
        # Store emoji objects once fetched
        self.thumbs_up_emoji = None
        self.thumbs_down_emoji = None
        
        logger.info("AutoReactionFeature cog initialized")

    async def setup_emojis(self):
        """
        Fetch and cache the custom emoji objects from their IDs.
        This is called when the bot is ready to ensure emojis are available.
        """
        try:
            # Get emoji objects from the bot's available emojis
            self.thumbs_up_emoji = self.bot.get_emoji(self.thumbs_up_emoji_id)
            self.thumbs_down_emoji = self.bot.get_emoji(self.thumbs_down_emoji_id)
            
            if not self.thumbs_up_emoji:
                logger.warning(f"Could not find thumbs_up emoji with ID {self.thumbs_up_emoji_id}")
            if not self.thumbs_down_emoji:
                logger.warning(f"Could not find thumbs_down emoji with ID {self.thumbs_down_emoji_id}")
                
            if self.thumbs_up_emoji and self.thumbs_down_emoji:
                logger.info("Custom emojis successfully loaded")
            else:
                logger.error("Failed to load one or more custom emojis")
                
        except Exception as e:
            logger.error(f"Error setting up emojis: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Called when the bot is ready. Sets up the custom emojis.
        """
        logger.info("AutoReactionFeature is ready")
        await self.setup_emojis()

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Event listener that triggers when any message is sent.
        Filters for the target channel and adds reactions.
        """
        try:
            # Skip if message is from the bot itself to prevent loops
            if message.author == self.bot.user:
                return
            
            # Check if message is in the target channel
            if message.channel.id != self.target_channel_id:
                return
            
            # Ensure emojis are available
            if not self.thumbs_up_emoji or not self.thumbs_down_emoji:
                logger.warning("Emojis not available, attempting to reload...")
                await self.setup_emojis()
                
                # If still not available, skip this reaction
                if not self.thumbs_up_emoji or not self.thumbs_down_emoji:
                    logger.error("Cannot react: custom emojis not available")
                    return
            
            # Add reactions to the message
            await self.add_reactions_safely(message)
            
            logger.info(f"Added reactions to message from {message.author} in channel {message.channel.name}")
            
        except Exception as e:
            logger.error(f"Error in on_message event: {e}")
            # Don't re-raise to prevent bot crashes

    async def add_reactions_safely(self, message):
        """
        Safely add both emoji reactions to a message with individual error handling.
        """
        # Add thumbs up reaction
        try:
            await message.add_reaction(self.thumbs_up_emoji)
        except discord.Forbidden:
            logger.error("Bot lacks permission to add thumbs_up reaction")
        except discord.NotFound:
            logger.error("Message not found when adding thumbs_up reaction")
        except discord.HTTPException as e:
            logger.error(f"Failed to add thumbs_up reaction: {e}")
        except Exception as e:
            logger.error(f"Unexpected error adding thumbs_up reaction: {e}")
        
        # Add thumbs down reaction
        try:
            await message.add_reaction(self.thumbs_down_emoji)
        except discord.Forbidden:
            logger.error("Bot lacks permission to add thumbs_down reaction")
        except discord.NotFound:
            logger.error("Message not found when adding thumbs_down reaction")
        except discord.HTTPException as e:
            logger.error(f"Failed to add thumbs_down reaction: {e}")
        except Exception as e:
            logger.error(f"Unexpected error adding thumbs_down reaction: {e}")

    @commands.command(name='test_reactions')
    @commands.has_permissions(administrator=True)
    async def test_reactions(self, ctx):
        """
        Admin command to test if the reaction feature is working.
        """
        try:
            if ctx.channel.id == self.target_channel_id:
                await ctx.send("Testing reactions in target channel...")
                # The on_message event will handle adding reactions to this message
            else:
                await ctx.send(f"This command should be used in the target channel: <#{self.target_channel_id}>")
        except Exception as e:
            logger.error(f"Error in test_reactions command: {e}")
            await ctx.send("An error occurred while testing reactions.")

    @commands.command(name='reaction_status')
    @commands.has_permissions(administrator=True)
    async def reaction_status(self, ctx):
        """
        Admin command to check the status of the reaction feature.
        """
        try:
            status_msg = "**Auto Reaction Feature Status:**\n"
            status_msg += f"Target Channel ID: {self.target_channel_id}\n"
            status_msg += f"Thumbs Up Emoji: {'✅ Loaded' if self.thumbs_up_emoji else '❌ Not Found'}\n"
            status_msg += f"Thumbs Down Emoji: {'✅ Loaded' if self.thumbs_down_emoji else '❌ Not Found'}\n"
            
            if self.thumbs_up_emoji:
                status_msg += f"Thumbs Up: {self.thumbs_up_emoji}\n"
            if self.thumbs_down_emoji:
                status_msg += f"Thumbs Down: {self.thumbs_down_emoji}\n"
            
            await ctx.send(status_msg)
            
        except Exception as e:
            logger.error(f"Error in reaction_status command: {e}")
            await ctx.send("An error occurred while checking reaction status.")

async def setup(bot):
    """
    Setup function to add the cog to the bot.
    This function should be called when loading the extension.
    """
    try:
        await bot.add_cog(AutoReactionFeature(bot))
        logger.info("AutoReactionFeature cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load AutoReactionFeature cog: {e}")
        raise

# Alternative function for manual loading without setup()
def create_auto_reaction_feature(bot):
    """
    Alternative method to create and return the cog instance
    for manual addition to the bot.
    
    Usage in bot.py:
    from auto_reaction_feature import create_auto_reaction_feature
    bot.add_cog(create_auto_reaction_feature(bot))
    """
    return AutoReactionFeature(bot)

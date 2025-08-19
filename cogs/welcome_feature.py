import discord
from discord.ext import commands
import logging

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WelcomeFeature(commands.Cog):
    """
    Discord bot cog that automatically welcomes new members when they join the server.
    """
    
    def __init__(self, bot):
        self.bot = bot
        # Target channel ID where welcome messages should be sent
        self.welcome_channel_id = 1338306025106837536
        
        # Custom emoji ID for the welcome emoji
        self.welcome_emoji_id = 1376016386999980183
        
        # Welcome image URL
        self.welcome_image_url = "https://cdn.discordapp.com/attachments/1338312258685767723/1407352654144864327/79E1C305-C54E-4866-BA4D-E4020D02A623.png?ex=68a5cacc&is=68a4794c&hm=31872747f7a75609c4c080ba2a4ebbb9959fe87694445b94309a7f2a96c69008&"
        
        # Store emoji and channel objects once fetched
        self.welcome_emoji = None
        self.welcome_channel = None
        
        logger.info("WelcomeFeature cog initialized")

    async def setup_resources(self):
        """
        Fetch and cache the custom emoji and channel objects.
        This is called when the bot is ready.
        """
        try:
            # Get emoji object from the bot's available emojis
            self.welcome_emoji = self.bot.get_emoji(self.welcome_emoji_id)
            
            if not self.welcome_emoji:
                logger.warning(f"Could not find welcome emoji with ID {self.welcome_emoji_id}")
                # Fallback to a default emoji if custom emoji not found
                self.welcome_emoji = "👋"
            else:
                logger.info("Welcome emoji successfully loaded")
            
            # Get channel object
            self.welcome_channel = self.bot.get_channel(self.welcome_channel_id)
            
            if not self.welcome_channel:
                logger.error(f"Could not find welcome channel with ID {self.welcome_channel_id}")
            else:
                logger.info(f"Welcome channel found: {self.welcome_channel.name}")
                
        except Exception as e:
            logger.error(f"Error setting up resources: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Called when the bot is ready. Sets up resources.
        """
        logger.info("WelcomeFeature is ready")
        await self.setup_resources()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Event listener that triggers when a new member joins the server.
        Sends a welcome message to the designated channel.
        """
        try:
            # Ensure we have the welcome channel
            if not self.welcome_channel:
                logger.warning("Welcome channel not available, attempting to reload...")
                await self.setup_resources()
                
                if not self.welcome_channel:
                    logger.error("Cannot send welcome message: channel not available")
                    return
            
            # Get current member count
            guild = member.guild
            current_member_count = guild.member_count
            old_member_count = current_member_count - 1
            
            # Create the welcome message
            welcome_message = await self.create_welcome_message(member, old_member_count, current_member_count)
            
            # Send the welcome message
            await self.welcome_channel.send(welcome_message)
            
            logger.info(f"Welcome message sent for {member.display_name} ({member.id})")
            
        except discord.Forbidden:
            logger.error("Bot lacks permission to send messages in welcome channel")
        except discord.HTTPException as e:
            logger.error(f"Failed to send welcome message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in on_member_join event: {e}")

    async def create_welcome_message(self, member, old_count, new_count):
        """
        Creates the welcome message with proper formatting and user mention.
        """
        try:
            # Create the welcome message with the exact format requested
            welcome_text = (
                f"### {self.welcome_emoji} Hello {member.mention}! Welcome to Kaiju Blocky, "
                f"you have gained us a new member, from {old_count} to {new_count}! "
                f"We're glad for you to join! {self.welcome_image_url}"
            )
            
            return welcome_text
            
        except Exception as e:
            logger.error(f"Error creating welcome message: {e}")
            # Return a simple welcome message as fallback
            return f"👋 Hello {member.mention}! Welcome to Kaiju Blocky!"

    @commands.command(name='test_welcome')
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        """
        Admin command to test the welcome message with the command author.
        """
        try:
            if not self.welcome_channel:
                await ctx.send("❌ Welcome channel not available. Please check the configuration.")
                return
            
            # Get current member count for testing
            guild = ctx.guild
            current_member_count = guild.member_count
            old_member_count = current_member_count - 1
            
            # Create and send a test welcome message
            welcome_message = await self.create_welcome_message(ctx.author, old_member_count, current_member_count)
            await self.welcome_channel.send(f"**[TEST MESSAGE]**\n{welcome_message}")
            
            await ctx.send(f"✅ Test welcome message sent to {self.welcome_channel.mention}")
            logger.info(f"Test welcome message triggered by {ctx.author}")
            
        except discord.Forbidden:
            await ctx.send("❌ Bot lacks permission to send messages in the welcome channel.")
        except Exception as e:
            logger.error(f"Error in test_welcome command: {e}")
            await ctx.send("❌ An error occurred while sending the test welcome message.")

    @commands.command(name='welcome_status')
    @commands.has_permissions(administrator=True)
    async def welcome_status(self, ctx):
        """
        Admin command to check the status of the welcome feature.
        """
        try:
            status_msg = "**Welcome Feature Status:**\n"
            status_msg += f"Target Channel ID: {self.welcome_channel_id}\n"
            status_msg += f"Channel Found: {'✅ Yes' if self.welcome_channel else '❌ No'}\n"
            status_msg += f"Welcome Emoji: {'✅ Loaded' if self.welcome_emoji else '❌ Not Found'}\n"
            
            if self.welcome_channel:
                status_msg += f"Target Channel: {self.welcome_channel.mention}\n"
            if self.welcome_emoji and hasattr(self.welcome_emoji, 'id'):
                status_msg += f"Welcome Emoji: {self.welcome_emoji}\n"
            
            status_msg += f"Image URL: {self.welcome_image_url[:50]}...\n"
            
            await ctx.send(status_msg)
            
        except Exception as e:
            logger.error(f"Error in welcome_status command: {e}")
            await ctx.send("❌ An error occurred while checking welcome feature status.")

    @commands.command(name='set_welcome_channel')
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel):
        """
        Admin command to change the welcome channel.
        """
        try:
            # Update the welcome channel
            self.welcome_channel_id = channel.id
            self.welcome_channel = channel
            
            await ctx.send(f"✅ Welcome channel updated to {channel.mention}")
            logger.info(f"Welcome channel updated to {channel.name} ({channel.id}) by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in set_welcome_channel command: {e}")
            await ctx.send("❌ An error occurred while updating the welcome channel.")

async def setup(bot):
    """
    Setup function to add the cog to the bot.
    This function should be called when loading the extension.
    """
    try:
        await bot.add_cog(WelcomeFeature(bot))
        logger.info("WelcomeFeature cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load WelcomeFeature cog: {e}")
        raise

# Alternative function for manual loading without setup()
def create_welcome_feature(bot):
    """
    Alternative method to create and return the cog instance
    for manual addition to the bot.
    
    Usage in bot.py:
    from welcome_feature import create_welcome_feature
    bot.add_cog(create_welcome_feature(bot))
    """
    return WelcomeFeature(bot)
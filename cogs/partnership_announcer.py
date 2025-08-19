import discord
from discord.ext import commands, tasks
import logging
import asyncio

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PartnershipAnnouncer(commands.Cog):
    """
    Discord bot cog that automatically sends partnership announcements 
    every 10 minutes in a specific channel.
    """
    
    def __init__(self, bot):
        self.bot = bot
        # Target channel ID where announcements should be sent
        self.announcement_channel_id = 1338308335568556156
        
        # Custom emoji ID for partnership emoji
        self.partnership_emoji_id = 1406300705458749550
        
        # Store emoji object once fetched
        self.partnership_emoji = None
        
        # Store channel object once fetched
        self.announcement_channel = None
        
        logger.info("PartnershipAnnouncer cog initialized")

    async def setup_resources(self):
        """
        Fetch and cache the custom emoji and channel objects.
        This is called when the bot is ready.
        """
        try:
            # Get emoji object from the bot's available emojis
            self.partnership_emoji = self.bot.get_emoji(self.partnership_emoji_id)
            
            if not self.partnership_emoji:
                logger.warning(f"Could not find partnership emoji with ID {self.partnership_emoji_id}")
                # Fallback to a default emoji if custom emoji not found
                self.partnership_emoji = "🤝"
            else:
                logger.info("Partnership emoji successfully loaded")
            
            # Get channel object
            self.announcement_channel = self.bot.get_channel(self.announcement_channel_id)
            
            if not self.announcement_channel:
                logger.error(f"Could not find announcement channel with ID {self.announcement_channel_id}")
            else:
                logger.info(f"Announcement channel found: {self.announcement_channel.name}")
                
        except Exception as e:
            logger.error(f"Error setting up resources: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Called when the bot is ready. Sets up resources and starts the announcement loop.
        """
        logger.info("PartnershipAnnouncer is ready")
        await self.setup_resources()
        
        # Start the announcement loop if not already running
        if not self.partnership_announcement_loop.is_running():
            self.partnership_announcement_loop.start()
            logger.info("Partnership announcement loop started")

    async def cog_unload(self):
        """
        Called when the cog is unloaded. Stops the announcement loop.
        """
        self.partnership_announcement_loop.cancel()
        logger.info("Partnership announcement loop stopped")

    @tasks.loop(minutes=50)
    async def partnership_announcement_loop(self):
        """
        Task loop that runs every 20 minutes to send partnership announcements.
        """
        try:
            # Ensure we have the channel
            if not self.announcement_channel:
                logger.warning("Announcement channel not available, attempting to reload...")
                await self.setup_resources()
                
                if not self.announcement_channel:
                    logger.error("Cannot send announcement: channel not available")
                    return
            
            # Create the partnership announcement embed
            embed = await self.create_partnership_embed()
            
            # Send the announcement
            await self.announcement_channel.send(embed=embed)
            
            logger.info(f"Partnership announcement sent to {self.announcement_channel.name}")
            
        except discord.Forbidden:
            logger.error("Bot lacks permission to send messages in announcement channel")
        except discord.HTTPException as e:
            logger.error(f"Failed to send partnership announcement: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in partnership announcement loop: {e}")

    async def create_partnership_embed(self):
        """
        Creates the partnership announcement embed with proper formatting.
        """
        try:
            # Create embed with discord-blurple color
            embed = discord.Embed(
                description=f"{self.partnership_emoji} - If you're not sure who to DM to do partnership with us! Please DM Maxshieldman, Magster, Mr. Rolex or the Community Manager! {self.partnership_emoji}",
                color=discord.Color.blurple()
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Error creating partnership embed: {e}")
            # Return a simple embed as fallback
            return discord.Embed(
                description="🤝 - If you're not sure who to DM to do partnership with us! Please DM Maxshieldman, Magster, Mr. Rolex or the Community Manager! 🤝",
                color=discord.Color.blurple()
            )

    @partnership_announcement_loop.before_loop
    async def before_partnership_announcement_loop(self):
        """
        Waits for the bot to be ready before starting the announcement loop.
        """
        await self.bot.wait_until_ready()

    @commands.command(name='send_partnership_now')
    @commands.has_permissions(administrator=True)
    async def send_partnership_now(self, ctx):
        """
        Admin command to manually trigger a partnership announcement.
        """
        try:
            if not self.announcement_channel:
                await ctx.send("❌ Announcement channel not available. Please check the configuration.")
                return
            
            # Create and send the embed
            embed = await self.create_partnership_embed()
            await self.announcement_channel.send(embed=embed)
            
            await ctx.send(f"✅ Partnership announcement sent to {self.announcement_channel.mention}")
            logger.info(f"Manual partnership announcement triggered by {ctx.author}")
            
        except discord.Forbidden:
            await ctx.send("❌ Bot lacks permission to send messages in the announcement channel.")
        except Exception as e:
            logger.error(f"Error in send_partnership_now command: {e}")
            await ctx.send("❌ An error occurred while sending the partnership announcement.")

    @commands.command(name='partnership_status')
    @commands.has_permissions(administrator=True)
    async def partnership_status(self, ctx):
        """
        Admin command to check the status of the partnership announcer.
        """
        try:
            status_msg = "**Partnership Announcer Status:**\n"
            status_msg += f"Target Channel ID: {self.announcement_channel_id}\n"
            status_msg += f"Channel Found: {'✅ Yes' if self.announcement_channel else '❌ No'}\n"
            status_msg += f"Partnership Emoji: {'✅ Loaded' if self.partnership_emoji else '❌ Not Found'}\n"
            status_msg += f"Announcement Loop: {'✅ Running' if self.partnership_announcement_loop.is_running() else '❌ Stopped'}\n"
            status_msg += f"Interval: Every 10 minutes\n"
            
            if self.announcement_channel:
                status_msg += f"Target Channel: {self.announcement_channel.mention}\n"
            if self.partnership_emoji and hasattr(self.partnership_emoji, 'id'):
                status_msg += f"Partnership Emoji: {self.partnership_emoji}\n"
            
            await ctx.send(status_msg)
            
        except Exception as e:
            logger.error(f"Error in partnership_status command: {e}")
            await ctx.send("❌ An error occurred while checking partnership announcer status.")

    @commands.command(name='stop_partnership_announcements')
    @commands.has_permissions(administrator=True)
    async def stop_partnership_announcements(self, ctx):
        """
        Admin command to stop the partnership announcement loop.
        """
        try:
            if self.partnership_announcement_loop.is_running():
                self.partnership_announcement_loop.cancel()
                await ctx.send("✅ Partnership announcements have been stopped.")
                logger.info(f"Partnership announcements stopped by {ctx.author}")
            else:
                await ctx.send("ℹ️ Partnership announcements are not currently running.")
                
        except Exception as e:
            logger.error(f"Error in stop_partnership_announcements command: {e}")
            await ctx.send("❌ An error occurred while stopping partnership announcements.")

    @commands.command(name='start_partnership_announcements')
    @commands.has_permissions(administrator=True)
    async def start_partnership_announcements(self, ctx):
        """
        Admin command to start the partnership announcement loop.
        """
        try:
            if not self.partnership_announcement_loop.is_running():
                self.partnership_announcement_loop.start()
                await ctx.send("✅ Partnership announcements have been started.")
                logger.info(f"Partnership announcements started by {ctx.author}")
            else:
                await ctx.send("ℹ️ Partnership announcements are already running.")
                
        except Exception as e:
            logger.error(f"Error in start_partnership_announcements command: {e}")
            await ctx.send("❌ An error occurred while starting partnership announcements.")

async def setup(bot):
    """
    Setup function to add the cog to the bot.
    This function should be called when loading the extension.
    """
    try:
        await bot.add_cog(PartnershipAnnouncer(bot))
        logger.info("PartnershipAnnouncer cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load PartnershipAnnouncer cog: {e}")
        raise

# Alternative function for manual loading without setup()
def create_partnership_announcer(bot):
    """
    Alternative method to create and return the cog instance
    for manual addition to the bot.
    
    Usage in bot.py:
    from partnership_announcer import create_partnership_announcer
    bot.add_cog(create_partnership_announcer(bot))
    """
    return PartnershipAnnouncer(bot)

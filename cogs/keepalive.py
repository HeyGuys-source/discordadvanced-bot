import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, timezone

class KeepAlive(commands.Cog):
    """
    A Discord bot cog that implements automated keep-alive functionality
    to prevent inactivity by periodically pinging Discord's API.
    """
    
    def __init__(self, bot: commands.Bot, ping_interval: int = 60):
        """
        Initialize the KeepAlive cog.
        
        Args:
            bot: The Discord bot instance
            ping_interval: Interval in seconds between keep-alive pings (default: 60)
        """
        self.bot = bot
        self.ping_interval = ping_interval
        self.logger = logging.getLogger(__name__)
        self.last_ping = None
        self.ping_count = 0
        self.failed_pings = 0
        
        # Configure logging for this cog
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Start the keep-alive task when the bot is ready."""
        if not self.keep_alive_task.is_running():
            self.keep_alive_task.start()
            self.logger.info(f"KeepAlive cog started with {self.ping_interval}s interval")
    
    async def cog_unload(self):
        """Clean up when the cog is unloaded."""
        if self.keep_alive_task.is_running():
            self.keep_alive_task.cancel()
            self.logger.info("KeepAlive task stopped")
    
    @tasks.loop(seconds=60)  # Default interval, will be changed in setup
    async def keep_alive_task(self):
        """
        Background task that performs keep-alive pings to Discord's API.
        This prevents the bot from being considered inactive.
        """
        try:
            # Perform a lightweight API call to maintain connection
            # We'll fetch the bot's own user info, which is a minimal API call
            await self.bot.fetch_user(self.bot.user.id)
            
            self.last_ping = datetime.now(timezone.utc)
            self.ping_count += 1
            
            # Log every 10th ping to avoid spam
            if self.ping_count % 10 == 0:
                self.logger.info(
                    f"Keep-alive ping #{self.ping_count} successful. "
                    f"Failed pings: {self.failed_pings}"
                )
            
        except discord.HTTPException as e:
            self.failed_pings += 1
            self.logger.warning(f"Keep-alive ping failed (HTTP): {e}")
            
        except discord.ConnectionClosed:
            self.failed_pings += 1
            self.logger.warning("Keep-alive ping failed: Connection closed")
            
        except Exception as e:
            self.failed_pings += 1
            self.logger.error(f"Unexpected error during keep-alive ping: {e}")
    
    @keep_alive_task.before_loop
    async def before_keep_alive_task(self):
        """Wait for the bot to be ready before starting the task."""
        await self.bot.wait_until_ready()
        # Update the task interval to the configured value
        self.keep_alive_task.change_interval(seconds=self.ping_interval)
    
    @keep_alive_task.error
    async def keep_alive_task_error(self, error):
        """Handle errors in the keep-alive task."""
        self.logger.error(f"Keep-alive task encountered an error: {error}")
        
        # If the task fails, try to restart it after a delay
        await asyncio.sleep(30)
        if not self.keep_alive_task.is_running():
            try:
                self.keep_alive_task.restart()
                self.logger.info("Keep-alive task restarted after error")
            except Exception as restart_error:
                self.logger.error(f"Failed to restart keep-alive task: {restart_error}")
    
    @commands.command(name="keepalive_status", aliases=["ka_status"])
    @commands.has_permissions(administrator=True)
    async def keepalive_status(self, ctx):
        """
        Display the current status of the keep-alive system.
        Requires administrator permissions.
        """
        embed = discord.Embed(
            title="🔄 Keep-Alive Status",
            color=discord.Color.green() if self.keep_alive_task.is_running() else discord.Color.red()
        )
        
        # Task status
        status = "✅ Running" if self.keep_alive_task.is_running() else "❌ Stopped"
        embed.add_field(name="Task Status", value=status, inline=True)
        
        # Ping interval
        embed.add_field(name="Ping Interval", value=f"{self.ping_interval} seconds", inline=True)
        
        # Statistics
        embed.add_field(name="Total Pings", value=str(self.ping_count), inline=True)
        embed.add_field(name="Failed Pings", value=str(self.failed_pings), inline=True)
        
        # Last ping time
        if self.last_ping:
            last_ping_str = self.last_ping.strftime("%Y-%m-%d %H:%M:%S UTC")
            embed.add_field(name="Last Ping", value=last_ping_str, inline=True)
        else:
            embed.add_field(name="Last Ping", value="Never", inline=True)
        
        # Success rate
        if self.ping_count > 0:
            success_rate = ((self.ping_count - self.failed_pings) / self.ping_count) * 100
            embed.add_field(name="Success Rate", value=f"{success_rate:.1f}%", inline=True)
        
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)
    
    @commands.command(name="keepalive_toggle", aliases=["ka_toggle"])
    @commands.has_permissions(administrator=True)
    async def keepalive_toggle(self, ctx):
        """
        Toggle the keep-alive task on/off.
        Requires administrator permissions.
        """
        if self.keep_alive_task.is_running():
            self.keep_alive_task.cancel()
            embed = discord.Embed(
                title="🔄 Keep-Alive Disabled",
                description="The keep-alive task has been stopped.",
                color=discord.Color.orange()
            )
        else:
            self.keep_alive_task.start()
            embed = discord.Embed(
                title="🔄 Keep-Alive Enabled",
                description=f"The keep-alive task has been started with a {self.ping_interval}s interval.",
                color=discord.Color.green()
            )
        
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)
    
    @commands.command(name="keepalive_interval", aliases=["ka_interval"])
    @commands.has_permissions(administrator=True)
    async def keepalive_interval(self, ctx, new_interval: int = None):
        """
        View or change the keep-alive ping interval.
        Requires administrator permissions.
        
        Args:
            new_interval: New interval in seconds (30-3600). If not provided, shows current interval.
        """
        if new_interval is None:
            embed = discord.Embed(
                title="🔄 Keep-Alive Interval",
                description=f"Current interval: **{self.ping_interval} seconds**",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Validate interval range
        if not 30 <= new_interval <= 3600:
            embed = discord.Embed(
                title="❌ Invalid Interval",
                description="Interval must be between 30 and 3600 seconds (30 seconds to 1 hour).",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Update interval
        old_interval = self.ping_interval
        self.ping_interval = new_interval
        
        # Restart task with new interval if it's running
        if self.keep_alive_task.is_running():
            self.keep_alive_task.cancel()
            await asyncio.sleep(1)
            self.keep_alive_task.change_interval(seconds=new_interval)
            self.keep_alive_task.start()
        
        embed = discord.Embed(
            title="🔄 Interval Updated",
            description=f"Keep-alive interval changed from **{old_interval}s** to **{new_interval}s**",
            color=discord.Color.green()
        )
        
        if self.keep_alive_task.is_running():
            embed.add_field(
                name="Status", 
                value="Task restarted with new interval", 
                inline=False
            )
        
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot, ping_interval: int = 60):
    """
    Setup function to load the KeepAlive cog.
    
    Args:
        bot: The Discord bot instance
        ping_interval: Interval in seconds between keep-alive pings (default: 60)
    """
    await bot.add_cog(KeepAlive(bot, ping_interval))


# Alternative setup function for different loading styles
def setup_keepalive(bot: commands.Bot, ping_interval: int = 60):
    """
    Synchronous setup function for older discord.py versions or different loading patterns.
    
    Args:
        bot: The Discord bot instance
        ping_interval: Interval in seconds between keep-alive pings (default: 60)
    """
    return bot.add_cog(KeepAlive(bot, ping_interval))

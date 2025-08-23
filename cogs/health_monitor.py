import discord
from discord.ext import commands, tasks
import asyncio
import logging
import traceback
import time
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psutil
import os

logger = logging.getLogger(__name__)

class HealthMonitor(commands.Cog):
    """Advanced health monitoring and error recovery system for Discord bots."""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.error_count = 0
        self.last_errors = []
        self.health_status = "healthy"
        self.last_health_check = datetime.utcnow()
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
        # Health metrics
        self.metrics = {
            'uptime': 0,
            'commands_executed': 0,
            'errors_handled': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'guild_count': 0,
            'user_count': 0,
            'latency': 0
        }
        
        # Error tracking
        self.error_threshold = 10  # Max errors in 10 minutes
        self.error_window = 600   # 10 minutes in seconds
        
        # Start monitoring tasks
        self.health_check_task.start()
        self.metrics_update_task.start()
        self.error_cleanup_task.start()
    
    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.health_check_task.cancel()
        self.metrics_update_task.cancel()
        self.error_cleanup_task.cancel()
    
    @tasks.loop(minutes=1)
    async def health_check_task(self):
        """Perform health checks every minute."""
        try:
            await self._perform_health_check()
            await self._check_error_threshold()
            await self._update_recovery_status()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            await self._handle_critical_error(e)
    
    @tasks.loop(minutes=5)
    async def metrics_update_task(self):
        """Update bot metrics every 5 minutes."""
        try:
            await self._update_metrics()
            await self._log_health_status()
            
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
    
    @tasks.loop(hours=1)
    async def error_cleanup_task(self):
        """Clean up old error records every hour."""
        current_time = time.time()
        self.last_errors = [
            error for error in self.last_errors
            if current_time - error['timestamp'] < self.error_window
        ]
    
    async def _perform_health_check(self):
        """Perform comprehensive health check."""
        try:
            # Check Discord connection
            if not self.bot.is_ready():
                self.health_status = "degraded"
                logger.warning("Bot is not ready")
                return
            
            # Check latency
            latency = self.bot.latency * 1000  # Convert to ms
            if latency > 1000:  # High latency
                self.health_status = "degraded"
                logger.warning(f"High latency detected: {latency:.2f}ms")
            
            # Check memory usage
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                self.health_status = "critical"
                logger.error(f"Critical memory usage: {memory_percent}%")
                await self._attempt_memory_cleanup()
            
            # Check recent errors
            recent_errors = len([
                e for e in self.last_errors
                if time.time() - e['timestamp'] < 300  # 5 minutes
            ])
            
            if recent_errors > 5:
                self.health_status = "degraded"
                logger.warning(f"High error rate: {recent_errors} errors in 5 minutes")
            
            # Update last check time
            self.last_health_check = datetime.utcnow()
            
            # If no issues found, mark as healthy
            if self.health_status != "critical" and recent_errors <= 2 and latency < 500:
                self.health_status = "healthy"
                self.recovery_attempts = 0
                
        except Exception as e:
            self.health_status = "critical"
            logger.error(f"Health check error: {e}")
            await self._handle_critical_error(e)
    
    async def _update_metrics(self):
        """Update bot performance metrics."""
        try:
            # Basic metrics
            self.metrics['uptime'] = int(time.time() - self.start_time)
            self.metrics['latency'] = round(self.bot.latency * 1000, 2)
            self.metrics['guild_count'] = len(self.bot.guilds)
            self.metrics['user_count'] = len(self.bot.users)
            self.metrics['errors_handled'] = self.error_count
            
            # System metrics
            self.metrics['memory_usage'] = round(psutil.virtual_memory().percent, 2)
            self.metrics['cpu_usage'] = round(psutil.cpu_percent(), 2)
            
        except Exception as e:
            logger.error(f"Metrics update error: {e}")
    
    async def _check_error_threshold(self):
        """Check if error threshold has been exceeded."""
        current_time = time.time()
        recent_errors = [
            e for e in self.last_errors
            if current_time - e['timestamp'] < self.error_window
        ]
        
        if len(recent_errors) >= self.error_threshold:
            logger.critical(f"Error threshold exceeded: {len(recent_errors)} errors")
            self.health_status = "critical"
            await self._attempt_recovery()
    
    async def _attempt_recovery(self):
        """Attempt to recover from critical errors."""
        if self.recovery_attempts >= self.max_recovery_attempts:
            logger.critical("Max recovery attempts reached")
            return
        
        self.recovery_attempts += 1
        logger.info(f"Attempting recovery (attempt {self.recovery_attempts})")
        
        try:
            # Clear error cache
            self.last_errors.clear()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Restart critical tasks
            await self._restart_critical_tasks()
            
            # Test Discord connection
            await self._test_discord_connection()
            
            logger.info("Recovery attempt completed")
            
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            await self._handle_critical_error(e)
    
    async def _restart_critical_tasks(self):
        """Restart critical bot tasks."""
        try:
            # This is where you'd restart important background tasks
            # Example: restart database connections, web servers, etc.
            
            # Test database connection if you have one
            if hasattr(self.bot, 'db') and hasattr(self.bot.db, 'conn'):
                try:
                    await self.bot.db.conn.execute('SELECT 1')
                    logger.info("Database connection verified")
                except Exception as e:
                    logger.error(f"Database connection failed: {e}")
                    # Attempt to reconnect database
                    await self._reconnect_database()
            
        except Exception as e:
            logger.error(f"Task restart failed: {e}")
    
    async def _reconnect_database(self):
        """Attempt to reconnect database."""
        try:
            if hasattr(self.bot, 'db'):
                # Close existing connection
                if hasattr(self.bot.db, 'conn') and self.bot.db.conn:
                    await self.bot.db.conn.close()
                
                # Reinitialize database
                await self.bot.db.initialize()
                logger.info("Database reconnected successfully")
                
        except Exception as e:
            logger.error(f"Database reconnection failed: {e}")
    
    async def _test_discord_connection(self):
        """Test Discord API connection."""
        try:
            # Simple API test
            await self.bot.fetch_user(self.bot.user.id)
            logger.info("Discord connection verified")
            
        except Exception as e:
            logger.error(f"Discord connection test failed: {e}")
            raise
    
    async def _attempt_memory_cleanup(self):
        """Attempt to free memory."""
        try:
            import gc
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")
            
            # Clear caches if available
            if hasattr(self.bot, 'command_cache'):
                self.bot.command_cache.clear()
            
            # Clear message cache
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    if hasattr(channel, '_state'):
                        channel._state.clear_messages(channel.id)
            
            logger.info("Memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    async def _update_recovery_status(self):
        """Update recovery status based on current health."""
        if self.health_status == "healthy" and self.recovery_attempts > 0:
            logger.info("Bot has recovered from errors")
            self.recovery_attempts = 0
    
    async def _handle_critical_error(self, error):
        """Handle critical errors."""
        self.error_count += 1
        error_info = {
            'timestamp': time.time(),
            'error': str(error),
            'traceback': traceback.format_exc(),
            'type': 'critical'
        }
        self.last_errors.append(error_info)
        
        # Log critical error
        logger.critical(f"Critical error handled: {error}")
        
        # Attempt recovery if not already in progress
        if self.recovery_attempts < self.max_recovery_attempts:
            await self._attempt_recovery()
    
    async def _log_health_status(self):
        """Log current health status."""
        logger.info(f"Health Status: {self.health_status}")
        logger.info(f"Uptime: {self.metrics['uptime']} seconds")
        logger.info(f"Memory Usage: {self.metrics['memory_usage']}%")
        logger.info(f"Errors: {self.error_count}")
        logger.info(f"Guilds: {self.metrics['guild_count']}")
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors and track them."""
        self.error_count += 1
        
        error_info = {
            'timestamp': time.time(),
            'error': str(error),
            'command': ctx.command.name if ctx.command else 'unknown',
            'guild': ctx.guild.id if ctx.guild else None,
            'user': ctx.author.id,
            'type': 'command'
        }
        self.last_errors.append(error_info)
        
        # Log the error
        logger.error(f"Command error in {ctx.command}: {error}")
        
        # Handle specific error types
        if isinstance(error, commands.CommandOnCooldown):
            return  # Don't treat cooldowns as critical
        elif isinstance(error, commands.MissingPermissions):
            return  # Don't treat permission errors as critical
        elif isinstance(error, discord.HTTPException) and error.status == 500:
            # Handle 500 errors specifically
            await self._handle_500_error(ctx, error)
        
        # Check if this pushes us over the error threshold
        await self._check_error_threshold()
    
    async def _handle_500_error(self, ctx, error):
        """Specifically handle 500 internal server errors."""
        logger.error(f"500 Internal Server Error in {ctx.command}: {error}")
        
        # Mark as degraded status
        self.health_status = "degraded"
        
        # Attempt to retry the command after a delay
        try:
            await asyncio.sleep(2)  # Wait 2 seconds
            await ctx.send("⚠️ Server error occurred. Attempting recovery...")
            
            # Test connection
            await self._test_discord_connection()
            
        except Exception as retry_error:
            logger.error(f"500 error recovery failed: {retry_error}")
            await ctx.send("❌ Server error - please try again in a moment.")
    
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Handle general bot errors."""
        self.error_count += 1
        
        error_info = {
            'timestamp': time.time(),
            'event': event,
            'error': traceback.format_exc(),
            'type': 'event'
        }
        self.last_errors.append(error_info)
        
        logger.error(f"Event error in {event}: {traceback.format_exc()}")
        
        # Check error threshold
        await self._check_error_threshold()
    
    def get_health_data(self):
        """Get health data for API endpoints."""
        return {
            'status': self.health_status,
            'uptime': int(time.time() - self.start_time),
            'last_check': self.last_health_check.isoformat(),
            'metrics': self.metrics,
            'error_count': self.error_count,
            'recent_errors': len([
                e for e in self.last_errors
                if time.time() - e['timestamp'] < 300  # Last 5 minutes
            ]),
            'recovery_attempts': self.recovery_attempts,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @commands.command(name='health')
    @commands.has_permissions(administrator=True)
    async def health_command(self, ctx):
        """Display bot health information."""
        health_data = self.get_health_data()
        
        embed = discord.Embed(
            title="🏥 Bot Health Status",
            color=discord.Color.green() if self.health_status == "healthy" else discord.Color.orange() if self.health_status == "degraded" else discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Overall Status",
            value=f"**{self.health_status.upper()}** ✅" if self.health_status == "healthy" else f"**{self.health_status.upper()}** ⚠️" if self.health_status == "degraded" else f"**{self.health_status.upper()}** ❌",
            inline=False
        )
        
        embed.add_field(
            name="Uptime",
            value=f"{health_data['uptime'] // 3600}h {(health_data['uptime'] % 3600) // 60}m",
            inline=True
        )
        
        embed.add_field(
            name="Latency",
            value=f"{self.metrics['latency']}ms",
            inline=True
        )
        
        embed.add_field(
            name="Memory",
            value=f"{self.metrics['memory_usage']}%",
            inline=True
        )
        
        embed.add_field(
            name="Errors (Total)",
            value=str(self.error_count),
            inline=True
        )
        
        embed.add_field(
            name="Recent Errors",
            value=str(health_data['recent_errors']),
            inline=True
        )
        
        embed.add_field(
            name="Guilds",
            value=str(self.metrics['guild_count']),
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='recover')
    @commands.has_permissions(administrator=True)
    async def manual_recovery(self, ctx):
        """Manually trigger recovery procedures."""
        await ctx.send("🔄 Initiating manual recovery...")
        
        try:
            await self._attempt_recovery()
            await ctx.send("✅ Recovery procedures completed.")
            
        except Exception as e:
            await ctx.send(f"❌ Recovery failed: {str(e)}")

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(HealthMonitor(bot))
    logger.info("Health Monitor cog loaded successfully")
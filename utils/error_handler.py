import discord
from discord.ext import commands
import logging
import traceback
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AdvancedErrorHandler:
    """Advanced error handling system for Discord bots."""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_log_channel = None
        self.retry_attempts = {}
        self.max_retries = 3
        self.retry_delay = 2.0
        
    def set_error_log_channel(self, channel_id: int):
        """Set the channel for error logging."""
        self.error_log_channel = channel_id
    
    async def handle_command_error(self, ctx, error):
        """Enhanced command error handling with recovery mechanisms."""
        
        # Get error details
        error_id = f"{ctx.command}_{ctx.guild.id if ctx.guild else 'dm'}_{int(datetime.utcnow().timestamp())}"
        
        # Log the error
        logger.error(f"Command error [{error_id}]: {error}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Handle specific error types
        if isinstance(error, commands.CommandOnCooldown):
            await self._handle_cooldown_error(ctx, error)
            
        elif isinstance(error, commands.MissingPermissions):
            await self._handle_permission_error(ctx, error)
            
        elif isinstance(error, commands.BotMissingPermissions):
            await self._handle_bot_permission_error(ctx, error)
            
        elif isinstance(error, discord.HTTPException):
            await self._handle_http_error(ctx, error, error_id)
            
        elif isinstance(error, commands.CommandNotFound):
            # Silently ignore command not found errors
            return
            
        elif isinstance(error, commands.UserInputError):
            await self._handle_user_input_error(ctx, error)
            
        elif isinstance(error, discord.Forbidden):
            await self._handle_forbidden_error(ctx, error)
            
        elif isinstance(error, asyncio.TimeoutError):
            await self._handle_timeout_error(ctx, error)
            
        else:
            await self._handle_unexpected_error(ctx, error, error_id)
        
        # Log to error channel if configured
        await self._log_to_error_channel(ctx, error, error_id)
    
    async def _handle_cooldown_error(self, ctx, error):
        """Handle command cooldown errors."""
        try:
            time_left = round(error.retry_after, 1)
            await ctx.send(
                f"⏰ This command is on cooldown. Try again in {time_left} seconds.",
                delete_after=time_left
            )
        except:
            pass  # Fail silently if we can't send the message
    
    async def _handle_permission_error(self, ctx, error):
        """Handle user permission errors."""
        try:
            missing_perms = ', '.join(error.missing_permissions)
            await ctx.send(f"❌ You need the following permissions: `{missing_perms}`")
        except:
            pass
    
    async def _handle_bot_permission_error(self, ctx, error):
        """Handle bot permission errors."""
        try:
            missing_perms = ', '.join(error.missing_permissions)
            await ctx.send(f"❌ I need the following permissions: `{missing_perms}`")
        except:
            # Can't send message, possibly due to missing Send Messages permission
            try:
                await ctx.author.send(
                    f"❌ I don't have the required permissions in {ctx.guild.name}.\n"
                    f"Missing permissions: `{missing_perms}`"
                )
            except:
                pass  # Can't DM either
    
    async def _handle_http_error(self, ctx, error, error_id):
        """Handle Discord HTTP errors with retry logic."""
        
        if error.status == 500:
            # Internal Server Error - attempt retry
            await self._handle_500_error(ctx, error, error_id)
            
        elif error.status == 429:
            # Rate limited
            await self._handle_rate_limit(ctx, error)
            
        elif error.status == 503:
            # Service unavailable
            await self._handle_service_unavailable(ctx, error)
            
        else:
            try:
                await ctx.send(f"❌ Discord API error occurred (Status: {error.status}). Please try again.")
            except:
                pass
    
    async def _handle_500_error(self, ctx, error, error_id):
        """Handle 500 internal server errors with retry mechanism."""
        
        # Check if we've already tried to retry this command
        retry_key = f"{ctx.command}_{ctx.author.id}_{ctx.channel.id}"
        current_retries = self.retry_attempts.get(retry_key, 0)
        
        if current_retries < self.max_retries:
            try:
                # Inform user we're retrying
                retry_msg = await ctx.send(f"⚠️ Server error occurred. Retrying... (Attempt {current_retries + 1}/{self.max_retries})")
                
                # Wait before retry
                await asyncio.sleep(self.retry_delay)
                
                # Update retry count
                self.retry_attempts[retry_key] = current_retries + 1
                
                # Attempt to reinvoke the command
                try:
                    await ctx.reinvoke()
                    # If successful, clear retry count and update message
                    del self.retry_attempts[retry_key]
                    await retry_msg.edit(content="✅ Command completed successfully after retry.")
                    
                except Exception as retry_error:
                    if current_retries + 1 >= self.max_retries:
                        # Max retries reached
                        del self.retry_attempts[retry_key]
                        await retry_msg.edit(content="❌ Command failed after multiple attempts. Please try again later.")
                    else:
                        # Will retry again
                        await retry_msg.edit(content=f"⚠️ Retry failed. Trying again... (Attempt {current_retries + 2}/{self.max_retries})")
                        await self._handle_500_error(ctx, retry_error, error_id)
                
            except Exception as handling_error:
                logger.error(f"Error during 500 error handling: {handling_error}")
                # Clear retry count to prevent infinite loops
                if retry_key in self.retry_attempts:
                    del self.retry_attempts[retry_key]
        else:
            # Max retries reached
            try:
                await ctx.send("❌ Server error persists. Please try again later.")
            except:
                pass
            
            # Clear retry count
            if retry_key in self.retry_attempts:
                del self.retry_attempts[retry_key]
    
    async def _handle_rate_limit(self, ctx, error):
        """Handle rate limit errors."""
        try:
            await ctx.send("⚠️ Rate limited by Discord. Please wait a moment and try again.")
        except:
            pass
    
    async def _handle_service_unavailable(self, ctx, error):
        """Handle service unavailable errors."""
        try:
            await ctx.send("⚠️ Discord services are temporarily unavailable. Please try again later.")
        except:
            pass
    
    async def _handle_user_input_error(self, ctx, error):
        """Handle user input errors."""
        try:
            if hasattr(error, 'original') and isinstance(error.original, ValueError):
                await ctx.send(f"❌ Invalid input: {str(error.original)}")
            else:
                await ctx.send(f"❌ Invalid command usage. Use `{ctx.prefix}help {ctx.command}` for help.")
        except:
            pass
    
    async def _handle_forbidden_error(self, ctx, error):
        """Handle forbidden errors."""
        try:
            await ctx.send("❌ I don't have permission to perform this action.")
        except:
            # Try to DM the user if we can't send to channel
            try:
                await ctx.author.send(
                    f"❌ I don't have permission to perform the action in {ctx.guild.name if ctx.guild else 'DM'}."
                )
            except:
                pass
    
    async def _handle_timeout_error(self, ctx, error):
        """Handle timeout errors."""
        try:
            await ctx.send("⏰ Command timed out. Please try again.")
        except:
            pass
    
    async def _handle_unexpected_error(self, ctx, error, error_id):
        """Handle unexpected errors."""
        try:
            await ctx.send(f"❌ An unexpected error occurred. Error ID: `{error_id}`")
        except:
            pass
        
        # Log the full error for debugging
        logger.critical(f"Unexpected error [{error_id}]: {error}")
        logger.critical(f"Full traceback: {traceback.format_exc()}")
    
    async def _log_to_error_channel(self, ctx, error, error_id):
        """Log errors to a designated error channel."""
        if not self.error_log_channel:
            return
        
        try:
            channel = self.bot.get_channel(self.error_log_channel)
            if not channel:
                return
            
            embed = discord.Embed(
                title="⚠️ Command Error",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Error ID",
                value=f"`{error_id}`",
                inline=False
            )
            
            embed.add_field(
                name="Command",
                value=f"`{ctx.command}` in {ctx.channel.mention}" if ctx.guild else f"`{ctx.command}` in DM",
                inline=True
            )
            
            embed.add_field(
                name="User",
                value=f"{ctx.author} (`{ctx.author.id}`)",
                inline=True
            )
            
            embed.add_field(
                name="Error Type",
                value=f"`{type(error).__name__}`",
                inline=True
            )
            
            # Truncate error message if too long
            error_msg = str(error)
            if len(error_msg) > 1000:
                error_msg = error_msg[:1000] + "..."
            
            embed.add_field(
                name="Error Message",
                value=f"```python\n{error_msg}\n```",
                inline=False
            )
            
            await channel.send(embed=embed)
            
        except Exception as log_error:
            logger.error(f"Failed to log error to channel: {log_error}")

def setup_error_handler(bot, error_log_channel_id=None):
    """Setup the advanced error handler for a bot."""
    
    error_handler = AdvancedErrorHandler(bot)
    
    if error_log_channel_id:
        error_handler.set_error_log_channel(error_log_channel_id)
    
    @bot.event
    async def on_command_error(ctx, error):
        """Enhanced command error handler."""
        await error_handler.handle_command_error(ctx, error)
    
    logger.info("Advanced error handler setup completed")
    return error_handler
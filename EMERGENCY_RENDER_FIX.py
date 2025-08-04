#!/usr/bin/env python3
"""
Complete Discord moderation bot for Render.com deployment.
Loads both original commands and new advanced moderation features.
"""

import os
import discord
from discord.ext import commands
import logging
import asyncio
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MinimalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        """Load all commands - both original and new advanced moderation"""
        # Create data directory for warnings
        os.makedirs('data', exist_ok=True)
        
        # Initialize warnings file if it doesn't exist
        if not os.path.exists('data/warnings.json'):
            import json
            with open('data/warnings.json', 'w') as f:
                json.dump({}, f)
        
        try:
            # Load original moderation commands (without utils.checks dependency)
            original_commands = [
                'commands.ban',
                'commands.unban', 
                'commands.kick',
                'commands.unkick',
                'commands.mute',
                'commands.warn',
                'commands.unwarn'
            ]
            
            for module in original_commands:
                try:
                    await self.load_extension(module)
                    logger.info(f"Loaded original command: {module}")
                except Exception as e:
                    logger.warning(f"Could not load {module}: {e}")
            
            # Load advanced moderation cog (with 'adv' prefix)
            try:
                await self.load_extension('cogs.advanced_moderation')
                logger.info("Loaded advanced moderation cog")
            except Exception as e:
                logger.warning(f"Could not load advanced moderation: {e}")
            
            # Load status cog
            await self.add_cog(StatusCog(self))
            logger.info("Loaded status cog")
                
            logger.info("Command loading complete")
            
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}")
    
    async def on_ready(self):
        logger.info(f'{self.user} connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Log loaded commands
        command_count = len(self.commands)
        cog_count = len(self.cogs)
        logger.info(f'Loaded {command_count} commands across {cog_count} cogs')
        
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for moderation commands"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Handle command errors gracefully."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the necessary permissions to execute this command.")
            return
        
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Member not found. Please mention a valid user.")
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
            return
        
        # Log unexpected errors
        logger.error(f"Unexpected error in command {ctx.command}: {error}")
        await ctx.send("❌ An unexpected error occurred. Please try again later.")

class StatusCog(commands.Cog):
    """Status and help commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='status')
    async def status_command(self, ctx):
        """Show bot status and loaded commands."""
        embed = discord.Embed(
            title="🤖 Bot Status",
            color=discord.Color.green(),
            description=f"Bot is running with {len(self.bot.commands)} commands loaded"
        )
        
        # List loaded cogs
        if self.bot.cogs:
            cog_list = "\n".join([f"• {cog}" for cog in self.bot.cogs.keys()])
            embed.add_field(name="Loaded Modules", value=cog_list, inline=False)
        
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StatusCog(bot))

async def main():
    bot = MinimalBot()
    token = os.getenv('DISCORD_BOT_TOKEN') or os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error('No Discord token found in environment variables')
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f'Bot error: {e}')
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())
import logging
import asyncio
import discord
from discord.ext import commands
import os
from database import Database
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class AdvancedBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.moderation = True
        intents.reactions = True
        
        super().__init__(
            command_prefix=commands.when_mentioned_or(Config.PREFIX),
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True
        )
        
        self.db = Database()
        self.config = Config()
        
    async def setup_hook(self):
        """Setup hook called when bot is starting up"""
        # Initialize database
        await self.db.init_db()
        
        # Load all cogs (REMOVED PROBLEMATIC ONES)
        cogs = [
            'cogs.moderation',
            'cogs.automod',
            'cogs.reaction_roles',
            'cogs.logging',
            'cogs.welcome',
            'cogs.starboard',
          #  'cogs.fun',
            'cogs.advanced_moderation',
            'cogs.funcogs.discord_fun_commands',
            'cogs.discord_commands',
            'cogs.word_blacklist_commands',
            'cogs.userinfo',
            'cogs.privateuserinfo',
            'cogs.serverdisplay',
            'cogs.avatardisplay',
            'cogs.dice',
            'cogs.connect4',
            'cogs.rpsgame',
            'cogs.coinflip',
            'cogs.echo_command',
            'cogs.slowmode_command',
            'cogs.lockdown_command',
            'cogs.hangman_command',
            'cogs.guessnumber_command',
            'cogs.slots_command',
            'cogs.ship_command',
            'cogs.trigger_system',
            'cogs.eightball_command',
            'cogs.godzillafact_command',
            'cogs.discord_rules_command',
            'cogs.discord_pacificrimfact_command',
            'cogs.auto_reaction_feature',
            'cogs.welcome_feature',
            'cogs.partnership_announcer',
            'cogs.keepalive',  # Keep this one - it's the good Discord API keep-alive
            'cogs.alt_detection'
            # REMOVED: 'cogs.health_monitor' - This was causing HTTP errors
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logging.info(f'Loaded {cog}')
            except Exception as e:
                logging.error(f'Failed to load {cog}: {e}')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logging.info(f'Synced {len(synced)} command(s)')
        except Exception as e:
            logging.error(f'Failed to sync commands: {e}')
    
    async def on_ready(self):
        """Called when bot is ready"""
        logging.info(f'{self.user} has connected to Discord!')
        logging.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logging.info(f'Joined guild: {guild.name} ({guild.id})')
        
        # Initialize guild in database
        await self.db.init_guild(guild.id)
        
        # Update status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild"""
        logging.info(f'Left guild: {guild.name} ({guild.id})')
        
        # Update status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        else:
            logging.error(f'Unhandled error: {error}')
            await ctx.send("❌ An unexpected error occurred.")

async def main():
    """Main function to run the bot"""
    bot = AdvancedBot()
    
    # Start bot
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logging.error('DISCORD_TOKEN environment variable not set')
        return
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logging.info('Bot stopped by user')
    except Exception as e:
        logging.error(f'Bot error: {e}')
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())

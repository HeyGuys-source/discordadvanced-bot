import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordBlacklistCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GUILD_ID = 1338306024582418503
        self.db_pool = None
        
    async def ensure_db_connection(self):
        """Ensure database connection is established"""
        if self.db_pool is None:
            try:
                # Try multiple ways to get the DATABASE_URL
                database_url = (
                    os.getenv('DATABASE_URL') or 
                    os.environ.get('DATABASE_URL') or
                    os.getenv('PGDATABASE')
                )
                
                if not database_url:
                    # If still no URL, construct from individual components
                    host = os.getenv('PGHOST', 'localhost')
                    port = os.getenv('PGPORT', '5432')
                    user = os.getenv('PGUSER', 'postgres')
                    password = os.getenv('PGPASSWORD', '')
                    database = os.getenv('PGDATABASE', 'postgres')
                    
                    if host and user and database:
                        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                        logger.info("Constructed DATABASE_URL from individual environment variables")
                    else:
                        raise ValueError("No database connection information found in environment variables")
                
                self.db_pool = await asyncpg.create_pool(
                    database_url,
                    min_size=1,
                    max_size=5,
                    command_timeout=30
                )
                logger.info("Database pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise
        return self.db_pool

    @app_commands.command(name="createwordblacklist", description="Add a word to the blacklist with punishment")
    @app_commands.describe(
        message="The word or phrase to blacklist",
        punishment="Punishment for using this word"
    )
    @app_commands.choices(punishment=[
        app_commands.Choice(name="Ban", value="ban"),
        app_commands.Choice(name="Mute", value="mute"),
        app_commands.Choice(name="Kick", value="kick"),
        app_commands.Choice(name="Warn", value="warn")
    ])
    async def create_word_blacklist(self, interaction: discord.Interaction, message: str, punishment: str):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if not message.strip():
                await interaction.followup.send("Please provide a valid word or phrase to blacklist.", ephemeral=True)
                return
            
            if len(message) > 255:
                await interaction.followup.send("Word/phrase is too long. Maximum 255 characters.", ephemeral=True)
                return
            
            pool = await self.ensure_db_connection()
            
            async with pool.acquire() as conn:
                # Check if word exists
                existing = await conn.fetchrow(
                    "SELECT word, punishment FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                    message.strip()
                )
                
                if existing:
                    await interaction.followup.send(
                        f"The word '{existing['word']}' is already blacklisted with punishment: {existing['punishment']}",
                        ephemeral=True
                    )
                    return
                
                # Add word
                await conn.execute(
                    "INSERT INTO word_blacklist (word, punishment, created_by) VALUES ($1, $2, $3)",
                    message.strip(), punishment, interaction.user.id
                )
                
                embed = discord.Embed(
                    title="Word Blacklisted Successfully",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="Word/Phrase", value=f"`{message.strip()}`", inline=True)
                embed.add_field(name="Punishment", value=punishment.capitalize(), inline=True)
                embed.set_footer(text=f"Added by {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in create_word_blacklist: {e}")
            try:
                await interaction.followup.send(f"Error occurred: {str(e)}", ephemeral=True)
            except:
                pass

    @app_commands.command(name="removewordblacklist", description="Remove a word from the blacklist")
    @app_commands.describe(message="The word or phrase to remove from blacklist")
    async def remove_word_blacklist(self, interaction: discord.Interaction, message: str):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if not message.strip():
                await interaction.followup.send("Please provide a valid word or phrase to remove.", ephemeral=True)
                return
            
            pool = await self.ensure_db_connection()
            
            async with pool.acquire() as conn:
                # Check if word exists
                existing = await conn.fetchrow(
                    "SELECT word, punishment FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                    message.strip()
                )
                
                if not existing:
                    await interaction.followup.send(
                        f"The word '{message.strip()}' is not in the blacklist.",
                        ephemeral=True
                    )
                    return
                
                # Remove word
                await conn.execute(
                    "DELETE FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                    message.strip()
                )
                
                embed = discord.Embed(
                    title="Word Removed from Blacklist",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="Word/Phrase", value=f"`{existing['word']}`", inline=True)
                embed.add_field(name="Previous Punishment", value=existing['punishment'].capitalize(), inline=True)
                embed.set_footer(text=f"Removed by {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in remove_word_blacklist: {e}")
            try:
                await interaction.followup.send(f"Error occurred: {str(e)}", ephemeral=True)
            except:
                pass

    @app_commands.command(name="wordblacklists", description="Show all blacklisted words")
    async def word_blacklists(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            pool = await self.ensure_db_connection()
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT word, punishment, created_at FROM word_blacklist ORDER BY created_at DESC"
                )
                
                if not rows:
                    embed = discord.Embed(
                        title="Word Blacklist",
                        description="No words are currently blacklisted.",
                        color=discord.Color.pink(),
                        timestamp=discord.utils.utcnow()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="Word Blacklist",
                    description=f"Total blacklisted words: {len(rows)}",
                    color=discord.Color.pink(),
                    timestamp=discord.utils.utcnow()
                )
                
                # Group by punishment
                punishments = {'ban': [], 'mute': [], 'kick': [], 'warn': []}
                for row in rows:
                    punishments[row['punishment']].append(row['word'])
                
                emojis = {'ban': '🔨', 'mute': '🔇', 'kick': '👢', 'warn': '⚠️'}
                
                for punishment_type, words in punishments.items():
                    if words:
                        emoji = emojis.get(punishment_type, '❓')
                        word_list = ', '.join([f"`{word}`" for word in words])
                        
                        if len(word_list) > 1024:
                            word_list = word_list[:1020] + "..."
                        
                        embed.add_field(
                            name=f"{emoji} {punishment_type.capitalize()} ({len(words)} words)",
                            value=word_list,
                            inline=False
                        )
                
                embed.set_footer(text="Use /removewordblacklist to remove words")
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in word_blacklists: {e}")
            try:
                await interaction.followup.send(f"Error occurred: {str(e)}", ephemeral=True)
            except:
                pass

# Setup functions
async def setup(bot):
    await bot.add_cog(WordBlacklistCommands(bot))

def add_word_blacklist_commands(bot):
    """Add word blacklist commands directly to the bot tree"""
    
    @bot.tree.command(name="createwordblacklist", description="Add a word to the blacklist with punishment")
    @app_commands.describe(
        message="The word or phrase to blacklist",
        punishment="Punishment for using this word"
    )
    @app_commands.choices(punishment=[
        app_commands.Choice(name="Ban", value="ban"),
        app_commands.Choice(name="Mute", value="mute"),
        app_commands.Choice(name="Kick", value="kick"),
        app_commands.Choice(name="Warn", value="warn")
    ])
    async def create_word_blacklist(interaction: discord.Interaction, message: str, punishment: str):
        await _handle_create_word_blacklist(interaction, message, punishment)
    
    @bot.tree.command(name="removewordblacklist", description="Remove a word from the blacklist")
    @app_commands.describe(message="The word or phrase to remove from blacklist")
    async def remove_word_blacklist(interaction: discord.Interaction, message: str):
        await _handle_remove_word_blacklist(interaction, message)
    
    @bot.tree.command(name="wordblacklists", description="Show all blacklisted words")
    async def word_blacklists(interaction: discord.Interaction):
        await _handle_word_blacklists(interaction)

# Command handlers
async def _handle_create_word_blacklist(interaction: discord.Interaction, message: str, punishment: str):
    try:
        await interaction.response.defer(ephemeral=True)
        
        if not message.strip():
            await interaction.followup.send("Please provide a valid word or phrase to blacklist.", ephemeral=True)
            return
        
        if len(message) > 255:
            await interaction.followup.send("Word/phrase is too long. Maximum 255 characters.", ephemeral=True)
            return
        
        pool = await _get_db_pool()
        
        async with pool.acquire() as conn:
            # Check if word exists
            existing = await conn.fetchrow(
                "SELECT word, punishment FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                message.strip()
            )
            
            if existing:
                await interaction.followup.send(
                    f"The word '{existing['word']}' is already blacklisted with punishment: {existing['punishment']}",
                    ephemeral=True
                )
                return
            
            # Add word
            await conn.execute(
                "INSERT INTO word_blacklist (word, punishment, created_by) VALUES ($1, $2, $3)",
                message.strip(), punishment, interaction.user.id
            )
            
            embed = discord.Embed(
                title="Word Blacklisted Successfully",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Word/Phrase", value=f"`{message.strip()}`", inline=True)
            embed.add_field(name="Punishment", value=punishment.capitalize(), inline=True)
            embed.set_footer(text=f"Added by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    except Exception as e:
        logger.error(f"Error in create_word_blacklist: {e}")
        try:
            await interaction.followup.send(f"Error occurred: {str(e)}", ephemeral=True)
        except:
            pass

async def _handle_remove_word_blacklist(interaction: discord.Interaction, message: str):
    try:
        await interaction.response.defer(ephemeral=True)
        
        if not message.strip():
            await interaction.followup.send("Please provide a valid word or phrase to remove.", ephemeral=True)
            return
        
        pool = await _get_db_pool()
        
        async with pool.acquire() as conn:
            # Check if word exists
            existing = await conn.fetchrow(
                "SELECT word, punishment FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                message.strip()
            )
            
            if not existing:
                await interaction.followup.send(
                    f"The word '{message.strip()}' is not in the blacklist.",
                    ephemeral=True
                )
                return
            
            # Remove word
            await conn.execute(
                "DELETE FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                message.strip()
            )
            
            embed = discord.Embed(
                title="Word Removed from Blacklist",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Word/Phrase", value=f"`{existing['word']}`", inline=True)
            embed.add_field(name="Previous Punishment", value=existing['punishment'].capitalize(), inline=True)
            embed.set_footer(text=f"Removed by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    except Exception as e:
        logger.error(f"Error in remove_word_blacklist: {e}")
        try:
            await interaction.followup.send(f"Error occurred: {str(e)}", ephemeral=True)
        except:
            pass

async def _handle_word_blacklists(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        
        pool = await _get_db_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT word, punishment, created_at FROM word_blacklist ORDER BY created_at DESC"
            )
            
            if not rows:
                embed = discord.Embed(
                    title="Word Blacklist",
                    description="No words are currently blacklisted.",
                    color=discord.Color.pink(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="Word Blacklist",
                description=f"Total blacklisted words: {len(rows)}",
                color=discord.Color.pink(),
                timestamp=discord.utils.utcnow()
            )
            
            # Group by punishment
            punishments = {'ban': [], 'mute': [], 'kick': [], 'warn': []}
            for row in rows:
                punishments[row['punishment']].append(row['word'])
            
            emojis = {'ban': '🔨', 'mute': '🔇', 'kick': '👢', 'warn': '⚠️'}
            
            for punishment_type, words in punishments.items():
                if words:
                    emoji = emojis.get(punishment_type, '❓')
                    word_list = ', '.join([f"`{word}`" for word in words])
                    
                    if len(word_list) > 1024:
                        word_list = word_list[:1020] + "..."
                    
                    embed.add_field(
                        name=f"{emoji} {punishment_type.capitalize()} ({len(words)} words)",
                        value=word_list,
                        inline=False
                    )
            
            embed.set_footer(text="Use /removewordblacklist to remove words")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    except Exception as e:
        logger.error(f"Error in word_blacklists: {e}")
        try:
            await interaction.followup.send(f"Error occurred: {str(e)}", ephemeral=True)
        except:
            pass

# Database connection helper
_db_pool = None

async def _get_db_pool():
    """Get database connection pool"""
    global _db_pool
    if _db_pool is None:
        try:
            # Try multiple ways to get the DATABASE_URL
            database_url = (
                os.getenv('DATABASE_URL') or 
                os.environ.get('DATABASE_URL')
            )
            
            if not database_url:
                # If still no URL, construct from individual components
                host = os.getenv('PGHOST', 'localhost')
                port = os.getenv('PGPORT', '5432')
                user = os.getenv('PGUSER', 'postgres')
                password = os.getenv('PGPASSWORD', '')
                database = os.getenv('PGDATABASE', 'postgres')
                
                if host and user and database:
                    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                    logger.info("Constructed DATABASE_URL from individual environment variables")
                else:
                    raise ValueError("No database connection information found in environment variables")
            
            _db_pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=5,
                command_timeout=30
            )
            logger.info("Database pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    return _db_pool

# Example usage in bot.py:
"""
import discord
from discord.ext import commands
from working_blacklist_commands import add_word_blacklist_commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

add_word_blacklist_commands(bot)

bot.run('YOUR_BOT_TOKEN')
"""

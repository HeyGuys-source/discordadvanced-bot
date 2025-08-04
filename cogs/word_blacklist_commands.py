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
        
        # Guild ID for permissions
        self.GUILD_ID = 1338306024582418503
        
        # Database connection pool
        self.db_pool = None
        
    async def get_db_connection(self):
        """Get database connection pool"""
        if self.db_pool is None:
            try:
                self.db_pool = await asyncpg.create_pool(
                    os.getenv('DATABASE_URL'),
                    min_size=1,
                    max_size=10
                )
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
        """Add a word to the blacklist with specified punishment"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Validate input
            if not message.strip():
                await interaction.followup.send("❌ Please provide a valid word or phrase to blacklist.", ephemeral=True)
                return
            
            if len(message) > 255:
                await interaction.followup.send("❌ Word/phrase is too long. Maximum 255 characters allowed.", ephemeral=True)
                return
            
            # Get database connection
            pool = await self.get_db_connection()
            
            async with pool.acquire() as conn:
                try:
                    # Check if word already exists
                    existing = await conn.fetchrow(
                        "SELECT word, punishment FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                        message.strip()
                    )
                    
                    if existing:
                        await interaction.followup.send(
                            f"❌ The word '{existing['word']}' is already blacklisted with punishment: {existing['punishment']}",
                            ephemeral=True
                        )
                        return
                    
                    # Add word to blacklist
                    await conn.execute(
                        "INSERT INTO word_blacklist (word, punishment, created_by) VALUES ($1, $2, $3)",
                        message.strip(), punishment, interaction.user.id
                    )
                    
                    # Create success embed
                    embed = discord.Embed(
                        title="✅ Word Blacklisted",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="Word/Phrase", value=f"`{message.strip()}`", inline=True)
                    embed.add_field(name="Punishment", value=punishment.capitalize(), inline=True)
                    embed.set_footer(text=f"Added by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    logger.error(f"Database error in create_word_blacklist: {e}")
                    await interaction.followup.send("❌ Database error occurred while adding word to blacklist.", ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error in create_word_blacklist command: {e}")
            await interaction.followup.send("❌ An unexpected error occurred.", ephemeral=True)

    @app_commands.command(name="removewordblacklist", description="Remove a word from the blacklist")
    @app_commands.describe(message="The word or phrase to remove from blacklist")
    async def remove_word_blacklist(self, interaction: discord.Interaction, message: str):
        """Remove a word from the blacklist"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Validate input
            if not message.strip():
                await interaction.followup.send("❌ Please provide a valid word or phrase to remove.", ephemeral=True)
                return
            
            # Get database connection
            pool = await self.get_db_connection()
            
            async with pool.acquire() as conn:
                try:
                    # Check if word exists
                    existing = await conn.fetchrow(
                        "SELECT word, punishment FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                        message.strip()
                    )
                    
                    if not existing:
                        await interaction.followup.send(
                            f"❌ The word '{message.strip()}' is not in the blacklist.",
                            ephemeral=True
                        )
                        return
                    
                    # Remove word from blacklist
                    await conn.execute(
                        "DELETE FROM word_blacklist WHERE LOWER(word) = LOWER($1)",
                        message.strip()
                    )
                    
                    # Create success embed
                    embed = discord.Embed(
                        title="✅ Word Removed from Blacklist",
                        color=discord.Color.orange(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="Word/Phrase", value=f"`{existing['word']}`", inline=True)
                    embed.add_field(name="Previous Punishment", value=existing['punishment'].capitalize(), inline=True)
                    embed.set_footer(text=f"Removed by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    logger.error(f"Database error in remove_word_blacklist: {e}")
                    await interaction.followup.send("❌ Database error occurred while removing word from blacklist.", ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error in remove_word_blacklist command: {e}")
            await interaction.followup.send("❌ An unexpected error occurred.", ephemeral=True)

    @app_commands.command(name="wordblacklists", description="Show all blacklisted words")
    async def word_blacklists(self, interaction: discord.Interaction):
        """Display all blacklisted words in a formatted embed"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Get database connection
            pool = await self.get_db_connection()
            
            async with pool.acquire() as conn:
                try:
                    # Get all blacklisted words
                    rows = await conn.fetch(
                        "SELECT word, punishment, created_at FROM word_blacklist ORDER BY created_at DESC"
                    )
                    
                    if not rows:
                        embed = discord.Embed(
                            title="📝 Word Blacklist",
                            description="No words are currently blacklisted.",
                            color=discord.Color.pink(),
                            timestamp=discord.utils.utcnow()
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    # Create main embed
                    embed = discord.Embed(
                        title="📝 Word Blacklist",
                        description=f"Total blacklisted words: {len(rows)}",
                        color=discord.Color.pink(),
                        timestamp=discord.utils.utcnow()
                    )
                    
                    # Group words by punishment type
                    punishments = {'ban': [], 'mute': [], 'kick': [], 'warn': []}
                    
                    for row in rows:
                        punishments[row['punishment']].append(row['word'])
                    
                    # Add fields for each punishment type
                    punishment_emojis = {
                        'ban': '🔨',
                        'mute': '🔇',
                        'kick': '👢',
                        'warn': '⚠️'
                    }
                    
                    for punishment_type, words in punishments.items():
                        if words:
                            emoji = punishment_emojis.get(punishment_type, '❓')
                            word_list = ', '.join([f"`{word}`" for word in words])
                            
                            # Discord embed field value limit is 1024 characters
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
                    logger.error(f"Database error in word_blacklists: {e}")
                    await interaction.followup.send("❌ Database error occurred while fetching blacklist.", ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error in word_blacklists command: {e}")
            await interaction.followup.send("❌ An unexpected error occurred.", ephemeral=True)

# Function to setup the cog (for integration with existing bot.py)
async def setup(bot):
    await bot.add_cog(WordBlacklistCommands(bot))

# Alternative setup for direct integration into bot.py
def add_word_blacklist_commands(bot):
    """
    Add word blacklist commands directly to your bot instance.
    Call this function in your bot.py after creating your bot instance.
    
    Usage in bot.py:
    from word_blacklist_commands import add_word_blacklist_commands
    add_word_blacklist_commands(bot)
    """
    
    # Create a single instance of the cog to share across commands
    cog_instance = WordBlacklistCommands(bot)
    
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
        await cog_instance.create_word_blacklist(interaction, message, punishment)
    
    @bot.tree.command(name="removewordblacklist", description="Remove a word from the blacklist")
    @app_commands.describe(message="The word or phrase to remove from blacklist")
    async def remove_word_blacklist(interaction: discord.Interaction, message: str):
        await cog_instance.remove_word_blacklist(interaction, message)
    
    @bot.tree.command(name="wordblacklists", description="Show all blacklisted words")
    async def word_blacklists(interaction: discord.Interaction):
        await cog_instance.word_blacklists(interaction)

# Example usage in your main bot.py:
"""
import discord
from discord.ext import commands
from word_blacklist_commands import add_word_blacklist_commands

# Your existing bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Add the word blacklist commands
add_word_blacklist_commands(bot)

# Your existing bot events and other code...

bot.run('YOUR_BOT_TOKEN')
"""
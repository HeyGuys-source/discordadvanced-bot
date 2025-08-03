import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import math
import random
from datetime import datetime, timedelta
from utils.helpers import create_embed, create_success_embed, create_error_embed, format_relative_time
from utils.checks import has_permissions

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns = {}  # User cooldowns for XP gain
        self.xp_per_message = 15
        self.cooldown_time = 60  # 1 minute cooldown between XP gains
    
    async def get_user_level_data(self, guild_id: int, user_id: int):
        """Get user's level data from database"""
        async with self.bot.db.get_connection() as conn:
            async with conn.execute(
                "SELECT * FROM user_levels WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            ) as cursor:
                return await cursor.fetchone()
    
    async def create_user_level_data(self, guild_id: int, user_id: int):
        """Create new user level data"""
        async with self.bot.db.get_connection() as conn:
            await conn.execute(
                """INSERT OR IGNORE INTO user_levels 
                   (guild_id, user_id, xp, level, total_xp, last_message) 
                   VALUES (?, ?, 0, 1, 0, ?)""",
                (guild_id, user_id, datetime.utcnow().isoformat())
            )
            await conn.commit()
    
    async def update_user_xp(self, guild_id: int, user_id: int, xp_gain: int):
        """Update user's XP and level"""
        await self.create_user_level_data(guild_id, user_id)
        
        async with self.bot.db.get_connection() as conn:
            # Get current data
            async with conn.execute(
                "SELECT xp, level, total_xp FROM user_levels WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            ) as cursor:
                result = await cursor.fetchone()
                if not result:
                    return None
                
                current_xp, current_level, total_xp = result
            
            # Calculate new values
            new_xp = current_xp + xp_gain
            new_total_xp = total_xp + xp_gain
            new_level = self.calculate_level(new_total_xp)
            
            # Check if leveled up
            leveled_up = new_level > current_level
            
            # Update database
            await conn.execute(
                """UPDATE user_levels 
                   SET xp = ?, level = ?, total_xp = ?, last_message = ?
                   WHERE guild_id = ? AND user_id = ?""",
                (new_xp, new_level, new_total_xp, datetime.utcnow().isoformat(), guild_id, user_id)
            )
            await conn.commit()
            
            return {
                'old_level': current_level,
                'new_level': new_level,
                'xp': new_xp,
                'total_xp': new_total_xp,
                'leveled_up': leveled_up
            }
    
    def calculate_level(self, total_xp: int) -> int:
        """Calculate level based on total XP"""
        # Level formula: level = floor(sqrt(total_xp / 100))
        return max(1, int(math.sqrt(total_xp / 100)))
    
    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate total XP needed for a specific level"""
        return (level ** 2) * 100
    
    def calculate_xp_for_next_level(self, current_level: int) -> int:
        """Calculate XP needed for next level"""
        return self.calculate_xp_for_level(current_level + 1)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Give XP for messages"""
        if message.author.bot or not message.guild:
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Check cooldown
        cooldown_key = f"{guild_id}_{user_id}"
        now = datetime.utcnow()
        
        if cooldown_key in self.xp_cooldowns:
            if now < self.xp_cooldowns[cooldown_key]:
                return
        
        # Set cooldown
        self.xp_cooldowns[cooldown_key] = now + timedelta(seconds=self.cooldown_time)
        
        # Add random XP (15 ± 5)
        xp_gain = self.xp_per_message + random.randint(-5, 5)
        
        # Update user XP
        result = await self.update_user_xp(guild_id, user_id, xp_gain)
        
        if result and result['leveled_up']:
            # Send level up message
            embed = create_success_embed(
                "Level Up!",
                f"🎉 {message.author.mention} reached **Level {result['new_level']}**!\n"
                f"Total XP: {result['total_xp']:,}"
            )
            try:
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass  # Ignore if we can't send messages
    
    @app_commands.command(name="rank", description="View your or another user's rank and level")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        """Show user's rank and level"""
        if not interaction.guild:
            return
        target = user or interaction.user
        if not isinstance(target, discord.Member):
            target = interaction.guild.get_member(target.id)
            if not target:
                await interaction.response.send_message(
                    embed=create_error_embed("Error", "User not found in this server!"),
                    ephemeral=True
                )
                return
        
        if target.bot:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Bots don't have levels!"),
                ephemeral=True
            )
            return
        
        # Get user data
        data = await self.get_user_level_data(interaction.guild.id, target.id)
        
        if not data:
            await self.create_user_level_data(interaction.guild.id, target.id)
            data = await self.get_user_level_data(interaction.guild.id, target.id)
        
        # Get user's rank
        async with self.bot.db.get_connection() as conn:
            async with conn.execute(
                """SELECT COUNT(*) + 1 FROM user_levels 
                   WHERE guild_id = ? AND total_xp > ?""",
                (interaction.guild.id, data[4])  # total_xp is index 4
            ) as cursor:
                rank = (await cursor.fetchone())[0]
        
        current_level = data[3]  # level is index 3
        total_xp = data[4]  # total_xp is index 4
        
        # Calculate XP progress for current level
        current_level_xp = self.calculate_xp_for_level(current_level)
        next_level_xp = self.calculate_xp_for_next_level(current_level)
        progress_xp = total_xp - current_level_xp
        needed_xp = next_level_xp - current_level_xp
        
        # Create progress bar
        progress_percent = min(progress_xp / needed_xp, 1.0) if needed_xp > 0 else 1.0
        bar_length = 20
        filled_length = int(bar_length * progress_percent)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        embed = create_embed(
            f"📊 {target.display_name}'s Rank",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🏆 Rank", 
            value=f"#{rank:,}", 
            inline=True
        )
        embed.add_field(
            name="📈 Level", 
            value=f"{current_level:,}", 
            inline=True
        )
        embed.add_field(
            name="✨ Total XP", 
            value=f"{total_xp:,}", 
            inline=True
        )
        
        embed.add_field(
            name="📊 Progress to Next Level",
            value=f"{bar}\n{progress_xp:,} / {needed_xp:,} XP ({progress_percent:.1%})",
            inline=False
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"XP per message: {self.xp_per_message} (±5)")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="View the server's XP leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        """Show server leaderboard"""
        if not interaction.guild:
            return
        async with self.bot.db.get_connection() as conn:
            async with conn.execute(
                """SELECT user_id, level, total_xp 
                   FROM user_levels 
                   WHERE guild_id = ? 
                   ORDER BY total_xp DESC 
                   LIMIT 10""",
                (interaction.guild.id,)
            ) as cursor:
                results = await cursor.fetchall()
        
        if not results:
            await interaction.response.send_message(
                embed=create_error_embed("No Data", "No one has earned XP yet!"),
                ephemeral=True
            )
            return
        
        embed = create_embed(
            f"🏆 {interaction.guild.name} Leaderboard",
            "Top 10 members by total XP",
            color=0xffd700
        )
        
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (user_id, level, total_xp) in enumerate(results, 1):
            user = interaction.guild.get_member(user_id)
            if user:
                medal = medals[i-1] if i <= 3 else f"`#{i:2d}`"
                leaderboard_text += f"{medal} **{user.display_name}** - Level {level:,} ({total_xp:,} XP)\n"
            else:
                medal = medals[i-1] if i <= 3 else f"`#{i:2d}`"
                leaderboard_text += f"{medal} *Unknown User* - Level {level:,} ({total_xp:,} XP)\n"
        
        embed.description = leaderboard_text
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="addxp", description="Add XP or set level for a user (Admin only)")
    @app_commands.describe(
        user="The user to modify",
        action="Whether to add XP or set level",
        amount="Amount of XP to add or level to set"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add XP", value="add_xp"),
        app_commands.Choice(name="Set Level", value="set_level")
    ])
    async def add_xp(self, interaction: discord.Interaction, user: discord.Member, 
                     action: app_commands.Choice[str], amount: int):
        """Add XP or set level for a user"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=create_error_embed("Permission Denied", "You need Administrator permissions to use this command!"),
                ephemeral=True
            )
            return
        
        if user.bot:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Cannot modify XP for bots!"),
                ephemeral=True
            )
            return
        
        if amount < 0:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Amount must be positive!"),
                ephemeral=True
            )
            return
        
        await self.create_user_level_data(interaction.guild.id, user.id)
        
        if action.value == "add_xp":
            result = await self.update_user_xp(interaction.guild.id, user.id, amount)
            embed = create_success_embed(
                "XP Added",
                f"Added {amount:,} XP to {user.mention}\n"
                f"New Level: {result['new_level']:,}\n"
                f"Total XP: {result['total_xp']:,}"
            )
        else:  # set_level
            target_xp = self.calculate_xp_for_level(amount)
            async with self.bot.db.get_connection() as conn:
                await conn.execute(
                    """UPDATE user_levels 
                       SET level = ?, total_xp = ?, xp = ?
                       WHERE guild_id = ? AND user_id = ?""",
                    (amount, target_xp, target_xp, interaction.guild.id, user.id)
                )
                await conn.commit()
            
            embed = create_success_embed(
                "Level Set",
                f"Set {user.mention}'s level to {amount:,}\n"
                f"Total XP: {target_xp:,}"
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
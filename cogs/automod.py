import discord
from discord.ext import commands
import re
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

class AutoMod(commands.Cog):
    """Automatic moderation system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = defaultdict(lambda: deque())
        self.violation_tracker = defaultdict(int)
        
        # Spam filters
        self.spam_threshold = 5  # Messages per interval
        self.spam_interval = 10  # Seconds
        
        # Content filters
        self.invite_pattern = re.compile(r'discord\.gg\/[a-zA-Z0-9]+|discordapp\.com\/invite\/[a-zA-Z0-9]+')
        self.link_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        
        # Blocked words (example list - should be configurable)
        self.blocked_words = [
            'spam', 'scam', 'hack', 'cheat', 
            # Add more words as needed
        ]
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor messages for automod violations"""
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        # Check if automod is enabled for this guild
        settings = await self.bot.db.get_guild_settings(message.guild.id)
        if not settings or not settings.get('automod_enabled', True):
            return
        
        # Skip if user has manage_messages permission
        if message.author.guild_permissions.manage_messages:
            return
        
        # Check for violations
        violations = []
        
        # Spam detection
        if await self._check_spam(message):
            violations.append('spam')
        
        # Excessive mentions
        if await self._check_mentions(message):
            violations.append('excessive_mentions')
        
        # Excessive links
        if await self._check_links(message):
            violations.append('excessive_links')
        
        # Discord invites
        if await self._check_invites(message):
            violations.append('discord_invite')
        
        # Blocked words
        if await self._check_blocked_words(message):
            violations.append('blocked_words')
        
        # Excessive caps
        if await self._check_caps(message):
            violations.append('excessive_caps')
        
        # Take action if violations found
        if violations:
            await self._handle_violations(message, violations)
    
    async def _check_spam(self, message):
        """Check for spam (rapid message sending)"""
        user_id = message.author.id
        now = datetime.utcnow()
        
        # Clean old messages
        user_messages = self.spam_tracker[user_id]
        while user_messages and (now - user_messages[0]).total_seconds() > self.spam_interval:
            user_messages.popleft()
        
        # Add current message
        user_messages.append(now)
        
        # Check if threshold exceeded
        return len(user_messages) > self.spam_threshold
    
    async def _check_mentions(self, message):
        """Check for excessive mentions"""
        mention_count = len(message.mentions) + len(message.role_mentions)
        return mention_count > 5
    
    async def _check_links(self, message):
        """Check for excessive links"""
        links = self.link_pattern.findall(message.content)
        return len(links) > 3
    
    async def _check_invites(self, message):
        """Check for Discord invite links"""
        return bool(self.invite_pattern.search(message.content))
    
    async def _check_blocked_words(self, message):
        """Check for blocked words"""
        content_lower = message.content.lower()
        return any(word in content_lower for word in self.blocked_words)
    
    async def _check_caps(self, message):
        """Check for excessive capital letters"""
        if len(message.content) < 10:
            return False
        
        caps_count = sum(1 for c in message.content if c.isupper())
        caps_ratio = caps_count / len(message.content)
        
        return caps_ratio > 0.7  # 70% caps
    
    async def _handle_violations(self, message, violations):
        """Handle automod violations"""
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Increment violation count
        self.violation_tracker[f"{guild_id}_{user_id}"] += len(violations)
        total_violations = self.violation_tracker[f"{guild_id}_{user_id}"]
        
        action_taken = []
        
        try:
            # Always delete the message
            await message.delete()
            action_taken.append("Message deleted")
            
            # Escalating punishments based on violation count
            if total_violations >= 10:
                # Timeout for 1 hour
                until = discord.utils.utcnow() + timedelta(hours=1)
                await message.author.timeout(until, reason="AutoMod: Repeated violations")
                action_taken.append("1 hour timeout")
                
            elif total_violations >= 5:
                # Timeout for 10 minutes
                until = discord.utils.utcnow() + timedelta(minutes=10)
                await message.author.timeout(until, reason="AutoMod: Multiple violations")
                action_taken.append("10 minute timeout")
            
            # Send warning to user
            try:
                embed = discord.Embed(
                    title="AutoMod Violation",
                    description=f"Your message in **{message.guild.name}** was removed for violating server rules.",
                    color=0xED4245
                )
                embed.add_field(name="Violations", value=", ".join(violations), inline=False)
                embed.add_field(name="Total Violations", value=str(total_violations), inline=False)
                if len(action_taken) > 1:
                    embed.add_field(name="Action Taken", value=", ".join(action_taken), inline=False)
                
                await message.author.send(embed=embed)
            except:
                pass  # User has DMs disabled
            
            # Log to database
            await self.bot.db.add_automod_violation(
                guild_id,
                user_id,
                ", ".join(violations),
                message.content[:500],  # Truncate long messages
                ", ".join(action_taken)
            )
            
            # Send notification to log channel
            settings = await self.bot.db.get_guild_settings(guild_id)
            if settings and settings.get('log_channel_id'):
                log_channel = message.guild.get_channel(settings['log_channel_id'])
                if log_channel:
                    embed = discord.Embed(
                        title="AutoMod Action",
                        color=0xED4245
                    )
                    embed.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=False)
                    embed.add_field(name="Channel", value=message.channel.mention, inline=False)
                    embed.add_field(name="Violations", value=", ".join(violations), inline=False)
                    embed.add_field(name="Action Taken", value=", ".join(action_taken), inline=False)
                    embed.add_field(name="Total Violations", value=str(total_violations), inline=False)
                    
                    # Add message content (truncated)
                    content = message.content[:1000] + "..." if len(message.content) > 1000 else message.content
                    embed.add_field(name="Message Content", value=f"```{content}```", inline=False)
                    
                    await log_channel.send(embed=embed)
        
        except discord.Forbidden:
            logging.warning(f"Missing permissions for automod action in guild {guild_id}")
        except Exception as e:
            logging.error(f"AutoMod error: {e}")
    
    @discord.app_commands.command(name="automod", description="Configure AutoMod settings")
    @discord.app_commands.describe(
        enabled="Enable or disable AutoMod",
        spam_threshold="Number of messages before spam detection triggers",
        spam_interval="Time window for spam detection (seconds)"
    )
    async def automod_config(self, interaction: discord.Interaction, 
                           enabled: bool = None,
                           spam_threshold: int = None,
                           spam_interval: int = None):
        """Configure AutoMod settings"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to configure AutoMod.", ephemeral=True)
            return
        
        if enabled is not None:
            await self.bot.db.update_guild_setting(interaction.guild.id, 'automod_enabled', enabled)
        
        # Update instance settings if provided
        if spam_threshold is not None:
            self.spam_threshold = spam_threshold
        
        if spam_interval is not None:
            self.spam_interval = spam_interval
        
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        
        embed = discord.Embed(
            title="AutoMod Configuration",
            color=0x5865F2
        )
        embed.add_field(
            name="Status", 
            value="✅ Enabled" if settings.get('automod_enabled', True) else "❌ Disabled", 
            inline=False
        )
        embed.add_field(name="Spam Threshold", value=f"{self.spam_threshold} messages", inline=True)
        embed.add_field(name="Spam Interval", value=f"{self.spam_interval} seconds", inline=True)
        
        embed.add_field(
            name="Monitored Violations",
            value="• Spam detection\n• Excessive mentions (>5)\n• Excessive links (>3)\n• Discord invites\n• Blocked words\n• Excessive caps (>70%)",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name="automod_stats", description="View AutoMod statistics")
    async def automod_stats(self, interaction: discord.Interaction):
        """View AutoMod statistics"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to view AutoMod stats.", ephemeral=True)
            return
        
        # This would require additional database queries to get proper stats
        # For now, show basic info
        embed = discord.Embed(
            title="AutoMod Statistics",
            description="AutoMod activity for this server",
            color=0x5865F2
        )
        
        # Count current violations in memory
        current_violations = sum(
            count for key, count in self.violation_tracker.items() 
            if key.startswith(f"{interaction.guild.id}_")
        )
        
        embed.add_field(name="Active Violations (Session)", value=str(current_violations), inline=True)
        embed.add_field(name="Monitored Users", value=str(len([k for k in self.violation_tracker.keys() if k.startswith(f"{interaction.guild.id}_")])), inline=True)
        
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        status = "✅ Enabled" if settings.get('automod_enabled', True) else "❌ Disabled"
        embed.add_field(name="Status", value=status, inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name="automod_reset", description="Reset violation count for a user")
    @discord.app_commands.describe(member="The member to reset violations for")
    async def automod_reset(self, interaction: discord.Interaction, member: discord.Member):
        """Reset AutoMod violation count for a user"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to reset violations.", ephemeral=True)
            return
        
        key = f"{interaction.guild.id}_{member.id}"
        old_count = self.violation_tracker.get(key, 0)
        self.violation_tracker[key] = 0
        
        embed = discord.Embed(
            title="Violations Reset",
            description=f"Reset violation count for **{member}**",
            color=0x57F287
        )
        embed.add_field(name="Previous Count", value=str(old_count), inline=True)
        embed.add_field(name="New Count", value="0", inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Starboard(commands.Cog):
    """Starboard system for highlighting popular messages"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle star reactions"""
        await self._handle_star_reaction(payload, added=True)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle star reaction removal"""
        await self._handle_star_reaction(payload, added=False)
    
    async def _handle_star_reaction(self, payload, added: bool):
        """Handle star reactions (add/remove)"""
        # Only handle star emoji
        if str(payload.emoji) != '⭐':
            return
        
        if not payload.guild_id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        # Get guild settings
        settings = await self.bot.db.get_guild_settings(payload.guild_id)
        if not settings or not settings.get('starboard_channel_id'):
            return
        
        starboard_channel = guild.get_channel(settings['starboard_channel_id'])
        if not starboard_channel:
            return
        
        # Don't star messages in the starboard channel itself
        channel = guild.get_channel(payload.channel_id)
        if channel == starboard_channel:
            return
        
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden):
            return
        
        # Don't star bot messages
        if message.author.bot:
            return
        
        # Count star reactions
        star_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == '⭐':
                star_count = reaction.count
                break
        
        threshold = settings.get('starboard_threshold', 3)
        
        # Check if entry already exists
        existing_entry = await self.bot.db.get_starboard_entry(payload.message_id)
        
        if star_count >= threshold:
            if existing_entry:
                # Update existing entry
                await self._update_starboard_message(existing_entry, message, star_count, starboard_channel)
            else:
                # Create new starboard entry
                await self._create_starboard_message(message, star_count, starboard_channel)
        
        elif existing_entry and star_count < threshold:
            # Remove from starboard if below threshold
            await self._remove_starboard_message(existing_entry, starboard_channel)
    
    async def _create_starboard_message(self, message: discord.Message, star_count: int, starboard_channel: discord.TextChannel):
        """Create a new starboard message"""
        embed = discord.Embed(
            description=message.content or "*No text content*",
            color=0xFFD700,
            timestamp=message.created_at
        )
        
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )
        
        embed.add_field(
            name="Source",
            value=f"[Jump to message]({message.jump_url})",
            inline=False
        )
        
        # Add image if present
        if message.attachments:
            attachment = message.attachments[0]
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                embed.set_image(url=attachment.url)
        
        # Add embed image if present
        if message.embeds:
            for embed_obj in message.embeds:
                if embed_obj.image:
                    embed.set_image(url=embed_obj.image.url)
                    break
        
        embed.set_footer(
            text=f"#{message.channel.name} • {message.id}",
            icon_url=message.guild.icon.url if message.guild.icon else None
        )
        
        content = f"⭐ **{star_count}** {message.channel.mention}"
        
        try:
            starboard_message = await starboard_channel.send(content=content, embed=embed)
            
            # Add to database
            await self.bot.db.add_starboard_entry(
                message.guild.id,
                message.id,
                message.channel.id,
                message.author.id
            )
            
            # Update with starboard message ID
            await self.bot.db.conn.execute(
                'UPDATE starboard_entries SET starboard_message_id = ?, star_count = ? WHERE original_message_id = ?',
                (starboard_message.id, star_count, message.id)
            )
            await self.bot.db.conn.commit()
            
        except discord.Forbidden:
            pass  # No permission to send messages
        except Exception as e:
            print(f"Error creating starboard message: {e}")
    
    async def _update_starboard_message(self, entry: dict, message: discord.Message, star_count: int, starboard_channel: discord.TextChannel):
        """Update existing starboard message"""
        if not entry.get('starboard_message_id'):
            return
        
        try:
            starboard_message = await starboard_channel.fetch_message(entry['starboard_message_id'])
            
            # Update content
            content = f"⭐ **{star_count}** {message.channel.mention}"
            
            await starboard_message.edit(content=content)
            
            # Update database
            await self.bot.db.update_star_count(message.id, star_count)
            
        except discord.NotFound:
            # Starboard message was deleted, create new one
            await self._create_starboard_message(message, star_count, starboard_channel)
        except Exception as e:
            print(f"Error updating starboard message: {e}")
    
    async def _remove_starboard_message(self, entry: dict, starboard_channel: discord.TextChannel):
        """Remove message from starboard"""
        if not entry.get('starboard_message_id'):
            return
        
        try:
            starboard_message = await starboard_channel.fetch_message(entry['starboard_message_id'])
            await starboard_message.delete()
        except discord.NotFound:
            pass  # Already deleted
        except Exception as e:
            print(f"Error removing starboard message: {e}")
        
        # Remove from database
        await self.bot.db.conn.execute(
            'DELETE FROM starboard_entries WHERE original_message_id = ?',
            (entry['original_message_id'],)
        )
        await self.bot.db.conn.commit()
    
    @app_commands.command(name="starboard", description="Configure starboard settings")
    @app_commands.describe(
        channel="Channel for starboard messages",
        threshold="Number of stars required (default: 3)"
    )
    async def starboard_config(self, interaction: discord.Interaction, 
                              channel: Optional[discord.TextChannel] = None,
                              threshold: Optional[int] = None):
        """Configure starboard settings"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to configure the starboard.", ephemeral=True)
            return
        
        if channel:
            if not channel.permissions_for(interaction.guild.me).send_messages:
                await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
                return
            
            await self.bot.db.update_guild_setting(interaction.guild.id, 'starboard_channel_id', channel.id)
        
        if threshold is not None:
            if threshold < 1 or threshold > 50:
                await interaction.response.send_message("❌ Threshold must be between 1 and 50.", ephemeral=True)
                return
            
            await self.bot.db.update_guild_setting(interaction.guild.id, 'starboard_threshold', threshold)
        
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        
        embed = discord.Embed(
            title="Starboard Configuration",
            color=0xFFD700
        )
        
        if settings.get('starboard_channel_id'):
            starboard_channel = interaction.guild.get_channel(settings['starboard_channel_id'])
            embed.add_field(
                name="Channel", 
                value=starboard_channel.mention if starboard_channel else "Not found",
                inline=False
            )
        else:
            embed.add_field(name="Channel", value="Not configured", inline=False)
        
        embed.add_field(
            name="Threshold", 
            value=f"{settings.get('starboard_threshold', 3)} ⭐",
            inline=False
        )
        
        embed.add_field(
            name="How it works",
            value="React with ⭐ to messages to add them to the starboard when they reach the threshold!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="starboard_disable", description="Disable the starboard")
    async def starboard_disable(self, interaction: discord.Interaction):
        """Disable the starboard"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to disable the starboard.", ephemeral=True)
            return
        
        await self.bot.db.update_guild_setting(interaction.guild.id, 'starboard_channel_id', None)
        
        embed = discord.Embed(
            title="Starboard Disabled",
            description="The starboard has been disabled for this server.",
            color=0xED4245
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="starboard_stats", description="View starboard statistics")
    async def starboard_stats(self, interaction: discord.Interaction):
        """View starboard statistics"""
        cursor = await self.bot.db.conn.execute(
            'SELECT COUNT(*), AVG(star_count), MAX(star_count) FROM starboard_entries WHERE guild_id = ?',
            (interaction.guild.id,)
        )
        stats = await cursor.fetchone()
        
        if not stats or stats[0] == 0:
            await interaction.response.send_message("❌ No starboard entries found.", ephemeral=True)
            return
        
        total_entries, avg_stars, max_stars = stats
        
        # Get top starred message
        cursor = await self.bot.db.conn.execute(
            'SELECT original_message_id, author_id, star_count FROM starboard_entries WHERE guild_id = ? ORDER BY star_count DESC LIMIT 1',
            (interaction.guild.id,)
        )
        top_entry = await cursor.fetchone()
        
        embed = discord.Embed(
            title="Starboard Statistics",
            color=0xFFD700
        )
        
        embed.add_field(name="Total Entries", value=str(total_entries), inline=True)
        embed.add_field(name="Average Stars", value=f"{avg_stars:.1f}", inline=True)
        embed.add_field(name="Most Stars", value=str(int(max_stars)), inline=True)
        
        if top_entry:
            author = interaction.guild.get_member(top_entry[1])
            author_name = author.display_name if author else f"<@{top_entry[1]}>"
            embed.add_field(
                name="Top Message", 
                value=f"{top_entry[2]} ⭐ by {author_name}",
                inline=False
            )
        
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        threshold = settings.get('starboard_threshold', 3) if settings else 3
        embed.add_field(name="Current Threshold", value=f"{threshold} ⭐", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="force_star", description="Force add a message to the starboard")
    @app_commands.describe(message_id="ID of the message to star")
    async def force_star(self, interaction: discord.Interaction, message_id: str):
        """Force add a message to the starboard"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to force star messages.", ephemeral=True)
            return
        
        try:
            message_id = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)
            return
        
        # Find the message
        message = None
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                break
            except:
                continue
        
        if not message:
            await interaction.response.send_message("❌ Message not found.", ephemeral=True)
            return
        
        if message.author.bot:
            await interaction.response.send_message("❌ Cannot star bot messages.", ephemeral=True)
            return
        
        # Check if already starred
        existing_entry = await self.bot.db.get_starboard_entry(message_id)
        if existing_entry:
            await interaction.response.send_message("❌ Message is already on the starboard.", ephemeral=True)
            return
        
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        if not settings or not settings.get('starboard_channel_id'):
            await interaction.response.send_message("❌ Starboard is not configured.", ephemeral=True)
            return
        
        starboard_channel = interaction.guild.get_channel(settings['starboard_channel_id'])
        if not starboard_channel:
            await interaction.response.send_message("❌ Starboard channel not found.", ephemeral=True)
            return
        
        # Create starboard entry with force star count
        await self._create_starboard_message(message, 999, starboard_channel)
        
        embed = discord.Embed(
            title="Message Force Starred",
            description=f"Added [message]({message.jump_url}) to the starboard.",
            color=0xFFD700
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Starboard(bot))

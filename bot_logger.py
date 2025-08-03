import discord
from discord.ext import commands
from discord import app_commands
import json
from datetime import datetime

class Logging(commands.Cog):
    """Event logging system"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def send_log(self, guild_id: int, embed: discord.Embed):
        """Send log to the configured log channel"""
        settings = await self.bot.db.get_guild_settings(guild_id)
        if not settings or not settings.get('log_channel_id'):
            return
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        
        log_channel = guild.get_channel(settings['log_channel_id'])
        if not log_channel:
            return
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # No permission to send messages
        except Exception as e:
            print(f"Error sending log: {e}")
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Log message edits"""
        if before.author.bot:
            return
        
        if before.content == after.content:
            return  # No content change
        
        # Add to database
        await self.bot.db.add_event_log(
            before.guild.id,
            'message_edit',
            before.author.id,
            before.channel.id,
            {
                'message_id': before.id,
                'before_content': before.content,
                'after_content': after.content
            }
        )
        
        embed = discord.Embed(
            title="Message Edited",
            color=0xFEE75C
        )
        embed.add_field(name="User", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        
        # Truncate long messages
        before_content = before.content[:1000] + ("..." if len(before.content) > 1000 else "")
        after_content = after.content[:1000] + ("..." if len(after.content) > 1000 else "")
        
        embed.add_field(name="Before", value=f"```{before_content}```", inline=False)
        embed.add_field(name="After", value=f"```{after_content}```", inline=False)
        embed.add_field(name="Message Link", value=f"[Jump to message]({after.jump_url})", inline=False)
        
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(before.guild.id, embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log message deletions"""
        if message.author.bot:
            return
        
        # Add to database
        await self.bot.db.add_event_log(
            message.guild.id,
            'message_delete',
            message.author.id,
            message.channel.id,
            {
                'message_id': message.id,
                'content': message.content,
                'attachments': [att.url for att in message.attachments]
            }
        )
        
        embed = discord.Embed(
            title="Message Deleted",
            color=0xED4245
        )
        embed.add_field(name="User", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        
        # Truncate long messages
        content = message.content[:1500] + ("..." if len(message.content) > 1500 else "")
        if content:
            embed.add_field(name="Content", value=f"```{content}```", inline=False)
        
        if message.attachments:
            attachment_list = "\n".join([att.filename for att in message.attachments])
            embed.add_field(name="Attachments", value=attachment_list, inline=False)
        
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(message.guild.id, embed)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log member joins"""
        # Add to database
        await self.bot.db.add_event_log(
            member.guild.id,
            'member_join',
            member.id,
            None,
            {
                'account_created': member.created_at.isoformat(),
                'avatar_url': str(member.display_avatar.url)
            }
        )
        
        embed = discord.Embed(
            title="Member Joined",
            color=0x57F287
        )
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=False)
        embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=False)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(member.guild.id, embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log member leaves"""
        # Add to database
        await self.bot.db.add_event_log(
            member.guild.id,
            'member_leave',
            member.id,
            None,
            {
                'roles': [role.id for role in member.roles if role.name != '@everyone'],
                'joined_at': member.joined_at.isoformat() if member.joined_at else None
            }
        )
        
        embed = discord.Embed(
            title="Member Left",
            color=0xED4245
        )
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        
        if member.joined_at:
            embed.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=False)
        
        roles = [role.name for role in member.roles if role.name != '@everyone']
        if roles:
            embed.add_field(name="Roles", value=", ".join(roles), inline=False)
        
        embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=False)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(member.guild.id, embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log member updates (nickname, roles)"""
        changes = []
        
        # Check nickname change
        if before.nick != after.nick:
            changes.append(f"Nickname: `{before.nick or 'None'}` → `{after.nick or 'None'}`")
        
        # Check role changes
        if before.roles != after.roles:
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)
            
            if added_roles:
                role_names = [role.name for role in added_roles]
                changes.append(f"Added roles: {', '.join(role_names)}")
            
            if removed_roles:
                role_names = [role.name for role in removed_roles]
                changes.append(f"Removed roles: {', '.join(role_names)}")
        
        if not changes:
            return
        
        # Add to database
        await self.bot.db.add_event_log(
            after.guild.id,
            'member_update',
            after.id,
            None,
            {
                'changes': changes,
                'before_nick': before.nick,
                'after_nick': after.nick,
                'before_roles': [role.id for role in before.roles],
                'after_roles': [role.id for role in after.roles]
            }
        )
        
        embed = discord.Embed(
            title="Member Updated",
            color=0x5865F2
        )
        embed.add_field(name="User", value=f"{after} ({after.id})", inline=False)
        embed.add_field(name="Changes", value="\n".join(changes), inline=False)
        
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(after.guild.id, embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creation"""
        embed = discord.Embed(
            title="Channel Created",
            color=0x57F287
        )
        embed.add_field(name="Channel", value=f"{channel.mention} ({channel.id})", inline=False)
        embed.add_field(name="Type", value=str(channel.type).title(), inline=False)
        
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=False)
        
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(channel.guild.id, embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletion"""
        embed = discord.Embed(
            title="Channel Deleted",
            color=0xED4245
        )
        embed.add_field(name="Channel", value=f"#{channel.name} ({channel.id})", inline=False)
        embed.add_field(name="Type", value=str(channel.type).title(), inline=False)
        
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=False)
        
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(channel.guild.id, embed)
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Log role creation"""
        embed = discord.Embed(
            title="Role Created",
            color=0x57F287
        )
        embed.add_field(name="Role", value=f"{role.mention} ({role.id})", inline=False)
        embed.add_field(name="Color", value=str(role.color), inline=False)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(role.guild.id, embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Log role deletion"""
        embed = discord.Embed(
            title="Role Deleted",
            color=0xED4245
        )
        embed.add_field(name="Role", value=f"{role.name} ({role.id})", inline=False)
        embed.add_field(name="Color", value=str(role.color), inline=False)
        embed.add_field(name="Members", value=str(len(role.members)), inline=False)
        
        embed.timestamp = datetime.utcnow()
        
        await self.send_log(role.guild.id, embed)
    
    @app_commands.command(name="setlogchannel", description="Set the logging channel")
    @app_commands.describe(channel="Channel to send logs to")
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the logging channel"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to set the log channel.", ephemeral=True)
            return
        
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
            return
        
        await self.bot.db.update_guild_setting(interaction.guild.id, 'log_channel_id', channel.id)
        
        embed = discord.Embed(
            title="Log Channel Set",
            description=f"Logs will now be sent to {channel.mention}",
            color=0x57F287
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Send test log
        test_embed = discord.Embed(
            title="✅ Logging Enabled",
            description="This channel has been set as the log channel. Events will be logged here.",
            color=0x57F287
        )
        test_embed.timestamp = datetime.utcnow()
        
        await channel.send(embed=test_embed)
    
    @app_commands.command(name="disablelogging", description="Disable event logging")
    async def disable_logging(self, interaction: discord.Interaction):
        """Disable event logging"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to disable logging.", ephemeral=True)
            return
        
        await self.bot.db.update_guild_setting(interaction.guild.id, 'log_channel_id', None)
        
        embed = discord.Embed(
            title="Logging Disabled",
            description="Event logging has been disabled for this server.",
            color=0xED4245
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))

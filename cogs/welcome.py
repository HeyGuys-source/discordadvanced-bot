import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import re

class Welcome(commands.Cog):
    """Welcome and farewell message system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.variable_pattern = re.compile(r'\{([^}]+)\}')
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when member joins"""
        settings = await self.bot.db.get_guild_settings(member.guild.id)
        if not settings:
            return
        
        welcome_channel_id = settings.get('welcome_channel_id')
        welcome_message = settings.get('welcome_message')
        auto_role_id = settings.get('auto_role_id')
        
        # Assign auto role if configured
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role and role < member.guild.me.top_role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                except discord.Forbidden:
                    pass  # No permission
        
        # Send welcome message if configured
        if welcome_channel_id and welcome_message:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                processed_message = self._process_variables(welcome_message, member)
                
                try:
                    if processed_message.startswith('{embed}') and processed_message.endswith('{/embed}'):
                        # Extract embed content
                        embed_content = processed_message[7:-8]
                        embed = self._create_embed_from_text(embed_content, member)
                        await channel.send(embed=embed)
                    else:
                        await channel.send(processed_message)
                except discord.HTTPException:
                    pass  # Message too long or other error
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send farewell message when member leaves"""
        settings = await self.bot.db.get_guild_settings(member.guild.id)
        if not settings:
            return
        
        welcome_channel_id = settings.get('welcome_channel_id')
        farewell_message = settings.get('farewell_message')
        
        if welcome_channel_id and farewell_message:
            channel = member.guild.get_channel(welcome_channel_id)
            if channel:
                processed_message = self._process_variables(farewell_message, member)
                
                try:
                    if processed_message.startswith('{embed}') and processed_message.endswith('{/embed}'):
                        # Extract embed content
                        embed_content = processed_message[7:-8]
                        embed = self._create_embed_from_text(embed_content, member)
                        await channel.send(embed=embed)
                    else:
                        await channel.send(processed_message)
                except discord.HTTPException:
                    pass  # Message too long or other error
    
    def _process_variables(self, text: str, member: discord.Member) -> str:
        """Process variables in welcome/farewell messages"""
        def replace_variable(match):
            var = match.group(1).lower()
            
            # User variables
            if var == 'user':
                return member.display_name
            elif var == 'user.mention':
                return member.mention
            elif var == 'user.id':
                return str(member.id)
            elif var == 'user.name':
                return member.name
            elif var == 'user.discriminator':
                return member.discriminator
            elif var == 'user.avatar':
                return str(member.display_avatar.url)
            elif var == 'user.created':
                return f"<t:{int(member.created_at.timestamp())}:R>"
            
            # Server variables
            elif var == 'server':
                return member.guild.name
            elif var == 'server.id':
                return str(member.guild.id)
            elif var == 'server.members':
                return str(member.guild.member_count)
            elif var == 'server.icon':
                return str(member.guild.icon.url) if member.guild.icon else ''
            elif var == 'server.owner':
                return member.guild.owner.display_name if member.guild.owner else 'Unknown'
            
            # Member count with ordinal
            elif var == 'server.members.ordinal':
                count = member.guild.member_count
                if count % 10 == 1 and count % 100 != 11:
                    return f"{count}st"
                elif count % 10 == 2 and count % 100 != 12:
                    return f"{count}nd"
                elif count % 10 == 3 and count % 100 != 13:
                    return f"{count}rd"
                else:
                    return f"{count}th"
            
            # Date/time
            elif var == 'date':
                return discord.utils.utcnow().strftime('%Y-%m-%d')
            elif var == 'time':
                return discord.utils.utcnow().strftime('%H:%M:%S')
            
            # Default: return unchanged
            return f"{{{var}}}"
        
        return self.variable_pattern.sub(replace_variable, text)
    
    def _create_embed_from_text(self, content: str, member: discord.Member) -> discord.Embed:
        """Create embed from formatted text"""
        lines = content.strip().split('\n')
        
        title = "Welcome!"
        description = ""
        color = 0x57F287
        
        for line in lines:
            line = line.strip()
            if line.startswith('title:'):
                title = line[6:].strip()
            elif line.startswith('description:'):
                description = line[12:].strip()
            elif line.startswith('color:'):
                try:
                    color = int(line[6:].strip().replace('#', ''), 16)
                except:
                    pass
            else:
                if description:
                    description += "\n" + line
                else:
                    description = line
        
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_thumbnail(url=member.display_avatar.url)
        return embed
    
    @app_commands.command(name="setwelcome", description="Set welcome message and channel")
    @app_commands.describe(
        channel="Channel to send welcome messages",
        message="Welcome message (supports variables and embeds)"
    )
    async def set_welcome(self, interaction: discord.Interaction, 
                         channel: discord.TextChannel, message: str):
        """Set welcome message and channel"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to set welcome messages.", ephemeral=True)
            return
        
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
            return
        
        if len(message) > 2000:
            await interaction.response.send_message("❌ Message must be 2000 characters or less.", ephemeral=True)
            return
        
        await self.bot.db.update_guild_setting(interaction.guild.id, 'welcome_channel_id', channel.id)
        await self.bot.db.update_guild_setting(interaction.guild.id, 'welcome_message', message)
        
        embed = discord.Embed(
            title="Welcome Message Set",
            color=0x57F287
        )
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        embed.add_field(name="Message", value=message[:1000] + ("..." if len(message) > 1000 else ""), inline=False)
        
        await interaction.response.send_message(embed=embed)
        
        # Send test message
        test_message = self._process_variables(message, interaction.user)
        
        try:
            if test_message.startswith('{embed}') and test_message.endswith('{/embed}'):
                embed_content = test_message[7:-8]
                test_embed = self._create_embed_from_text(embed_content, interaction.user)
                test_embed.set_footer(text="This is a test message")
                await channel.send(embed=test_embed)
            else:
                await channel.send(f"**Test Welcome Message:**\n{test_message}")
        except:
            pass
    
    @app_commands.command(name="setfarewell", description="Set farewell message")
    @app_commands.describe(message="Farewell message (supports variables and embeds)")
    async def set_farewell(self, interaction: discord.Interaction, message: str):
        """Set farewell message"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to set farewell messages.", ephemeral=True)
            return
        
        if len(message) > 2000:
            await interaction.response.send_message("❌ Message must be 2000 characters or less.", ephemeral=True)
            return
        
        await self.bot.db.update_guild_setting(interaction.guild.id, 'farewell_message', message)
        
        embed = discord.Embed(
            title="Farewell Message Set",
            description=message[:1000] + ("..." if len(message) > 1000 else ""),
            color=0x57F287
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="setautorole", description="Set role to automatically assign to new members")
    @app_commands.describe(role="Role to automatically assign")
    async def set_auto_role(self, interaction: discord.Interaction, role: discord.Role):
        """Set auto role for new members"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need Manage Roles permission to set auto roles.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ I need Manage Roles permission to assign auto roles.", ephemeral=True)
            return
        
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I can't assign a role that's higher than or equal to my highest role.", ephemeral=True)
            return
        
        await self.bot.db.update_guild_setting(interaction.guild.id, 'auto_role_id', role.id)
        
        embed = discord.Embed(
            title="Auto Role Set",
            description=f"New members will automatically receive the {role.mention} role.",
            color=0x57F287
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="removeautorole", description="Remove auto role assignment")
    async def remove_auto_role(self, interaction: discord.Interaction):
        """Remove auto role assignment"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need Manage Roles permission to remove auto roles.", ephemeral=True)
            return
        
        await self.bot.db.update_guild_setting(interaction.guild.id, 'auto_role_id', None)
        
        embed = discord.Embed(
            title="Auto Role Removed",
            description="Auto role assignment has been disabled.",
            color=0x57F287
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="welcomehelp", description="Show help for welcome message variables")
    async def welcome_help(self, interaction: discord.Interaction):
        """Show welcome message help"""
        embed = discord.Embed(
            title="Welcome Message Variables",
            description="Available variables for welcome and farewell messages:",
            color=0x5865F2
        )
        
        embed.add_field(
            name="User Variables",
            value="`{user}` - User display name\n"
                  "`{user.mention}` - User mention\n"
                  "`{user.id}` - User ID\n"
                  "`{user.name}` - Username\n"
                  "`{user.avatar}` - Avatar URL\n"
                  "`{user.created}` - Account creation time",
            inline=False
        )
        
        embed.add_field(
            name="Server Variables",
            value="`{server}` - Server name\n"
                  "`{server.id}` - Server ID\n"
                  "`{server.members}` - Member count\n"
                  "`{server.members.ordinal}` - Ordinal member count (1st, 2nd, etc.)\n"
                  "`{server.owner}` - Server owner\n"
                  "`{server.icon}` - Server icon URL",
            inline=False
        )
        
        embed.add_field(
            name="Time Variables",
            value="`{date}` - Current date\n"
                  "`{time}` - Current time",
            inline=False
        )
        
        embed.add_field(
            name="Embed Format",
            value="Wrap your message in `{embed}` and `{/embed}` to create an embed:\n"
                  "```{embed}\n"
                  "title: Welcome to the server!\n"
                  "description: Hello {user.mention}!\n"
                  "color: #57F287\n"
                  "{/embed}```",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))

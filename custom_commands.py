import discord
from discord.ext import commands
from discord import app_commands
import re
from typing import Optional

class CustomCommands(commands.Cog):
    """Custom command system with variables and auto-responses"""
    
    def __init__(self, bot):
        self.bot = bot
        self.variable_pattern = re.compile(r'\{([^}]+)\}')
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for custom command triggers"""
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        # Check for custom commands
        content = message.content.lower().strip()
        
        # Remove prefix if present
        settings = await self.bot.db.get_guild_settings(message.guild.id)
        prefix = settings.get('prefix', '!') if settings else '!'
        
        if content.startswith(prefix):
            trigger = content[len(prefix):].strip()
        else:
            trigger = content
        
        # Get custom command
        command = await self.bot.db.get_custom_command(message.guild.id, trigger)
        if command:
            # Increment usage counter
            await self.bot.db.increment_command_usage(command['id'])
            
            # Process response with variables
            response = await self._process_variables(command['response'], message)
            
            # Send response
            try:
                await message.channel.send(response)
            except discord.HTTPException:
                pass  # Message too long or other error
    
    async def _process_variables(self, text: str, message: discord.Message) -> str:
        """Process variables in text"""
        def replace_variable(match):
            var = match.group(1).lower()
            
            # User variables
            if var == 'user':
                return message.author.display_name
            elif var == 'user.mention':
                return message.author.mention
            elif var == 'user.id':
                return str(message.author.id)
            elif var == 'user.name':
                return message.author.name
            elif var == 'user.discriminator':
                return message.author.discriminator
            elif var == 'user.avatar':
                return str(message.author.display_avatar.url)
            
            # Server variables
            elif var == 'server':
                return message.guild.name
            elif var == 'server.id':
                return str(message.guild.id)
            elif var == 'server.members':
                return str(message.guild.member_count)
            elif var == 'server.icon':
                return str(message.guild.icon.url) if message.guild.icon else ''
            elif var == 'server.owner':
                return message.guild.owner.display_name if message.guild.owner else 'Unknown'
            
            # Channel variables
            elif var == 'channel':
                return message.channel.name
            elif var == 'channel.mention':
                return message.channel.mention
            elif var == 'channel.id':
                return str(message.channel.id)
            
            # Time variables
            elif var == 'date':
                return message.created_at.strftime('%Y-%m-%d')
            elif var == 'time':
                return message.created_at.strftime('%H:%M:%S')
            elif var == 'datetime':
                return message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Role variables
            elif var == 'user.roles':
                roles = [role.name for role in message.author.roles if role.name != '@everyone']
                return ', '.join(roles) if roles else 'No roles'
            elif var == 'user.top_role':
                return message.author.top_role.name
            
            # Random variables
            elif var.startswith('random:'):
                try:
                    choices = var.split(':', 1)[1].split('|')
                    import random
                    return random.choice(choices).strip()
                except:
                    return var
            
            # Math variables
            elif var.startswith('math:'):
                try:
                    expression = var.split(':', 1)[1]
                    # Simple math evaluation (be careful with eval!)
                    # In production, use a safer math parser
                    result = eval(expression)
                    return str(result)
                except:
                    return var
            
            # Default: return the variable unchanged
            return f"{{{var}}}"
        
        return self.variable_pattern.sub(replace_variable, text)
    
    @app_commands.command(name="addcommand", description="Add a custom command")
    @app_commands.describe(
        trigger="Trigger word/phrase for the command",
        response="Response text (supports variables)"
    )
    async def add_command(self, interaction: discord.Interaction, trigger: str, response: str):
        """Add a custom command"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to add custom commands.", ephemeral=True)
            return
        
        trigger = trigger.lower().strip()
        
        if len(trigger) < 2:
            await interaction.response.send_message("❌ Trigger must be at least 2 characters long.", ephemeral=True)
            return
        
        if len(response) > 2000:
            await interaction.response.send_message("❌ Response must be 2000 characters or less.", ephemeral=True)
            return
        
        # Check if command already exists
        existing = await self.bot.db.get_custom_command(interaction.guild.id, trigger)
        if existing:
            await interaction.response.send_message("❌ A command with that trigger already exists.", ephemeral=True)
            return
        
        # Add to database
        await self.bot.db.add_custom_command(
            interaction.guild.id,
            trigger,
            response,
            interaction.user.id
        )
        
        embed = discord.Embed(
            title="Custom Command Added",
            color=0x57F287
        )
        embed.add_field(name="Trigger", value=f"`{trigger}`", inline=False)
        embed.add_field(name="Response", value=response[:1000] + ("..." if len(response) > 1000 else ""), inline=False)
        embed.add_field(name="Created by", value=interaction.user.mention, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="removecommand", description="Remove a custom command")
    @app_commands.describe(trigger="Trigger word/phrase of the command to remove")
    async def remove_command(self, interaction: discord.Interaction, trigger: str):
        """Remove a custom command"""
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need Manage Server permission to remove custom commands.", ephemeral=True)
            return
        
        trigger = trigger.lower().strip()
        
        # Check if command exists
        command = await self.bot.db.get_custom_command(interaction.guild.id, trigger)
        if not command:
            await interaction.response.send_message("❌ No command found with that trigger.", ephemeral=True)
            return
        
        # Remove from database
        await self.bot.db.conn.execute(
            'DELETE FROM custom_commands WHERE guild_id = ? AND trigger = ?',
            (interaction.guild.id, trigger)
        )
        await self.bot.db.conn.commit()
        
        embed = discord.Embed(
            title="Custom Command Removed",
            description=f"Removed command with trigger: `{trigger}`",
            color=0x57F287
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="listcommands", description="List all custom commands")
    async def list_commands(self, interaction: discord.Interaction):
        """List all custom commands"""
        cursor = await self.bot.db.conn.execute(
            'SELECT trigger, uses FROM custom_commands WHERE guild_id = ? ORDER BY uses DESC',
            (interaction.guild.id,)
        )
        commands = await cursor.fetchall()
        
        if not commands:
            await interaction.response.send_message("❌ No custom commands found for this server.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Custom Commands",
            description=f"Total commands: {len(commands)}",
            color=0x5865F2
        )
        
        command_list = []
        for trigger, uses in commands[:20]:  # Show first 20 commands
            command_list.append(f"`{trigger}` (used {uses} times)")
        
        embed.add_field(
            name="Commands",
            value="\n".join(command_list),
            inline=False
        )
        
        if len(commands) > 20:
            embed.set_footer(text=f"Showing 20 of {len(commands)} commands")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="command_info", description="Get information about a custom command")
    @app_commands.describe(trigger="Trigger word/phrase of the command")
    async def command_info(self, interaction: discord.Interaction, trigger: str):
        """Get information about a custom command"""
        trigger = trigger.lower().strip()
        
        command = await self.bot.db.get_custom_command(interaction.guild.id, trigger)
        if not command:
            await interaction.response.send_message("❌ No command found with that trigger.", ephemeral=True)
            return
        
        creator = interaction.guild.get_member(command['created_by'])
        creator_name = creator.display_name if creator else f"<@{command['created_by']}>"
        
        embed = discord.Embed(
            title="Command Information",
            color=0x5865F2
        )
        embed.add_field(name="Trigger", value=f"`{command['trigger']}`", inline=False)
        embed.add_field(name="Response", value=command['response'][:1000] + ("..." if len(command['response']) > 1000 else ""), inline=False)
        embed.add_field(name="Created by", value=creator_name, inline=True)
        embed.add_field(name="Uses", value=str(command['uses']), inline=True)
        embed.add_field(name="Created", value=f"<t:{int(command['created_at'].timestamp())}:R>", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="variables", description="Show available variables for custom commands")
    async def variables_help(self, interaction: discord.Interaction):
        """Show available variables for custom commands"""
        embed = discord.Embed(
            title="Custom Command Variables",
            description="Available variables you can use in custom commands:",
            color=0x5865F2
        )
        
        embed.add_field(
            name="User Variables",
            value="`{user}` - User display name\n"
                  "`{user.mention}` - User mention\n"
                  "`{user.id}` - User ID\n"
                  "`{user.name}` - Username\n"
                  "`{user.avatar}` - Avatar URL\n"
                  "`{user.roles}` - User's roles\n"
                  "`{user.top_role}` - Highest role",
            inline=False
        )
        
        embed.add_field(
            name="Server Variables",
            value="`{server}` - Server name\n"
                  "`{server.id}` - Server ID\n"
                  "`{server.members}` - Member count\n"
                  "`{server.owner}` - Server owner\n"
                  "`{server.icon}` - Server icon URL",
            inline=False
        )
        
        embed.add_field(
            name="Channel Variables",
            value="`{channel}` - Channel name\n"
                  "`{channel.mention}` - Channel mention\n"
                  "`{channel.id}` - Channel ID",
            inline=False
        )
        
        embed.add_field(
            name="Time Variables",
            value="`{date}` - Current date\n"
                  "`{time}` - Current time\n"
                  "`{datetime}` - Date and time",
            inline=False
        )
        
        embed.add_field(
            name="Special Variables",
            value="`{random:option1|option2|option3}` - Random choice\n"
                  "`{math:2+2}` - Math expression",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))

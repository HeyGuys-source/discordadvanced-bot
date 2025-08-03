import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class ReactionRoles(commands.Cog):
    """Reaction role system with button support"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reaction add events"""
        if payload.user_id == self.bot.user.id:
            return
        
        # Get reaction role from database
        reaction_role = await self.bot.db.get_reaction_role(payload.message_id, str(payload.emoji))
        if not reaction_role:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        role = guild.get_role(reaction_role['role_id'])
        if not role:
            return
        
        try:
            await member.add_roles(role, reason="Reaction role")
        except discord.Forbidden:
            pass  # Missing permissions
        except Exception as e:
            print(f"Error adding reaction role: {e}")
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle reaction remove events"""
        if payload.user_id == self.bot.user.id:
            return
        
        # Get reaction role from database
        reaction_role = await self.bot.db.get_reaction_role(payload.message_id, str(payload.emoji))
        if not reaction_role:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        role = guild.get_role(reaction_role['role_id'])
        if not role:
            return
        
        try:
            await member.remove_roles(role, reason="Reaction role removed")
        except discord.Forbidden:
            pass  # Missing permissions
        except Exception as e:
            print(f"Error removing reaction role: {e}")
    
    @app_commands.command(name="reactionrole", description="Create a reaction role message")
    @app_commands.describe(
        title="Title of the embed",
        description="Description of the embed",
        channel="Channel to send the message to"
    )
    async def create_reaction_role(self, interaction: discord.Interaction, 
                                  title: str, description: str,
                                  channel: Optional[discord.TextChannel] = None):
        """Create a reaction role message"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need Manage Roles permission to create reaction roles.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ I need Manage Roles permission to create reaction roles.", ephemeral=True)
            return
        
        target_channel = channel or interaction.channel
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x5865F2
        )
        embed.set_footer(text="React with emojis to get roles! Use /add_reaction_role to configure.")
        
        try:
            message = await target_channel.send(embed=embed)
            
            embed = discord.Embed(
                title="Reaction Role Message Created",
                description=f"Message created in {target_channel.mention}",
                color=0x57F287
            )
            embed.add_field(name="Message ID", value=str(message.id), inline=False)
            embed.add_field(name="Next Step", value="Use `/add_reaction_role` to add role-emoji pairs to this message.", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="add_reaction_role", description="Add a role-emoji pair to a reaction role message")
    @app_commands.describe(
        message_id="ID of the reaction role message",
        emoji="Emoji to react with",
        role="Role to assign"
    )
    async def add_reaction_role(self, interaction: discord.Interaction, 
                               message_id: str, emoji: str, role: discord.Role):
        """Add a role-emoji pair to a reaction role message"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need Manage Roles permission to manage reaction roles.", ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ I need Manage Roles permission to manage reaction roles.", ephemeral=True)
            return
        
        # Check if bot can assign this role
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I can't assign a role that's higher than or equal to my highest role.", ephemeral=True)
            return
        
        # Check if user can assign this role
        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("❌ You can't assign a role that's higher than or equal to your highest role.", ephemeral=True)
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
        
        if message.author != interaction.guild.me:
            await interaction.response.send_message("❌ I can only add reaction roles to my own messages.", ephemeral=True)
            return
        
        try:
            # Add reaction to message
            await message.add_reaction(emoji)
            
            # Add to database
            await self.bot.db.add_reaction_role(
                interaction.guild.id,
                message_id,
                message.channel.id,
                role.id,
                str(emoji)
            )
            
            embed = discord.Embed(
                title="Reaction Role Added",
                description=f"Successfully added reaction role configuration.",
                color=0x57F287
            )
            embed.add_field(name="Emoji", value=str(emoji), inline=True)
            embed.add_field(name="Role", value=role.mention, inline=True)
            embed.add_field(name="Message", value=f"[Jump to message]({message.jump_url})", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.HTTPException:
            await interaction.response.send_message("❌ Invalid emoji or unable to add reaction.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="remove_reaction_role", description="Remove a role-emoji pair from a reaction role message")
    @app_commands.describe(
        message_id="ID of the reaction role message",
        emoji="Emoji to remove"
    )
    async def remove_reaction_role(self, interaction: discord.Interaction, 
                                  message_id: str, emoji: str):
        """Remove a role-emoji pair from a reaction role message"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need Manage Roles permission to manage reaction roles.", ephemeral=True)
            return
        
        try:
            message_id = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)
            return
        
        # Check if reaction role exists
        reaction_role = await self.bot.db.get_reaction_role(message_id, str(emoji))
        if not reaction_role:
            await interaction.response.send_message("❌ Reaction role not found.", ephemeral=True)
            return
        
        # Find the message
        message = None
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                break
            except:
                continue
        
        try:
            # Remove reaction from message
            if message:
                await message.clear_reaction(emoji)
            
            # Remove from database
            await self.bot.db.remove_reaction_role(message_id, str(emoji))
            
            embed = discord.Embed(
                title="Reaction Role Removed",
                description=f"Successfully removed reaction role configuration.",
                color=0x57F287
            )
            embed.add_field(name="Emoji", value=str(emoji), inline=True)
            embed.add_field(name="Message ID", value=str(message_id), inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="reaction_role_panel", description="Create a reaction role panel with buttons")
    @app_commands.describe(
        title="Title of the panel",
        description="Description of the panel"
    )
    async def reaction_role_panel(self, interaction: discord.Interaction, 
                                 title: str, description: str):
        """Create a reaction role panel with buttons"""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need Manage Roles permission to create reaction role panels.", ephemeral=True)
            return
        
        # This is a simplified version - in a full implementation,
        # you would create a modal or series of commands to configure roles
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x5865F2
        )
        
        # Example view with buttons (simplified)
        view = ReactionRoleView()
        
        await interaction.response.send_message(embed=embed, view=view)

class ReactionRoleView(discord.ui.View):
    """Button view for reaction roles"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Role 1", style=discord.ButtonStyle.primary, emoji="🔵")
    async def role_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Example role button"""
        await interaction.response.send_message("This is an example button. Configure this with actual roles!", ephemeral=True)
    
    @discord.ui.button(label="Role 2", style=discord.ButtonStyle.secondary, emoji="🟡")
    async def role_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Example role button"""
        await interaction.response.send_message("This is an example button. Configure this with actual roles!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))

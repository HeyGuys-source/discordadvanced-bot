import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging

class PrivateUserInfoCommand(commands.Cog):
    """Private user information command for Discord bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="privateuserinfo", description="Send detailed user information privately via DM")
    @app_commands.describe(user="The user to get information about")
    @commands.cooldown(1, 10, commands.BucketType.user)  # 1 use per 10 seconds per user (longer cooldown for DMs)
    async def privateuserinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        """
        Send comprehensive user information privately via DM
        
        Args:
            interaction: Discord interaction object
            user: Target user (defaults to command invoker if not specified)
        """
        try:
            # Default to command invoker if no user specified
            if user is None:
                user = interaction.user
            
            # Ensure user is a Member object for guild-specific info
            if isinstance(user, discord.User):
                try:
                    user = interaction.guild.get_member(user.id)
                    if user is None:
                        await interaction.response.send_message(
                            "❌ User not found in this server.", 
                            ephemeral=True
                        )
                        return
                except AttributeError:
                    await interaction.response.send_message(
                        "❌ This command can only be used in a server.", 
                        ephemeral=True
                    )
                    return
            
            # First respond to the interaction to acknowledge it
            await interaction.response.send_message(
                f"📬 Sending detailed information about {user.display_name} to your DMs...", 
                ephemeral=True
            )
            
            # Create comprehensive embed with user information
            embed = discord.Embed(
                title=f"🔍 Private User Information - {user.display_name}",
                description=f"Detailed information about {user.mention} from **{interaction.guild.name}**",
                color=user.color if user.color != discord.Color.default() else discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            # Set user avatar as thumbnail
            try:
                embed.set_thumbnail(url=user.display_avatar.url)
            except:
                # Fallback if avatar URL is not accessible
                pass
            
            # Basic user information
            embed.add_field(
                name="👤 Basic Information", 
                value=f"**Username:** {user.name}#{user.discriminator if hasattr(user, 'discriminator') and user.discriminator and user.discriminator != '0' else user.name}\n"
                      f"**Display Name:** {user.display_name}\n"
                      f"**User ID:** {user.id}\n"
                      f"**Mention:** {user.mention}",
                inline=False
            )
            
            # Account timestamps
            account_age = (datetime.utcnow() - user.created_at).days
            timestamp_info = f"**Account Created:** {user.created_at.strftime('%B %d, %Y at %I:%M %p UTC')}\n" \
                           f"**Account Age:** {account_age} days old\n"
            
            if user.joined_at:
                join_age = (datetime.utcnow() - user.joined_at).days
                timestamp_info += f"**Joined Server:** {user.joined_at.strftime('%B %d, %Y at %I:%M %p UTC')}\n" \
                                f"**Member For:** {join_age} days"
            
            embed.add_field(
                name="📅 Timeline Information",
                value=timestamp_info,
                inline=False
            )
            
            # Status and presence information
            status_emojis = {
                discord.Status.online: "🟢 Online",
                discord.Status.idle: "🟡 Idle",
                discord.Status.dnd: "🔴 Do Not Disturb",
                discord.Status.offline: "⚫ Offline"
            }
            
            presence_info = f"**Status:** {status_emojis.get(user.status, '❓ Unknown')}\n"
            
            # Desktop/Mobile/Web status
            if hasattr(user, 'desktop_status') and user.desktop_status != discord.Status.offline:
                presence_info += f"**Desktop:** {status_emojis.get(user.desktop_status, '❓')}\n"
            if hasattr(user, 'mobile_status') and user.mobile_status != discord.Status.offline:
                presence_info += f"**Mobile:** {status_emojis.get(user.mobile_status, '❓')}\n"
            if hasattr(user, 'web_status') and user.web_status != discord.Status.offline:
                presence_info += f"**Web:** {status_emojis.get(user.web_status, '❓')}\n"
            
            # Current activity
            if hasattr(user, 'activity') and user.activity:
                activity_type = {
                    discord.ActivityType.playing: "🎮 Playing",
                    discord.ActivityType.streaming: "📺 Streaming",
                    discord.ActivityType.listening: "🎵 Listening to",
                    discord.ActivityType.watching: "👀 Watching",
                    discord.ActivityType.custom: "💭 Custom Status",
                    discord.ActivityType.competing: "🏆 Competing in"
                }
                activity_name = getattr(user.activity, 'name', 'Unknown Activity')
                presence_info += f"**Activity:** {activity_type.get(user.activity.type, '❓')} {activity_name}\n"
                
                # Additional activity details
                if hasattr(user.activity, 'details') and user.activity.details:
                    presence_info += f"**Details:** {user.activity.details}\n"
                if hasattr(user.activity, 'state') and user.activity.state:
                    presence_info += f"**State:** {user.activity.state}\n"
            
            embed.add_field(
                name="📡 Presence Information",
                value=presence_info.strip(),
                inline=False
            )
            
            # Roles information (more detailed)
            if len(user.roles) > 1:  # Exclude @everyone role
                roles = user.roles[1:]  # Skip @everyone
                roles.reverse()  # Show highest roles first
                
                role_info = f"**Total Roles:** {len(roles)}\n"
                role_info += f"**Highest Role:** {roles[0].mention} (Position: {roles[0].position})\n"
                role_info += f"**Role Color:** {str(user.color)}\n\n"
                
                # List all roles with positions
                role_list = []
                for role in roles[:15]:  # Limit to prevent embed size issues
                    role_list.append(f"{role.mention} (pos: {role.position})")
                
                role_info += "**Roles:**\n" + "\n".join(role_list)
                
                if len(roles) > 15:
                    role_info += f"\n... and {len(roles) - 15} more roles"
                
                embed.add_field(
                    name=f"🎭 Server Roles ({len(roles)})",
                    value=role_info,
                    inline=False
                )
            
            # Detailed permissions
            if user.guild_permissions:
                admin_perms = []
                mod_perms = []
                general_perms = []
                
                # Categorize permissions
                perm_categories = {
                    'admin': [
                        ("Administrator", user.guild_permissions.administrator),
                        ("Manage Server", user.guild_permissions.manage_guild),
                        ("Manage Roles", user.guild_permissions.manage_roles),
                        ("Manage Channels", user.guild_permissions.manage_channels),
                    ],
                    'moderation': [
                        ("Kick Members", user.guild_permissions.kick_members),
                        ("Ban Members", user.guild_permissions.ban_members),
                        ("Manage Messages", user.guild_permissions.manage_messages),
                        ("Manage Nicknames", user.guild_permissions.manage_nicknames),
                        ("Mute Members", user.guild_permissions.mute_members),
                        ("Deafen Members", user.guild_permissions.deafen_members),
                        ("Move Members", user.guild_permissions.move_members),
                    ],
                    'general': [
                        ("View Channels", user.guild_permissions.view_channel),
                        ("Send Messages", user.guild_permissions.send_messages),
                        ("Send TTS Messages", user.guild_permissions.send_tts_messages),
                        ("Embed Links", user.guild_permissions.embed_links),
                        ("Attach Files", user.guild_permissions.attach_files),
                        ("Add Reactions", user.guild_permissions.add_reactions),
                        ("Use External Emojis", user.guild_permissions.external_emojis),
                        ("Connect to Voice", user.guild_permissions.connect),
                        ("Speak in Voice", user.guild_permissions.speak),
                        ("Use Voice Activity", user.guild_permissions.use_voice_activation),
                    ]
                }
                
                for category, perms in perm_categories.items():
                    for perm_name, has_perm in perms:
                        if has_perm:
                            if category == 'admin':
                                admin_perms.append(perm_name)
                            elif category == 'moderation':
                                mod_perms.append(perm_name)
                            else:
                                general_perms.append(perm_name)
                
                perm_text = ""
                if admin_perms:
                    perm_text += f"**🔴 Administrative:** {', '.join(admin_perms)}\n"
                if mod_perms:
                    perm_text += f"**🟡 Moderation:** {', '.join(mod_perms[:5])}\n"
                if general_perms:
                    perm_text += f"**🟢 General:** {', '.join(general_perms[:8])}\n"
                
                if perm_text:
                    embed.add_field(
                        name="🔑 Key Permissions",
                        value=perm_text.strip(),
                        inline=False
                    )
            
            # User flags (badges) with descriptions
            if user.public_flags:
                flags = []
                flag_descriptions = {
                    "staff": "🏢 **Discord Staff** - Discord employee",
                    "partner": "🤝 **Discord Partner** - Partnered server owner",
                    "hypesquad": "🎉 **HypeSquad Events** - HypeSquad events coordinator",
                    "bug_hunter": "🐛 **Bug Hunter** - Helped find bugs in Discord",
                    "hypesquad_bravery": "💪 **HypeSquad Bravery** - Member of House Bravery",
                    "hypesquad_brilliance": "💎 **HypeSquad Brilliance** - Member of House Brilliance",
                    "hypesquad_balance": "⚖️ **HypeSquad Balance** - Member of House Balance",
                    "early_supporter": "⭐ **Early Supporter** - Supported Discord before Nitro",
                    "verified_bot_developer": "🔧 **Verified Bot Developer** - Developer of a verified bot",
                    "discord_certified_moderator": "🛡️ **Discord Certified Moderator** - Completed moderator academy",
                    "bot_http_interactions": "🤖 **Bot HTTP Interactions** - Bot uses HTTP interactions",
                    "active_developer": "💻 **Active Developer** - Currently developing Discord applications"
                }
                
                for flag in user.public_flags:
                    flag_name = flag.name.lower()
                    if flag_name in flag_descriptions:
                        flags.append(flag_descriptions[flag_name])
                
                if flags:
                    embed.add_field(
                        name="🏅 Discord Badges",
                        value="\n".join(flags),
                        inline=False
                    )
            
            # Avatar information
            avatar_info = f"**Current Avatar:** [View Full Size]({user.display_avatar.url})\n"
            if user.avatar and user.guild_avatar:
                avatar_info += f"**Server Avatar:** [View Full Size]({user.guild_avatar.url})\n"
                avatar_info += f"**Global Avatar:** [View Full Size]({user.avatar.url})"
            elif user.avatar:
                avatar_info += f"**Avatar Type:** Custom Avatar"
            else:
                avatar_info += f"**Avatar Type:** Default Avatar"
            
            embed.add_field(
                name="🖼️ Avatar Information",
                value=avatar_info,
                inline=False
            )
            
            # Footer with additional info
            embed.set_footer(
                text=f"Private info requested by {interaction.user.display_name} from {interaction.guild.name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Try to send DM
            try:
                await interaction.user.send(embed=embed)
                
                # Send follow-up confirmation
                follow_embed = discord.Embed(
                    title="✅ Information Sent",
                    description=f"Detailed information about {user.display_name} has been sent to your DMs.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=follow_embed, ephemeral=True)
                
            except discord.Forbidden:
                # User has DMs disabled
                error_embed = discord.Embed(
                    title="❌ Cannot Send DM",
                    description="I couldn't send you a DM. Please check your privacy settings and make sure DMs from server members are enabled.",
                    color=discord.Color.red()
                )
                error_embed.add_field(
                    name="How to enable DMs:",
                    value="1. Go to Server Settings\n2. Privacy & Safety\n3. Enable 'Allow direct messages from server members'",
                    inline=False
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                
        except discord.HTTPException as e:
            self.logger.error(f"HTTP Exception in privateuserinfo command: {e}")
            await interaction.followup.send(
                "❌ Failed to send user information due to Discord API error.", 
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in privateuserinfo command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An unexpected error occurred while fetching user information.", 
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An unexpected error occurred while fetching user information.", 
                        ephemeral=True
                    )
            except:
                pass
    
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle command errors"""
        if isinstance(error, app_commands.CommandOnCooldown):
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"⏰ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⏰ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
            except:
                pass
        else:
            self.logger.error(f"Command error: {error}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred while executing the command.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An error occurred while executing the command.",
                        ephemeral=True
                    )
            except:
                pass

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(PrivateUserInfoCommand(bot))

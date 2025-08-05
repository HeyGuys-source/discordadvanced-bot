import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging

class UserInfoCommand(commands.Cog):
    """Public user information command for Discord bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="userinfo", description="Display detailed information about a user publicly")
    @app_commands.describe(user="The user to get information about")
    @commands.cooldown(1, 5, commands.BucketType.user)  # 1 use per 5 seconds per user
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        """
        Display comprehensive user information publicly in the channel
        
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
            
            # Create embed with user information
            embed = discord.Embed(
                title=f"📋 User Information - {user.display_name}",
                color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # Set user avatar as thumbnail
            try:
                embed.set_thumbnail(url=user.display_avatar.url)
            except:
                # Fallback if avatar URL is not accessible
                pass
            
            # Basic user information
            username = f"{user.name}#{user.discriminator}" if hasattr(user, 'discriminator') and user.discriminator and user.discriminator != "0" else user.name
            embed.add_field(
                name="👤 Username", 
                value=username, 
                inline=True
            )
            embed.add_field(name="🆔 User ID", value=user.id, inline=True)
            embed.add_field(name="📝 Display Name", value=user.display_name, inline=True)
            
            # Account creation date
            account_age = (datetime.utcnow() - user.created_at).days
            embed.add_field(
                name="📅 Account Created",
                value=f"{user.created_at.strftime('%B %d, %Y')}\n({account_age} days ago)",
                inline=True
            )
            
            # Server join date
            if user.joined_at:
                join_age = (datetime.utcnow() - user.joined_at).days
                embed.add_field(
                    name="📥 Joined Server",
                    value=f"{user.joined_at.strftime('%B %d, %Y')}\n({join_age} days ago)",
                    inline=True
                )
            
            # User status and activity
            status_emojis = {
                discord.Status.online: "🟢 Online",
                discord.Status.idle: "🟡 Idle",
                discord.Status.dnd: "🔴 Do Not Disturb",
                discord.Status.offline: "⚫ Offline"
            }
            embed.add_field(
                name="📡 Status",
                value=status_emojis.get(user.status, "❓ Unknown"),
                inline=True
            )
            
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
                activity_text = f"{activity_type.get(user.activity.type, '❓')} {activity_name}"
                embed.add_field(name="🎯 Activity", value=activity_text, inline=True)
            
            # Roles information
            if len(user.roles) > 1:  # Exclude @everyone role
                roles = [role.mention for role in reversed(user.roles[1:])]  # Skip @everyone and reverse for hierarchy
                roles_text = ", ".join(roles[:10])  # Limit to prevent embed size issues
                if len(user.roles) > 11:
                    roles_text += f" ... and {len(user.roles) - 11} more"
                
                embed.add_field(
                    name=f"🎭 Roles ({len(user.roles) - 1})",
                    value=roles_text,
                    inline=False
                )
            
            # User permissions (top permissions only)
            if user.guild_permissions:
                important_perms = []
                perm_checks = [
                    ("Administrator", user.guild_permissions.administrator),
                    ("Manage Server", user.guild_permissions.manage_guild),
                    ("Manage Roles", user.guild_permissions.manage_roles),
                    ("Manage Channels", user.guild_permissions.manage_channels),
                    ("Kick Members", user.guild_permissions.kick_members),
                    ("Ban Members", user.guild_permissions.ban_members),
                    ("Manage Messages", user.guild_permissions.manage_messages)
                ]
                
                for perm_name, has_perm in perm_checks:
                    if has_perm:
                        important_perms.append(perm_name)
                
                if important_perms:
                    embed.add_field(
                        name="🔑 Key Permissions",
                        value=", ".join(important_perms[:5]),  # Limit to prevent embed size issues
                        inline=False
                    )
            
            # User flags (badges)
            if user.public_flags:
                flags = []
                flag_emojis = {
                    "staff": "🏢 Discord Staff",
                    "partner": "🤝 Discord Partner",
                    "hypesquad": "🎉 HypeSquad Events",
                    "bug_hunter": "🐛 Bug Hunter",
                    "hypesquad_bravery": "💪 HypeSquad Bravery",
                    "hypesquad_brilliance": "💎 HypeSquad Brilliance",
                    "hypesquad_balance": "⚖️ HypeSquad Balance",
                    "early_supporter": "⭐ Early Supporter",
                    "verified_bot_developer": "🔧 Verified Bot Developer",
                    "discord_certified_moderator": "🛡️ Discord Certified Moderator",
                    "bot_http_interactions": "🤖 Bot HTTP Interactions",
                    "active_developer": "💻 Active Developer"
                }
                
                for flag in user.public_flags:
                    flag_name = flag.name.lower()
                    if flag_name in flag_emojis:
                        flags.append(flag_emojis[flag_name])
                
                if flags:
                    embed.add_field(
                        name="🏅 Badges",
                        value="\n".join(flags),
                        inline=False
                    )
            
            # Footer with additional info
            embed.set_footer(
                text=f"Requested by {interaction.user.display_name} • User Info Command",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
        except discord.HTTPException as e:
            self.logger.error(f"HTTP Exception in userinfo command: {e}")
            await interaction.response.send_message(
                "❌ Failed to send user information due to Discord API error.", 
                ephemeral=True
            )
        except Exception as e:
            import traceback
            self.logger.error(f"Unexpected error in userinfo command: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
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
    await bot.add_cog(UserInfoCommand(bot))

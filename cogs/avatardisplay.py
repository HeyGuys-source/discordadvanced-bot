import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging

class AvatarDisplayCommand(commands.Cog):
    """Avatar display command for Discord bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="avatardisplay", description="Display a user's avatar and profile information")
    @app_commands.describe(user="The user whose avatar you want to display")
    @commands.cooldown(1, 3, commands.BucketType.user)  # 1 use per 3 seconds per user
    async def avatardisplay(self, interaction: discord.Interaction, user: discord.Member = None):
        """
        Display user's avatar and basic profile information
        
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
                    # Command used in DM, continue with User object
                    pass
            
            # Create embed with avatar information
            embed = discord.Embed(
                title=f"🖼️ {user.display_name}'s Avatar",
                color=user.color if hasattr(user, 'color') and user.color != discord.Color.default() else discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            # Set the main avatar as the large image
            embed.set_image(url=user.display_avatar.url)
            
            # Basic user information
            embed.add_field(
                name="👤 User",
                value=f"{user.name}#{user.discriminator}" if user.discriminator != "0" else user.name,
                inline=True
            )
            embed.add_field(name="🆔 User ID", value=user.id, inline=True)
            
            # Bot indicator
            if user.bot:
                embed.add_field(name="🤖 Type", value="Bot Account", inline=True)
            else:
                embed.add_field(name="👤 Type", value="User Account", inline=True)
            
            # Avatar information section
            avatar_info = []
            
            # Check for different types of avatars
            if hasattr(user, 'guild_avatar') and user.guild_avatar:
                # User has a server-specific avatar
                avatar_info.append(f"**Current Avatar:** Server Avatar")
                avatar_info.append(f"**Server Avatar:** [View Full Size]({user.guild_avatar.url})")
                
                if user.avatar:
                    avatar_info.append(f"**Global Avatar:** [View Full Size]({user.avatar.url})")
                    embed.set_thumbnail(url=user.avatar.url)
            elif user.avatar:
                # User has a custom global avatar
                avatar_info.append(f"**Avatar Type:** Custom Avatar")
                avatar_info.append(f"**Avatar URL:** [View Full Size]({user.avatar.url})")
            else:
                # User is using default avatar
                avatar_info.append(f"**Avatar Type:** Default Discord Avatar")
                avatar_info.append(f"**Default Avatar:** [View Full Size]({user.default_avatar.url})")
            
            # Avatar formats available
            if user.avatar:
                formats = []
                base_url = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}"
                
                # Check for animated avatar
                if user.avatar.is_animated():
                    formats.append(f"[GIF]({base_url}.gif?size=1024)")
                    avatar_info.append("**Animated:** Yes 🎭")
                else:
                    avatar_info.append("**Animated:** No")
                
                formats.extend([
                    f"[PNG]({base_url}.png?size=1024)",
                    f"[JPEG]({base_url}.jpg?size=1024)",
                    f"[WebP]({base_url}.webp?size=1024)"
                ])
                
                avatar_info.append(f"**Available Formats:** {' • '.join(formats)}")
            
            embed.add_field(
                name="🎨 Avatar Details",
                value="\n".join(avatar_info),
                inline=False
            )
            
            # Additional user context if in a guild
            if hasattr(user, 'joined_at') and user.joined_at:
                # User status and activity
                status_emojis = {
                    discord.Status.online: "🟢 Online",
                    discord.Status.idle: "🟡 Idle", 
                    discord.Status.dnd: "🔴 Do Not Disturb",
                    discord.Status.offline: "⚫ Offline"
                }
                
                context_info = []
                context_info.append(f"**Status:** {status_emojis.get(user.status, '❓ Unknown')}")
                
                if user.activity:
                    activity_type = {
                        discord.ActivityType.playing: "🎮 Playing",
                        discord.ActivityType.streaming: "📺 Streaming",
                        discord.ActivityType.listening: "🎵 Listening to",
                        discord.ActivityType.watching: "👀 Watching",
                        discord.ActivityType.custom: "💭 Custom Status",
                        discord.ActivityType.competing: "🏆 Competing in"
                    }
                    context_info.append(f"**Activity:** {activity_type.get(user.activity.type, '❓')} {user.activity.name}")
                
                # Highest role color
                if user.top_role and user.top_role.color != discord.Color.default():
                    context_info.append(f"**Role Color:** {str(user.top_role.color)} ({user.top_role.name})")
                
                embed.add_field(
                    name="📊 User Context",
                    value="\n".join(context_info),
                    inline=False
                )
            
            # Avatar creation/upload date (if available)
            if user.avatar:
                # Calculate approximate upload date from avatar hash (Discord Snowflake)
                try:
                    avatar_id = int(user.avatar.key, 16) if hasattr(user.avatar, 'key') else None
                    if avatar_id:
                        # This is an approximation - Discord doesn't provide exact upload dates
                        embed.add_field(
                            name="🕒 Avatar Hash",
                            value=f"`{user.avatar}`",
                            inline=True
                        )
                except:
                    pass
            
            # Account creation date
            account_age = (datetime.utcnow() - user.created_at).days
            embed.add_field(
                name="📅 Account Created",
                value=f"{user.created_at.strftime('%B %d, %Y')}\n({account_age} days ago)",
                inline=True
            )
            
            # Server join date (if applicable)
            if hasattr(user, 'joined_at') and user.joined_at:
                join_age = (datetime.utcnow() - user.joined_at).days
                embed.add_field(
                    name="📥 Joined Server",
                    value=f"{user.joined_at.strftime('%B %d, %Y')}\n({join_age} days ago)",
                    inline=True
                )
            
            # Footer
            embed.set_footer(
                text=f"Avatar requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
        except discord.HTTPException as e:
            self.logger.error(f"HTTP Exception in avatardisplay command: {e}")
            await interaction.response.send_message(
                "❌ Failed to display avatar due to Discord API error.",
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in avatardisplay command: {e}")
            await interaction.response.send_message(
                "❌ An unexpected error occurred while fetching avatar information.",
                ephemeral=True
            )
    
    @avatardisplay.error
    async def avatardisplay_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle command errors"""
        if isinstance(error, commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏰ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                ephemeral=True
            )
        else:
            self.logger.error(f"Command error: {error}")
            await interaction.response.send_message(
                "❌ An error occurred while executing the command.",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(AvatarDisplayCommand(bot))
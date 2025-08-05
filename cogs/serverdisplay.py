import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging

class ServerDisplayCommand(commands.Cog):
    """Server display command for Discord bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="serverdisplay", description="Display the server's icon and information")
    @commands.cooldown(1, 3, commands.BucketType.guild)  # 1 use per 3 seconds per guild
    async def serverdisplay(self, interaction: discord.Interaction):
        """
        Display server icon and basic server information
        
        Args:
            interaction: Discord interaction object
        """
        try:
            # Ensure command is used in a guild
            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ This command can only be used in a server.",
                    ephemeral=True
                )
                return
            
            guild = interaction.guild
            
            # Create embed with server information
            embed = discord.Embed(
                title=f"🏠 {guild.name}",
                description=f"Server information and icon display",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # Server icon
            if guild.icon:
                try:
                    embed.set_image(url=guild.icon.url)
                    embed.add_field(
                        name="🖼️ Server Icon",
                        value=f"[View Full Size]({guild.icon.url})",
                        inline=True
                    )
                except:
                    embed.add_field(
                        name="🖼️ Server Icon",
                        value="Icon present but URL not accessible",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="🖼️ Server Icon",
                    value="No custom icon set",
                    inline=True
                )
            
            # Basic server info
            embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
            embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
            
            # Server creation date
            creation_age = (datetime.utcnow() - guild.created_at).days
            embed.add_field(
                name="📅 Created",
                value=f"{guild.created_at.strftime('%B %d, %Y')}\n({creation_age} days ago)",
                inline=True
            )
            
            # Member count
            embed.add_field(
                name="👥 Members",
                value=f"{guild.member_count:,}" if guild.member_count else "Unknown",
                inline=True
            )
            
            # Channel counts
            text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
            voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
            embed.add_field(
                name="📝 Channels",
                value=f"Text: {text_channels}\nVoice: {voice_channels}",
                inline=True
            )
            
            # Role count
            embed.add_field(
                name="🎭 Roles",
                value=f"{len(guild.roles):,}",
                inline=True
            )
            
            # Boost information
            if guild.premium_tier > 0:
                embed.add_field(
                    name="⭐ Boost Level",
                    value=f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts",
                    inline=True
                )
            
            # Server features
            if guild.features:
                feature_emojis = {
                    "COMMUNITY": "🏘️ Community",
                    "VERIFIED": "✅ Verified",
                    "PARTNERED": "🤝 Partnered",
                    "VANITY_URL": "🔗 Vanity URL",
                    "BANNER": "🎨 Banner",
                    "ANIMATED_ICON": "🎭 Animated Icon",
                    "INVITE_SPLASH": "🌊 Invite Splash",
                    "DISCOVERABLE": "🔍 Discoverable",
                    "COMMERCE": "💰 Commerce",
                    "NEWS": "📰 News Channels",
                    "THREADS_ENABLED": "🧵 Threads",
                    "PRIVATE_THREADS": "🔒 Private Threads"
                }
                
                features = []
                for feature in guild.features[:8]:  # Limit to prevent embed size issues
                    if feature in feature_emojis:
                        features.append(feature_emojis[feature])
                    else:
                        features.append(feature.replace('_', ' ').title())
                
                if features:
                    embed.add_field(
                        name="✨ Features",
                        value="\n".join(features),
                        inline=False
                    )
            
            # Server banner
            if guild.banner:
                embed.add_field(
                    name="🎨 Server Banner",
                    value=f"[View Banner]({guild.banner.url})",
                    inline=True
                )
            
            # Server splash
            if guild.splash:
                embed.add_field(
                    name="🌊 Invite Splash",
                    value=f"[View Splash]({guild.splash.url})",
                    inline=True
                )
            
            # Footer
            embed.set_footer(
                text=f"Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
        except discord.HTTPException as e:
            self.logger.error(f"HTTP Exception in serverdisplay command: {e}")
            await interaction.response.send_message(
                "❌ Failed to display server information due to Discord API error.",
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in serverdisplay command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An unexpected error occurred while fetching server information.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An unexpected error occurred while fetching server information.",
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
    await bot.add_cog(ServerDisplayCommand(bot))

"""
Advanced Moderation Cog - 7 additional moderation commands
Integrates with existing AdvancedBot structure
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AdvancedModeration(commands.Cog):
    """Advanced moderation commands cog with enhanced features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = 'data/warnings.json'
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        # Initialize warnings file if it doesn't exist
        if not os.path.exists(self.warnings_file):
            with open(self.warnings_file, 'w') as f:
                json.dump({}, f)
    
    def has_moderation_permissions(self, member, guild):
        """Check if a member has moderation permissions"""
        # Server owner always has permissions
        if member == guild.owner:
            return True
        
        # Check for administrator permission
        if member.guild_permissions.administrator:
            return True
        
        # Check for specific moderation permissions
        moderation_perms = [
            member.guild_permissions.kick_members,
            member.guild_permissions.ban_members,
            member.guild_permissions.manage_messages,
            member.guild_permissions.manage_roles
        ]
        
        # If user has any moderation permission, they can use moderation commands
        if any(moderation_perms):
            return True
        
        # Check for moderator role (case insensitive)
        moderator_role_names = ['moderator', 'mod', 'staff', 'admin']
        
        for role in member.roles:
            if role.name.lower() in moderator_role_names:
                return True
        
        return False
    
    def load_warnings(self):
        """Load warnings from JSON file"""
        try:
            with open(self.warnings_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_warnings(self, warnings):
        """Save warnings to JSON file"""
        os.makedirs('data', exist_ok=True)
        with open(self.warnings_file, 'w') as f:
            json.dump(warnings, f, indent=2)
    
    async def get_or_create_muted_role(self, guild):
        """Get or create the muted role"""
        # Look for existing muted role
        muted_role = discord.utils.get(guild.roles, name="Muted")
        
        if muted_role is None:
            # Create muted role
            try:
                muted_role = await guild.create_role(
                    name="Muted",
                    color=discord.Color(0x818386),
                    reason="Auto-created muted role for moderation"
                )
                
                # Set permissions for all channels
                for channel in guild.channels:
                    try:
                        if isinstance(channel, discord.TextChannel):
                            await channel.set_permissions(
                                muted_role,
                                send_messages=False,
                                add_reactions=False,
                                speak=False,
                                reason="Setting up muted role permissions"
                            )
                        elif isinstance(channel, discord.VoiceChannel):
                            await channel.set_permissions(
                                muted_role,
                                speak=False,
                                stream=False,
                                reason="Setting up muted role permissions"
                            )
                    except discord.Forbidden:
                        continue
                        
            except discord.Forbidden:
                return None
        
        return muted_role

    @commands.hybrid_command(name='advban')
    @commands.guild_only()
    async def advanced_ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Advanced ban command with enhanced features
        
        Usage: !advban @user [reason]
        """
        # Check if the command user has moderation permissions
        if not self.has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to ban members.")
            return
        
        # Check if bot has ban permissions
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("❌ I don't have permission to ban members.")
            return
        
        # Can't ban yourself
        if member == ctx.author:
            await ctx.send("❌ You cannot ban yourself.")
            return
        
        # Can't ban the bot
        if member == ctx.guild.me:
            await ctx.send("❌ I cannot ban myself.")
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot ban someone with a higher or equal role.")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot ban someone with a higher or equal role than me.")
            return
        
        try:
            # Try to send DM to user before banning
            try:
                embed = discord.Embed(
                    title="🔨 You have been banned",
                    description=f"You have been banned from **{ctx.guild.name}**",
                    color=0xff0000
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Ban the user
            await member.ban(reason=f"{reason} | Banned by {ctx.author}")
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Banned",
                description=f"**{member}** has been banned",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} banned {member} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to ban user: {e}")
        except Exception as e:
            logger.error(f"Error in advanced ban command: {e}")
            await ctx.send("❌ An error occurred while trying to ban the user.")

    @commands.hybrid_command(name='advunban')
    @commands.guild_only()
    async def advanced_unban(self, ctx, user_id: int, *, reason="No reason provided"):
        """
        Advanced unban command with enhanced features
        
        Usage: !advunban <user_id> [reason]
        """
        # Check if the command user has moderation permissions
        if not self.has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to unban members.")
            return
        
        # Check if bot has ban permissions
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("❌ I don't have permission to unban members.")
            return
        
        try:
            # Get user object
            user = await self.bot.fetch_user(user_id)
            
            # Check if user is actually banned
            try:
                ban_entry = await ctx.guild.fetch_ban(user)
            except discord.NotFound:
                await ctx.send(f"❌ **{user}** is not banned from this server.")
                return
            
            # Unban the user
            await ctx.guild.unban(user, reason=f"{reason} | Unbanned by {ctx.author}")
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"**{user}** has been unbanned",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} unbanned {user} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.NotFound:
            await ctx.send("❌ User not found. Please provide a valid user ID.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unban this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to unban user: {e}")
        except Exception as e:
            logger.error(f"Error in advanced unban command: {e}")
            await ctx.send("❌ An error occurred while trying to unban the user.")

    @commands.hybrid_command(name='advkick')
    @commands.guild_only()
    async def advanced_kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Advanced kick command with enhanced features
        
        Usage: !advkick @user [reason]
        """
        # Check if the command user has moderation permissions
        if not self.has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to kick members.")
            return
        
        # Check if bot has kick permissions
        if not ctx.guild.me.guild_permissions.kick_members:
            await ctx.send("❌ I don't have permission to kick members.")
            return
        
        # Can't kick yourself
        if member == ctx.author:
            await ctx.send("❌ You cannot kick yourself.")
            return
        
        # Can't kick the bot
        if member == ctx.guild.me:
            await ctx.send("❌ I cannot kick myself.")
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot kick someone with a higher or equal role.")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot kick someone with a higher or equal role than me.")
            return
        
        try:
            # Try to send DM to user before kicking
            try:
                embed = discord.Embed(
                    title="👢 You have been kicked",
                    description=f"You have been kicked from **{ctx.guild.name}**",
                    color=0xffa500
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Kick the user
            await member.kick(reason=f"{reason} | Kicked by {ctx.author}")
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Kicked",
                description=f"**{member}** has been kicked",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} kicked {member} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to kick user: {e}")
        except Exception as e:
            logger.error(f"Error in advanced kick command: {e}")
            await ctx.send("❌ An error occurred while trying to kick the user.")

    @commands.hybrid_command(name='advunkick')
    @commands.guild_only()
    async def advanced_unkick(self, ctx, user_id: int, *, reason="No reason provided"):
        """
        Advanced unkick command - creates invite for kicked user
        
        Usage: !advunkick <user_id> [reason]
        """
        # Check if the command user has moderation permissions
        if not self.has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to unkick members.")
            return
        
        # Check if bot has invite permissions
        if not ctx.guild.me.guild_permissions.create_instant_invite:
            await ctx.send("❌ I don't have permission to create invites.")
            return
        
        try:
            # Get user object
            user = await self.bot.fetch_user(user_id)
            
            # Check if user is in the server
            member = ctx.guild.get_member(user_id)
            if member:
                await ctx.send(f"❌ **{user}** is already in the server.")
                return
            
            # Create an invite
            invite = await ctx.channel.create_invite(
                max_uses=1,
                max_age=86400,  # 24 hours
                unique=True,
                reason=f"Unkick invite for {user} | Created by {ctx.author}"
            )
            
            # Try to send DM to user with invite
            try:
                embed = discord.Embed(
                    title="🔄 You've been invited back",
                    description=f"You have been invited back to **{ctx.guild.name}**",
                    color=0x00ff00
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                embed.add_field(name="Invite Link", value=invite.url, inline=False)
                embed.add_field(name="Expires", value="24 hours", inline=False)
                
                await user.send(embed=embed)
                dm_sent = True
            except discord.Forbidden:
                dm_sent = False
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ Unkick Invite Created",
                description=f"Invite created for **{user}**",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            embed.add_field(name="Invite Link", value=invite.url, inline=False)
            embed.add_field(name="DM Sent", value="✅ Yes" if dm_sent else "❌ No (DMs disabled)", inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} created unkick invite for {user} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.NotFound:
            await ctx.send("❌ User not found. Please provide a valid user ID.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create invites or contact this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to create invite: {e}")
        except Exception as e:
            logger.error(f"Error in advanced unkick command: {e}")
            await ctx.send("❌ An error occurred while trying to create the unkick invite.")

    @commands.hybrid_command(name='advmute')
    @commands.guild_only()
    async def advanced_mute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Advanced mute command with automatic role creation
        
        Usage: !advmute @user [reason]
        """
        # Check if the command user has moderation permissions
        if not self.has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to mute members.")
            return
        
        # Check if bot has manage roles permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("❌ I don't have permission to manage roles.")
            return
        
        # Can't mute yourself
        if member == ctx.author:
            await ctx.send("❌ You cannot mute yourself.")
            return
        
        # Can't mute the bot
        if member == ctx.guild.me:
            await ctx.send("❌ I cannot mute myself.")
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot mute someone with a higher or equal role.")
            return
        
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ I cannot mute someone with a higher or equal role than me.")
            return
        
        try:
            # Get or create muted role
            muted_role = await self.get_or_create_muted_role(ctx.guild)
            
            if muted_role is None:
                await ctx.send("❌ I couldn't create or find the muted role. Please check my permissions.")
                return
            
            # Check if user is already muted
            if muted_role in member.roles:
                await ctx.send(f"❌ **{member}** is already muted.")
                return
            
            # Add muted role
            await member.add_roles(muted_role, reason=f"{reason} | Muted by {ctx.author}")
            
            # Try to send DM to user
            try:
                embed = discord.Embed(
                    title="🔇 You have been muted",
                    description=f"You have been muted in **{ctx.guild.name}**",
                    color=0x808080
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Muted",
                description=f"**{member}** has been muted",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} muted {member} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to mute user: {e}")
        except Exception as e:
            logger.error(f"Error in advanced mute command: {e}")
            await ctx.send("❌ An error occurred while trying to mute the user.")

    @commands.hybrid_command(name='advunmute')
    @commands.guild_only()
    async def advanced_unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """
        Advanced unmute command
        
        Usage: !advunmute @user [reason]
        """
        # Check if the command user has moderation permissions
        if not self.has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to unmute members.")
            return
        
        # Check if bot has manage roles permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("❌ I don't have permission to manage roles.")
            return
        
        try:
            # Get muted role
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            
            if muted_role is None:
                await ctx.send("❌ No muted role found in this server.")
                return
            
            # Check if user is actually muted
            if muted_role not in member.roles:
                await ctx.send(f"❌ **{member}** is not muted.")
                return
            
            # Remove muted role
            await member.remove_roles(muted_role, reason=f"{reason} | Unmuted by {ctx.author}")
            
            # Try to send DM to user
            try:
                embed = discord.Embed(
                    title="🔊 You have been unmuted",
                    description=f"You have been unmuted in **{ctx.guild.name}**",
                    color=0x00ff00
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Unmuted",
                description=f"**{member}** has been unmuted",
                color=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} unmuted {member} in {ctx.guild.name}. Reason: {reason}")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unmute this user.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to unmute user: {e}")
        except Exception as e:
            logger.error(f"Error in advanced unmute command: {e}")
            await ctx.send("❌ An error occurred while trying to unmute the user.")

    @commands.hybrid_command(name='advwarn')
    @commands.guild_only()
    async def advanced_warn(self, ctx, member: discord.Member, *, reason):
        """
        Advanced warn command with persistent storage
        
        Usage: !advwarn @user <reason>
        """
        # Check if the command user has moderation permissions
        if not self.has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to warn members.")
            return
        
        # Can't warn yourself
        if member == ctx.author:
            await ctx.send("❌ You cannot warn yourself.")
            return
        
        # Can't warn the bot
        if member == ctx.guild.me:
            await ctx.send("❌ I cannot warn myself.")
            return
        
        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ You cannot warn someone with a higher or equal role.")
            return
        
        try:
            # Load existing warnings
            warnings = self.load_warnings()
            
            # Initialize guild and user data if not exists
            guild_id = str(ctx.guild.id)
            user_id = str(member.id)
            
            if guild_id not in warnings:
                warnings[guild_id] = {}
            
            if user_id not in warnings[guild_id]:
                warnings[guild_id][user_id] = []
            
            # Create warning entry
            warning_data = {
                'id': len(warnings[guild_id][user_id]) + 1,
                'reason': reason,
                'moderator': str(ctx.author.id),
                'moderator_name': str(ctx.author),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add warning
            warnings[guild_id][user_id].append(warning_data)
            
            # Save warnings
            self.save_warnings(warnings)
            
            # Get total warnings count
            total_warnings = len(warnings[guild_id][user_id])
            
            # Try to send DM to user
            try:
                embed = discord.Embed(
                    title="⚠️ You have been warned",
                    description=f"You have been warned in **{ctx.guild.name}**",
                    color=0xffff00
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                embed.add_field(name="Total Warnings", value=total_warnings, inline=False)
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            embed = discord.Embed(
                title="✅ User Warned",
                description=f"**{member}** has been warned",
                color=0x00ff00
            )
            embed.add_field(name="Warning ID", value=warning_data['id'], inline=True)
            embed.add_field(name="Total Warnings", value=total_warnings, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            
            await ctx.send(embed=embed)
            
            # Log the action
            logger.info(f"{ctx.author} warned {member} in {ctx.guild.name}. Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error in advanced warn command: {e}")
            await ctx.send("❌ An error occurred while trying to warn the user.")

    @commands.hybrid_command(name='advwarnings')
    @commands.guild_only()
    async def advanced_warnings(self, ctx, member: Optional[discord.Member] = None):
        """
        List warnings for a user
        
        Usage: !advwarnings [@user]
        """
        if member is None:
            member = ctx.author
        
        # At this point, member is guaranteed to not be None
        assert member is not None
        
        # Check permissions if checking someone else's warnings
        if member != ctx.author and not self.has_moderation_permissions(ctx.author, ctx.guild):
            await ctx.send("❌ You don't have permission to view other members' warnings.")
            return
        
        try:
            # Load warnings
            warnings = self.load_warnings()
            
            guild_id = str(ctx.guild.id)
            user_id = str(member.id)
            
            # Get user warnings
            user_warnings = warnings.get(guild_id, {}).get(user_id, [])
            
            if not user_warnings:
                await ctx.send(f"✅ **{member}** has no warnings.")
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"⚠️ Warnings for {member}",
                description=f"Total warnings: {len(user_warnings)}",
                color=0xffff00
            )
            
            # Add warning fields (limit to last 10)
            for warning in user_warnings[-10:]:
                moderator_name = warning.get('moderator_name', 'Unknown')
                timestamp = warning.get('timestamp', 'Unknown')
                
                # Parse timestamp for better display
                try:
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except:
                    formatted_time = timestamp
                
                embed.add_field(
                    name=f"Warning #{warning['id']}",
                    value=f"**Reason:** {warning['reason']}\n**Moderator:** {moderator_name}\n**Date:** {formatted_time}",
                    inline=False
                )
            
            if len(user_warnings) > 10:
                embed.set_footer(text="Showing last 10 warnings only")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in advanced warnings command: {e}")
            await ctx.send("❌ An error occurred while retrieving warnings.")

async def setup(bot):
    """Setup function to add the cog to the bot"""
    await bot.add_cog(AdvancedModeration(bot))
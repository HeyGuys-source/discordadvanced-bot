import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

class TriggerStorage:
    """Persistent storage system for triggers with JSON file backend."""
    
    def __init__(self, filename: str = "triggers.json"):
        self.filename = filename
        self.triggers = {}
        self.load_triggers()
    
    def load_triggers(self):
        """Load triggers from JSON file."""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.triggers = data.get('triggers', {})
                    logging.info(f"Loaded {len(self.triggers)} triggers from storage")
            else:
                self.triggers = {}
                logging.info("No trigger file found, starting with empty trigger list")
        except Exception as e:
            logging.error(f"Error loading triggers: {e}")
            self.triggers = {}
    
    def save_triggers(self):
        """Save triggers to JSON file."""
        try:
            data = {
                'triggers': self.triggers,
                'last_updated': datetime.now().isoformat(),
                'total_triggers': len(self.triggers)
            }
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved {len(self.triggers)} triggers to storage")
            return True
        except Exception as e:
            logging.error(f"Error saving triggers: {e}")
            return False
    
    def add_trigger(self, guild_id: int, trigger: str, response: str, use_embed: bool, creator_id: int) -> bool:
        """Add a new trigger."""
        guild_key = str(guild_id)
        if guild_key not in self.triggers:
            self.triggers[guild_key] = {}
        
        trigger_lower = trigger.lower()
        self.triggers[guild_key][trigger_lower] = {
            'original_trigger': trigger,
            'response': response,
            'use_embed': use_embed,
            'creator_id': creator_id,
            'created_at': datetime.now().isoformat(),
            'usage_count': 0
        }
        
        return self.save_triggers()
    
    def delete_trigger(self, guild_id: int, trigger: str) -> bool:
        """Delete a trigger."""
        guild_key = str(guild_id)
        trigger_lower = trigger.lower()
        
        if guild_key in self.triggers and trigger_lower in self.triggers[guild_key]:
            del self.triggers[guild_key][trigger_lower]
            
            # Clean up empty guild entries
            if not self.triggers[guild_key]:
                del self.triggers[guild_key]
            
            return self.save_triggers()
        
        return False
    
    def get_trigger(self, guild_id: int, trigger: str) -> Optional[Dict[str, Any]]:
        """Get a specific trigger."""
        guild_key = str(guild_id)
        trigger_lower = trigger.lower()
        
        if guild_key in self.triggers and trigger_lower in self.triggers[guild_key]:
            return self.triggers[guild_key][trigger_lower]
        
        return None
    
    def get_all_triggers(self, guild_id: int) -> Dict[str, Dict[str, Any]]:
        """Get all triggers for a guild."""
        guild_key = str(guild_id)
        return self.triggers.get(guild_key, {})
    
    def increment_usage(self, guild_id: int, trigger: str):
        """Increment usage count for a trigger."""
        guild_key = str(guild_id)
        trigger_lower = trigger.lower()
        
        if guild_key in self.triggers and trigger_lower in self.triggers[guild_key]:
            self.triggers[guild_key][trigger_lower]['usage_count'] += 1
            self.save_triggers()
    
    def trigger_exists(self, guild_id: int, trigger: str) -> bool:
        """Check if a trigger exists."""
        guild_key = str(guild_id)
        trigger_lower = trigger.lower()
        return guild_key in self.triggers and trigger_lower in self.triggers[guild_key]

class TriggerSystem(commands.Cog):
    """Advanced 24/7 trigger system with persistent storage and comprehensive management."""
    
    def __init__(self, bot):
        self.bot = bot
        self.storage = TriggerStorage()
        self.message_cache = {}  # Cache recent messages to avoid duplicate responses
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and respond to triggers 24/7."""
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        # Ignore messages that start with common prefixes to avoid conflicts
        if message.content.startswith(('!', '/', '$', '%', '&', '?', '.', ',', ';')):
            return
        
        # Check if message content matches any triggers
        content_lower = message.content.lower().strip()
        if not content_lower:
            return
        
        # Get triggers for this guild
        triggers = self.storage.get_all_triggers(message.guild.id)
        
        # Check for exact matches and partial matches
        matched_trigger = None
        trigger_data = None
        
        # First check for exact matches
        if content_lower in triggers:
            matched_trigger = content_lower
            trigger_data = triggers[content_lower]
        else:
            # Check for partial matches (trigger contained in message)
            for trigger_key, data in triggers.items():
                if trigger_key in content_lower:
                    matched_trigger = trigger_key
                    trigger_data = data
                    break
        
        if matched_trigger and trigger_data:
            try:
                # Avoid spam by checking recent cache
                cache_key = f"{message.guild.id}_{message.channel.id}_{matched_trigger}"
                current_time = asyncio.get_event_loop().time()
                
                if cache_key in self.message_cache:
                    if current_time - self.message_cache[cache_key] < 3:  # 3 second cooldown
                        return
                
                self.message_cache[cache_key] = current_time
                
                # Clean old cache entries (keep only last 100 entries)
                if len(self.message_cache) > 100:
                    old_keys = list(self.message_cache.keys())[:50]
                    for key in old_keys:
                        del self.message_cache[key]
                
                # Send the trigger response
                if trigger_data['use_embed']:
                    embed = discord.Embed(
                        description=trigger_data['response'],
                        color=discord.Color.blue(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.set_footer(
                        text=f"Triggered by: {trigger_data['original_trigger']}",
                        icon_url=message.author.display_avatar.url
                    )
                    await message.channel.send(embed=embed)
                else:
                    await message.channel.send(trigger_data['response'])
                
                # Increment usage counter
                self.storage.increment_usage(message.guild.id, matched_trigger)
                
                # Log trigger usage
                logging.info(
                    f"Trigger '{matched_trigger}' activated by {message.author} "
                    f"in {message.guild.name}#{message.channel.name}"
                )
                
            except discord.HTTPException as e:
                logging.error(f"Failed to send trigger response: {e}")
            except Exception as e:
                logging.error(f"Error processing trigger: {e}", exc_info=True)

    @app_commands.command(name="createtrigger", description="🎯 Create a new message trigger with automatic responses")
    @app_commands.describe(
        trigger="The word or phrase that will trigger the response",
        message_reply="The message the bot will send when triggered",
        format_type="Choose whether to format as embed or plain text"
    )
    @app_commands.choices(format_type=[
        app_commands.Choice(name="Plain Text", value="no_embed"),
        app_commands.Choice(name="Embed", value="embed")
    ])
    @app_commands.checks.has_permissions(manage_messages=True)
    async def createtrigger(
        self, 
        interaction: discord.Interaction, 
        trigger: str,
        message_reply: str,
        format_type: str
    ):
        """Create a new trigger with comprehensive validation and feedback."""
        try:
            # Input validation
            if not trigger or not trigger.strip():
                embed = discord.Embed(
                    title="❌ Invalid Trigger",
                    description="Trigger cannot be empty or just whitespace.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if not message_reply or not message_reply.strip():
                embed = discord.Embed(
                    title="❌ Invalid Response",
                    description="Message reply cannot be empty or just whitespace.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Length validation
            if len(trigger) > 100:
                embed = discord.Embed(
                    title="❌ Trigger Too Long",
                    description="Trigger must be 100 characters or less.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="📏 Current Length:",
                    value=f"{len(trigger)} characters",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if len(message_reply) > 2000:
                embed = discord.Embed(
                    title="❌ Response Too Long",
                    description="Message reply must be 2000 characters or less.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="📏 Current Length:",
                    value=f"{len(message_reply)} characters",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if trigger already exists
            if self.storage.trigger_exists(interaction.guild.id, trigger):
                embed = discord.Embed(
                    title="⚠️ Trigger Already Exists",
                    description=f"A trigger for `{trigger}` already exists in this server.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Suggestion:",
                    value="Use `/deletetrigger` to remove the existing trigger first, or choose a different trigger phrase.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check guild trigger limit (prevent spam)
            existing_triggers = self.storage.get_all_triggers(interaction.guild.id)
            if len(existing_triggers) >= 200:  # Reasonable limit
                embed = discord.Embed(
                    title="⚠️ Trigger Limit Reached",
                    description="This server has reached the maximum limit of 200 triggers.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Solution:",
                    value="Delete some unused triggers with `/deletetrigger` or `/triggerlist` to manage existing triggers.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create the trigger
            use_embed = format_type == "embed"
            success = self.storage.add_trigger(
                interaction.guild.id, 
                trigger, 
                message_reply, 
                use_embed, 
                interaction.user.id
            )
            
            if success:
                # Success embed
                embed = discord.Embed(
                    title="✅ Trigger Created Successfully!",
                    description=f"New trigger has been added and is now active 24/7!",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                
                embed.add_field(
                    name="🎯 Trigger:",
                    value=f"`{trigger}`",
                    inline=True
                )
                
                embed.add_field(
                    name="📝 Format:",
                    value="**Embed**" if use_embed else "**Plain Text**",
                    inline=True
                )
                
                embed.add_field(
                    name="👤 Created by:",
                    value=interaction.user.mention,
                    inline=True
                )
                
                # Show preview of response
                preview_text = message_reply[:100] + "..." if len(message_reply) > 100 else message_reply
                embed.add_field(
                    name="💬 Response Preview:",
                    value=f"```{preview_text}```",
                    inline=False
                )
                
                embed.add_field(
                    name="🚀 Status:",
                    value="**ACTIVE** - Bot will now respond to this trigger automatically!",
                    inline=False
                )
                
                embed.add_field(
                    name="📊 Server Triggers:",
                    value=f"**{len(existing_triggers) + 1}/200** triggers",
                    inline=True
                )
                
                embed.set_footer(
                    text=f"Created by {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url
                )
                
                await interaction.response.send_message(embed=embed)
                
                # Log successful creation
                logging.info(
                    f"Trigger created by {interaction.user} in {interaction.guild.name}: "
                    f"'{trigger}' -> '{message_reply[:50]}...'"
                )
                
            else:
                embed = discord.Embed(
                    title="❌ Storage Error",
                    description="Failed to save the trigger to storage. Please try again.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An error occurred while creating the trigger.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in createtrigger command: {e}", exc_info=True)

    @app_commands.command(name="deletetrigger", description="🗑️ Delete an existing message trigger")
    @app_commands.describe(
        trigger="The trigger phrase to delete"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def deletetrigger(self, interaction: discord.Interaction, trigger: str):
        """Delete an existing trigger with confirmation."""
        try:
            # Input validation
            if not trigger or not trigger.strip():
                embed = discord.Embed(
                    title="❌ Invalid Input",
                    description="Please specify a trigger to delete.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if trigger exists
            trigger_data = self.storage.get_trigger(interaction.guild.id, trigger)
            if not trigger_data:
                embed = discord.Embed(
                    title="❌ Trigger Not Found",
                    description=f"No trigger found for `{trigger}` in this server.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Suggestion:",
                    value="Use `/triggerlist` to see all available triggers, or check your spelling.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Show trigger info and confirm deletion
            embed = discord.Embed(
                title="🗑️ Delete Trigger Confirmation",
                description=f"Are you sure you want to delete this trigger?",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="🎯 Trigger:",
                value=f"`{trigger_data['original_trigger']}`",
                inline=True
            )
            
            embed.add_field(
                name="📝 Format:",
                value="**Embed**" if trigger_data['use_embed'] else "**Plain Text**",
                inline=True
            )
            
            embed.add_field(
                name="📊 Usage Count:",
                value=f"**{trigger_data['usage_count']}** times",
                inline=True
            )
            
            # Show response preview
            preview_text = trigger_data['response'][:150] + "..." if len(trigger_data['response']) > 150 else trigger_data['response']
            embed.add_field(
                name="💬 Current Response:",
                value=f"```{preview_text}```",
                inline=False
            )
            
            # Get creator info
            try:
                creator = self.bot.get_user(trigger_data['creator_id'])
                creator_name = creator.display_name if creator else f"ID: {trigger_data['creator_id']}"
            except:
                creator_name = f"ID: {trigger_data['creator_id']}"
            
            embed.add_field(
                name="👤 Created by:",
                value=creator_name,
                inline=True
            )
            
            embed.add_field(
                name="📅 Created:",
                value=f"<t:{int(datetime.fromisoformat(trigger_data['created_at']).timestamp())}:R>",
                inline=True
            )
            
            # Create confirmation view
            view = DeleteTriggerView(self.storage, interaction.guild.id, trigger)
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An error occurred while processing the delete request.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in deletetrigger command: {e}", exc_info=True)

    @app_commands.command(name="triggerlist", description="📋 View all message triggers in this server")
    @app_commands.describe(
        page="Page number to view (optional)"
    )
    async def triggerlist(self, interaction: discord.Interaction, page: Optional[int] = 1):
        """Display all triggers in a paginated embed list."""
        try:
            # Get all triggers for this guild
            triggers = self.storage.get_all_triggers(interaction.guild.id)
            
            if not triggers:
                embed = discord.Embed(
                    title="📋 No Triggers Found",
                    description="This server doesn't have any triggers set up yet.",
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="🚀 Get Started:",
                    value="Use `/createtrigger` to create your first trigger!",
                    inline=False
                )
                embed.add_field(
                    name="💡 Example:",
                    value='`/createtrigger trigger:"hello" message_reply:"Hi there!" format_type:"Embed"`',
                    inline=False
                )
                await interaction.response.send_message(embed=embed)
                return
            
            # Pagination setup
            triggers_per_page = 10
            total_triggers = len(triggers)
            total_pages = (total_triggers + triggers_per_page - 1) // triggers_per_page
            
            # Validate page number
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages
            
            # Calculate start and end indices
            start_idx = (page - 1) * triggers_per_page
            end_idx = min(start_idx + triggers_per_page, total_triggers)
            
            # Sort triggers by usage count (most used first)
            sorted_triggers = sorted(
                triggers.items(), 
                key=lambda x: x[1]['usage_count'], 
                reverse=True
            )
            
            page_triggers = sorted_triggers[start_idx:end_idx]
            
            # Create embed
            embed = discord.Embed(
                title="📋 Server Trigger List",
                description=f"Showing **{len(page_triggers)}** triggers (Page {page}/{total_pages})",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            # Add trigger information
            for i, (trigger_key, trigger_data) in enumerate(page_triggers, start_idx + 1):
                # Format trigger entry
                format_icon = "📎" if trigger_data['use_embed'] else "💬"
                usage_info = f"Used {trigger_data['usage_count']} times"
                
                # Truncate response for display
                response_preview = trigger_data['response'][:50] + "..." if len(trigger_data['response']) > 50 else trigger_data['response']
                
                embed.add_field(
                    name=f"{format_icon} `{trigger_data['original_trigger']}`",
                    value=f"**Response:** {response_preview}\n**Usage:** {usage_info}",
                    inline=False
                )
            
            # Add summary information
            embed.add_field(
                name="📊 Server Statistics:",
                value=f"**Total Triggers:** {total_triggers}/200\n**This Page:** {start_idx + 1}-{end_idx}",
                inline=True
            )
            
            # Calculate total usage
            total_usage = sum(data['usage_count'] for data in triggers.values())
            embed.add_field(
                name="🎯 Usage Statistics:",
                value=f"**Total Activations:** {total_usage:,}\n**Average per Trigger:** {total_usage // total_triggers if total_triggers > 0 else 0}",
                inline=True
            )
            
            # Format types breakdown
            embed_count = sum(1 for data in triggers.values() if data['use_embed'])
            plain_count = total_triggers - embed_count
            embed.add_field(
                name="📝 Format Breakdown:",
                value=f"**Embeds:** {embed_count}\n**Plain Text:** {plain_count}",
                inline=True
            )
            
            embed.set_footer(
                text=f"Page {page}/{total_pages} • Use /triggerlist page:[number] to navigate",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            # Create navigation view if multiple pages
            view = None
            if total_pages > 1:
                view = TriggerListView(self.storage, interaction.guild.id, page, total_pages)
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An error occurred while retrieving the trigger list.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in triggerlist command: {e}", exc_info=True)

    @createtrigger.error
    async def createtrigger_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Error handler for createtrigger command."""
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 Insufficient Permissions",
                description="You need the **Manage Messages** permission to create triggers.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="Required Permission:",
                value="• Manage Messages",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @deletetrigger.error
    async def deletetrigger_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Error handler for deletetrigger command."""
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 Insufficient Permissions",
                description="You need the **Manage Messages** permission to delete triggers.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class DeleteTriggerView(discord.ui.View):
    """Confirmation view for trigger deletion."""
    
    def __init__(self, storage: TriggerStorage, guild_id: int, trigger: str):
        super().__init__(timeout=60)
        self.storage = storage
        self.guild_id = guild_id
        self.trigger = trigger
    
    @discord.ui.button(label="✅ Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm and execute trigger deletion."""
        try:
            success = self.storage.delete_trigger(self.guild_id, self.trigger)
            
            if success:
                embed = discord.Embed(
                    title="✅ Trigger Deleted Successfully!",
                    description=f"The trigger `{self.trigger}` has been permanently removed.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="🎯 Status:",
                    value="The bot will no longer respond to this trigger.",
                    inline=False
                )
                
                # Disable all buttons
                for item in self.children:
                    item.disabled = True
                
                await interaction.response.edit_message(embed=embed, view=self)
                
                logging.info(f"Trigger '{self.trigger}' deleted by {interaction.user} in guild {self.guild_id}")
                
            else:
                embed = discord.Embed(
                    title="❌ Deletion Failed",
                    description="Failed to delete the trigger. It may have already been removed.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error During Deletion",
                description="An unexpected error occurred while deleting the trigger.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            logging.error(f"Error deleting trigger: {e}", exc_info=True)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel trigger deletion."""
        embed = discord.Embed(
            title="❌ Deletion Cancelled",
            description=f"The trigger `{self.trigger}` was not deleted and remains active.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        """Handle view timeout."""
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        embed = discord.Embed(
            title="⏰ Confirmation Timeout",
            description=f"Deletion confirmation timed out. The trigger `{self.trigger}` was not deleted.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        
        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass

class TriggerListView(discord.ui.View):
    """Navigation view for paginated trigger list."""
    
    def __init__(self, storage: TriggerStorage, guild_id: int, current_page: int, total_pages: int):
        super().__init__(timeout=300)
        self.storage = storage
        self.guild_id = guild_id
        self.current_page = current_page
        self.total_pages = total_pages
        
        # Disable buttons if not applicable
        if current_page <= 1:
            self.previous_page.disabled = True
        if current_page >= total_pages:
            self.next_page.disabled = True
    
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page."""
        if self.current_page > 1:
            # Use the triggerlist command logic to generate the page
            cog = interaction.client.get_cog('TriggerSystem')
            await cog.triggerlist(interaction, self.current_page - 1)
    
    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page."""
        if self.current_page < self.total_pages:
            # Use the triggerlist command logic to generate the page
            cog = interaction.client.get_cog('TriggerSystem')
            await cog.triggerlist(interaction, self.current_page + 1)
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.primary)
    async def refresh_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh current page."""
        cog = interaction.client.get_cog('TriggerSystem')
        await cog.triggerlist(interaction, self.current_page)

# Setup functions
async def setup(bot):
    """Setup function to add the TriggerSystem cog to the bot."""
    await bot.add_cog(TriggerSystem(bot))
    logging.info("Trigger system loaded successfully")

def add_trigger_commands(bot):
    """Alternative setup function for manual integration."""
    trigger_cog = TriggerSystem(bot)
    
    @bot.tree.command(name="createtrigger", description="🎯 Create a new message trigger with automatic responses")
    @app_commands.describe(
        trigger="The word or phrase that will trigger the response",
        message_reply="The message the bot will send when triggered",
        format_type="Choose whether to format as embed or plain text"
    )
    @app_commands.choices(format_type=[
        app_commands.Choice(name="Plain Text", value="no_embed"),
        app_commands.Choice(name="Embed", value="embed")
    ])
    @app_commands.checks.has_permissions(manage_messages=True)
    async def createtrigger(
        interaction: discord.Interaction, 
        trigger: str,
        message_reply: str,
        format_type: str
    ):
        await trigger_cog.createtrigger(interaction, trigger, message_reply, format_type)
    
    @bot.tree.command(name="deletetrigger", description="🗑️ Delete an existing message trigger")
    @app_commands.describe(trigger="The trigger phrase to delete")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def deletetrigger(interaction: discord.Interaction, trigger: str):
        await trigger_cog.deletetrigger(interaction, trigger)
    
    @bot.tree.command(name="triggerlist", description="📋 View all message triggers in this server")
    @app_commands.describe(page="Page number to view (optional)")
    async def triggerlist(interaction: discord.Interaction, page: Optional[int] = 1):
        await trigger_cog.triggerlist(interaction, page)
    
    # Add the message listener
    @bot.event
    async def on_message(message):
        await trigger_cog.on_message(message)
    
    logging.info("Trigger commands added successfully")
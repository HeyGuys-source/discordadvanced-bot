import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import logging
from typing import Dict, List

class SlotsGame:
    """Advanced slots game with decorative animations and pixel rewards."""
    
    def __init__(self):
        # Slot symbols with their rarities and payouts
        self.symbols = {
            "🍒": {"rarity": 40, "payout": 2, "name": "Cherry"},
            "🍋": {"rarity": 30, "payout": 3, "name": "Lemon"}, 
            "🔔": {"rarity": 20, "payout": 5, "name": "Bell"},
            "⭐": {"rarity": 8, "payout": 10, "name": "Star"},
            "💎": {"rarity": 2, "payout": 50, "name": "Diamond"}
        }
        
        # Animation frames for spinning effect
        self.spin_frames = [
            ["🎰", "🎰", "🎰"],
            ["🌀", "🌀", "🌀"],
            ["💫", "💫", "💫"],
            ["✨", "✨", "✨"]
        ]
        
        # Jackpot combinations (all same symbol)
        self.jackpot_multipliers = {
            "🍒": 10,
            "🍋": 15,
            "🔔": 25,
            "⭐": 50,
            "💎": 100
        }
    
    def get_random_symbol(self) -> str:
        """Get a random symbol based on rarity weights."""
        total_weight = sum(data["rarity"] for data in self.symbols.values())
        random_num = random.randint(1, total_weight)
        
        current_weight = 0
        for symbol, data in self.symbols.items():
            current_weight += data["rarity"]
            if random_num <= current_weight:
                return symbol
        
        return "🍒"  # Fallback
    
    def spin_slots(self) -> tuple:
        """Spin the slots and return the result."""
        return tuple(self.get_random_symbol() for _ in range(3))
    
    def calculate_payout(self, result: tuple, bet_amount: int) -> dict:
        """Calculate the payout for a spin result."""
        symbol1, symbol2, symbol3 = result
        
        # Check for jackpot (all three same)
        if symbol1 == symbol2 == symbol3:
            multiplier = self.jackpot_multipliers[symbol1]
            payout = bet_amount * multiplier
            return {
                "type": "jackpot",
                "payout": payout,
                "multiplier": multiplier,
                "symbol": symbol1
            }
        
        # Check for two matching symbols
        if symbol1 == symbol2 or symbol2 == symbol3 or symbol1 == symbol3:
            # Find the matching symbol
            if symbol1 == symbol2:
                matching_symbol = symbol1
            elif symbol2 == symbol3:
                matching_symbol = symbol2
            else:
                matching_symbol = symbol1
            
            multiplier = self.symbols[matching_symbol]["payout"]
            payout = bet_amount * multiplier
            return {
                "type": "match",
                "payout": payout,
                "multiplier": multiplier,
                "symbol": matching_symbol
            }
        
        # No matches
        return {
            "type": "loss",
            "payout": 0,
            "multiplier": 0,
            "symbol": None
        }
    
    def get_result_embed(self, player: discord.abc.User, result: tuple, payout_info: dict, 
                        bet_amount: int, new_balance: int) -> discord.Embed:
        """Create a decorative embed for the slots result."""
        
        if payout_info["type"] == "jackpot":
            embed = discord.Embed(
                title="🎰 JACKPOT! 🎰",
                description=f"**{player.display_name}** hit the JACKPOT!",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="💥 AMAZING WIN!",
                value=f"Triple **{self.symbols[payout_info['symbol']]['name']}s**!",
                inline=False
            )
        elif payout_info["type"] == "match":
            embed = discord.Embed(
                title="🎰 Winner! 🎰",
                description=f"**{player.display_name}** got a match!",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="🎉 Nice Win!",
                value=f"Matched **{self.symbols[payout_info['symbol']]['name']}s**!",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="🎰 Slots Result 🎰",
                description=f"**{player.display_name}** tried their luck!",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="💔 No Match",
                value="Better luck next time!",
                inline=False
            )
        
        # Show the result
        result_display = " | ".join(result)
        embed.add_field(
            name="🎯 Result:",
            value=f"**{result_display}**",
            inline=True
        )
        
        # Show bet and payout
        embed.add_field(
            name="💰 Bet:",
            value=f"**{bet_amount:,}** pixels",
            inline=True
        )
        
        if payout_info["payout"] > 0:
            embed.add_field(
                name="🏆 Won:",
                value=f"**+{payout_info['payout']:,}** pixels\n(x{payout_info['multiplier']} multiplier)",
                inline=True
            )
        else:
            embed.add_field(
                name="📉 Lost:",
                value=f"**-{bet_amount:,}** pixels",
                inline=True
            )
        
        embed.add_field(
            name="💳 New Balance:",
            value=f"**{new_balance:,}** pixels",
            inline=False
        )
        
        # Add symbols guide
        symbols_guide = ""
        for symbol, data in self.symbols.items():
            symbols_guide += f"{symbol} **{data['name']}** (x{data['payout']})\n"
        
        embed.add_field(
            name="📋 Symbol Guide:",
            value=symbols_guide,
            inline=True
        )
        
        # Add jackpot multipliers
        jackpot_guide = ""
        for symbol, multiplier in self.jackpot_multipliers.items():
            jackpot_guide += f"{symbol}{symbol}{symbol} **x{multiplier}**\n"
        
        embed.add_field(
            name="🎰 Jackpots:",
            value=jackpot_guide,
            inline=True
        )
        
        embed.set_footer(
            text=f"Played by {player.display_name}",
            icon_url=player.display_avatar.url
        )
        
        return embed

class TradeView(discord.ui.View):
    """View for handling trade confirmations."""
    
    def __init__(self, sender: discord.abc.User, receiver: discord.abc.User, amount: int, cog):
        super().__init__(timeout=60.0)
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.cog = cog
        self.confirmed_by_sender = False
        self.confirmed_by_receiver = False
        self.cancelled = False
    
    @discord.ui.button(label="Accept Trade", style=discord.ButtonStyle.green, emoji="✅")
    async def accept_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle trade acceptance."""
        if interaction.user.id not in [self.sender.id, self.receiver.id]:
            await interaction.response.send_message("❌ You are not part of this trade!", ephemeral=True)
            return
        
        if self.cancelled:
            await interaction.response.send_message("❌ This trade has been cancelled!", ephemeral=True)
            return
        
        if interaction.user.id == self.sender.id:
            if not self.confirmed_by_sender:
                self.confirmed_by_sender = True
                await interaction.response.send_message("✅ You have accepted the trade!", ephemeral=True)
        elif interaction.user.id == self.receiver.id:
            if not self.confirmed_by_receiver:
                self.confirmed_by_receiver = True
                await interaction.response.send_message("✅ You have accepted the trade!", ephemeral=True)
        
        # Check if both have confirmed
        if self.confirmed_by_sender and self.confirmed_by_receiver:
            await self.execute_trade(interaction)
    
    @discord.ui.button(label="Cancel Trade", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle trade cancellation."""
        if interaction.user.id not in [self.sender.id, self.receiver.id]:
            await interaction.response.send_message("❌ You are not part of this trade!", ephemeral=True)
            return
        
        self.cancelled = True
        
        embed = discord.Embed(
            title="❌ Trade Cancelled",
            description=f"Trade cancelled by **{interaction.user.display_name}**",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        # Disable all buttons
        for item in self.children:
            try:
                item.disabled = True
            except:
                pass
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    async def execute_trade(self, interaction: discord.Interaction):
        """Execute the confirmed trade."""
        try:
            # Final balance check
            sender_balance = self.cog.get_user_balance(self.sender.id)
            if sender_balance < self.amount:
                embed = discord.Embed(
                    title="❌ Trade Failed",
                    description=f"**{self.sender.display_name}** no longer has enough pixels to complete the trade!",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return
            
            # Execute the trade
            self.cog.update_user_balance(self.sender.id, -self.amount)
            self.cog.update_user_balance(self.receiver.id, self.amount)
            
            sender_new_balance = self.cog.get_user_balance(self.sender.id)
            receiver_new_balance = self.cog.get_user_balance(self.receiver.id)
            
            embed = discord.Embed(
                title="✅ Trade Completed!",
                description=f"**{self.sender.display_name}** traded **{self.amount:,}** pixels to **{self.receiver.display_name}**",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name=f"💰 {self.sender.display_name}'s Balance:",
                value=f"**{sender_new_balance:,}** pixels",
                inline=True
            )
            
            embed.add_field(
                name=f"💰 {self.receiver.display_name}'s Balance:",
                value=f"**{receiver_new_balance:,}** pixels",
                inline=True
            )
            
            embed.set_footer(text="Trade completed successfully!")
            
            # Disable all buttons
            for item in self.children:
                if hasattr(item, 'disabled'):
                    item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Trade Failed",
                description="An error occurred while processing the trade. Please try again.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.edit_message(embed=embed, view=None)
    
    async def on_timeout(self):
        """Handle view timeout."""
        embed = discord.Embed(
            title="⏰ Trade Expired",
            description="This trade has expired due to inactivity.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        
        # Disable all buttons
        for item in self.children:
            try:
                item.disabled = True
            except:
                pass

class SlotsCommand(commands.Cog):
    """Advanced slots command with pixel gambling and decorative animations."""
    
    def __init__(self, bot):
        self.bot = bot
        self.game = SlotsGame()
        self.user_balances = {}  # Simple in-memory balance system
        self.spinning_users = set()  # Track users currently spinning
        self.active_trades = {}  # Track active trades
        
        # Default starting balance
        self.starting_balance = 1000
    
    def get_user_balance(self, user_id: int) -> int:
        """Get user's pixel balance."""
        if user_id not in self.user_balances:
            self.user_balances[user_id] = self.starting_balance
        return self.user_balances[user_id]
    
    def update_user_balance(self, user_id: int, amount: int):
        """Update user's pixel balance."""
        if user_id not in self.user_balances:
            self.user_balances[user_id] = self.starting_balance
        self.user_balances[user_id] += amount
    
    def is_admin(self, member: discord.abc.User) -> bool:
        """Check if user has admin permissions."""
        if not isinstance(member, discord.Member):
            return False
        return member.guild_permissions.administrator or any(role.permissions.administrator for role in member.roles)
    
    @app_commands.command(name="slots", description="🎰 Play the advanced pixel slots game")
    @app_commands.describe(
        bet="Amount of pixels to bet (1-10,000)"
    )
    async def slots(self, interaction: discord.Interaction, bet: int = 50):
        """Play the slots game with pixel betting."""
        try:
            # Check if user is already spinning
            if interaction.user.id in self.spinning_users:
                embed = discord.Embed(
                    title="⚠️ Already Spinning",
                    description="You're already spinning the slots! Wait for your current game to finish.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Validate bet amount - MODIFIED: Changed from 1-1000 to 1-10,000
            if bet < 1 or bet > 10000:
                embed = discord.Embed(
                    title="⚠️ Invalid Bet",
                    description="Bet amount must be between **1** and **10,000** pixels.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Suggested Bets:",
                    value="• **1** - Minimum bet\n• **50** - Default bet\n• **100** - Medium risk\n• **500** - High risk\n• **1,000** - Very high risk\n• **10,000** - Maximum bet",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if user has enough balance
            current_balance = self.get_user_balance(interaction.user.id)
            if current_balance < bet:
                embed = discord.Embed(
                    title="💸 Insufficient Pixels",
                    description=f"You don't have enough pixels to bet **{bet:,}**!",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💳 Your Balance:",
                    value=f"**{current_balance:,}** pixels",
                    inline=True
                )
                embed.add_field(
                    name="💡 Tip:",
                    value="Try a smaller bet or wait for your daily pixels!",
                    inline=True
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Add user to spinning set
            self.spinning_users.add(interaction.user.id)
            
            # Create spinning animation embed
            embed = discord.Embed(
                title="🎰 Spinning Slots... 🎰",
                description=f"**{interaction.user.display_name}** is spinning for **{bet:,}** pixels!",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="🎯 Current Spin:",
                value="**🌀 | 🌀 | 🌀**",
                inline=False
            )
            embed.add_field(
                name="💰 Bet Amount:",
                value=f"**{bet:,}** pixels",
                inline=True
            )
            embed.add_field(
                name="💳 Balance:",
                value=f"**{current_balance:,}** pixels",
                inline=True
            )
            embed.set_footer(text="🎲 Good luck!")
            
            await interaction.response.send_message(embed=embed)
            
            # Animate the spinning
            message = await interaction.original_response()
            
            for i in range(4):  # 4 animation frames
                await asyncio.sleep(0.8)
                
                frame = self.game.spin_frames[i]
                embed.set_field_at(
                    0,
                    name="🎯 Current Spin:",
                    value=f"**{' | '.join(frame)}**",
                    inline=False
                )
                
                try:
                    await message.edit(embed=embed)
                except:
                    break
            
            # Final spin result
            await asyncio.sleep(1)
            result = self.game.spin_slots()
            payout_info = self.game.calculate_payout(result, bet)
            
            # Update balance
            if payout_info["payout"] > 0:
                self.update_user_balance(interaction.user.id, payout_info["payout"] - bet)
                new_balance = self.get_user_balance(interaction.user.id)
            else:
                self.update_user_balance(interaction.user.id, -bet)
                new_balance = self.get_user_balance(interaction.user.id)
            
            # Create result embed
            result_embed = self.game.get_result_embed(
                interaction.user, result, payout_info, bet, new_balance
            )
            
            try:
                await message.edit(embed=result_embed)
            except Exception as e:
                logging.error(f"Error editing slots result: {e}")
            
            # Remove user from spinning set
            self.spinning_users.discard(interaction.user.id)
            
        except Exception as e:
            logging.error(f"Error in slots command: {e}")
            self.spinning_users.discard(interaction.user.id)
            
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while playing slots. Please try again.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(embed=embed)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                pass
    
    @app_commands.command(name="add", description="💰 Add pixels to a user's balance (Admin only)")
    @app_commands.describe(
        user="User to give pixels to",
        amount="Amount of pixels to add (1-500,000)"
    )
    async def add_money(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Add pixels to a user's balance - Admin only command."""
        try:
            # Check if user is admin
            if not self.is_admin(interaction.user):
                embed = discord.Embed(
                    title="❌ Access Denied",
                    description="You need administrator permissions to use this command.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Validate amount
            if amount < 1 or amount > 500000:
                embed = discord.Embed(
                    title="⚠️ Invalid Amount",
                    description="Amount must be between **1** and **500,000** pixels.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get current balance
            old_balance = self.get_user_balance(user.id)
            
            # Add pixels
            self.update_user_balance(user.id, amount)
            new_balance = self.get_user_balance(user.id)
            
            # Create success embed
            embed = discord.Embed(
                title="💰 Pixels Added Successfully",
                description=f"**{interaction.user.display_name}** added **{amount:,}** pixels to **{user.display_name}**",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="📊 Balance Update:",
                value=f"**{old_balance:,}** → **{new_balance:,}** pixels",
                inline=False
            )
            
            embed.add_field(
                name="➕ Amount Added:",
                value=f"**+{amount:,}** pixels",
                inline=True
            )
            
            embed.add_field(
                name="👤 Recipient:",
                value=f"**{user.display_name}**",
                inline=True
            )
            
            embed.set_footer(
                text=f"Added by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logging.error(f"Error in add money command: {e}")
            
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while adding pixels. Please try again.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(embed=embed)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                pass
    
    @app_commands.command(name="trade", description="🤝 Trade pixels with another player")
    @app_commands.describe(
        user="User to trade with",
        amount="Amount of pixels to trade (1-100,000)"
    )
    async def trade(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Trade pixels with another player."""
        try:
            # Check if trying to trade with self
            if user.id == interaction.user.id:
                embed = discord.Embed(
                    title="❌ Invalid Trade",
                    description="You cannot trade with yourself!",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if trading with a bot
            if user.bot:
                embed = discord.Embed(
                    title="❌ Invalid Trade",
                    description="You cannot trade with bots!",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Validate amount
            if amount < 1 or amount > 100000:
                embed = discord.Embed(
                    title="⚠️ Invalid Amount",
                    description="Trade amount must be between **1** and **100,000** pixels.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if sender has enough balance
            sender_balance = self.get_user_balance(interaction.user.id)
            if sender_balance < amount:
                embed = discord.Embed(
                    title="💸 Insufficient Pixels",
                    description=f"You don't have enough pixels to trade **{amount:,}**!",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💳 Your Balance:",
                    value=f"**{sender_balance:,}** pixels",
                    inline=True
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if either user already has an active trade
            trade_key = f"{min(interaction.user.id, user.id)}_{max(interaction.user.id, user.id)}"
            if trade_key in self.active_trades:
                embed = discord.Embed(
                    title="⚠️ Trade In Progress",
                    description="You or the other user already have an active trade. Please wait for it to complete.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get receiver balance for display
            receiver_balance = self.get_user_balance(user.id)
            
            # Create trade embed
            embed = discord.Embed(
                title="🤝 Trade Proposal",
                description=f"**{interaction.user.display_name}** wants to trade **{amount:,}** pixels to **{user.display_name}**",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name=f"💰 {interaction.user.display_name}'s Balance:",
                value=f"**{sender_balance:,}** pixels",
                inline=True
            )
            
            embed.add_field(
                name=f"💰 {user.display_name}'s Balance:",
                value=f"**{receiver_balance:,}** pixels",
                inline=True
            )
            
            embed.add_field(
                name="💸 Trade Amount:",
                value=f"**{amount:,}** pixels",
                inline=False
            )
            
            embed.add_field(
                name="📋 Instructions:",
                value="Both players need to click **Accept Trade** to complete the transaction.\nClick **Cancel Trade** to cancel.",
                inline=False
            )
            
            embed.set_footer(text="Trade expires in 60 seconds")
            
            # Create trade view
            trade_view = TradeView(interaction.user, user, amount, self)
            
            # Mark trade as active
            self.active_trades[trade_key] = trade_view
            
            await interaction.response.send_message(embed=embed, view=trade_view)
            
            # Wait for trade to complete and clean up
            await trade_view.wait()
            self.active_trades.pop(trade_key, None)
            
        except Exception as e:
            logging.error(f"Error in trade command: {e}")
            
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while setting up the trade. Please try again.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(embed=embed, view=None)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                pass
    
    @app_commands.command(name="balance", description="💳 Check your pixel balance")
    @app_commands.describe(
        user="User to check balance for (optional)"
    )
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check pixel balance for yourself or another user."""
        try:
            target_user = user if user else interaction.user
            balance = self.get_user_balance(target_user.id)
            
            if target_user.id == interaction.user.id:
                title = "💳 Your Balance"
                description = f"You have **{balance:,}** pixels!"
            else:
                title = f"💳 {target_user.display_name}'s Balance"
                description = f"**{target_user.display_name}** has **{balance:,}** pixels!"
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.set_footer(
                text=f"Balance for {target_user.display_name}",
                icon_url=target_user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logging.error(f"Error in balance command: {e}")
            
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while checking balance. Please try again.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(embed=embed)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                pass

# Setup function for the cog
async def setup(bot):
    await bot.add_cog(SlotsCommand(bot))

# Main bot setup and run
if __name__ == "__main__":
    import os
    
    # Bot setup
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        try:
            synced = await bot.tree.sync()
            print(f'Synced {len(synced)} command(s)')
        except Exception as e:
            print(f'Failed to sync commands: {e}')
    
    async def main():
        async with bot:
            await bot.add_cog(SlotsCommand(bot))
            # You need to replace 'YOUR_BOT_TOKEN' with your actual bot token
            token = os.getenv('DISCORD_BOT_TOKEN')
            if not token:
                print("Error: Please set your DISCORD_BOT_TOKEN environment variable")
                return
            await bot.start(token)
    
    import asyncio
    asyncio.run(main())

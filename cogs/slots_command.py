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
    
    def get_result_embed(self, player: discord.Member, result: tuple, payout_info: dict, 
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

class SlotsCommand(commands.Cog):
    """Advanced slots command with pixel gambling and decorative animations."""
    
    def __init__(self, bot):
        self.bot = bot
        self.game = SlotsGame()
        self.user_balances = {}  # Simple in-memory balance system
        self.spinning_users = set()  # Track users currently spinning
        
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
    
    @app_commands.command(name="slots", description="🎰 Play the advanced pixel slots game")
    @app_commands.describe(
        bet="Amount of pixels to bet (10-1000)"
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
            
            # Validate bet amount
            if bet < 10 or bet > 1000:
                embed = discord.Embed(
                    title="⚠️ Invalid Bet",
                    description="Bet amount must be between **10** and **1,000** pixels.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Suggested Bets:",
                    value="• **10** - Minimum bet\n• **50** - Default bet\n• **100** - Medium risk\n• **500** - High risk\n• **1000** - Maximum bet",
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
            
            # Add view with play again button if user has enough pixels
            view = None
            if new_balance >= 10:
                view = SlotsView(self, interaction.user.id)
            
            await message.edit(embed=result_embed, view=view)
            
            # Remove user from spinning set
            self.spinning_users.discard(interaction.user.id)
            
            # Log the game
            logging.info(
                f"Slots played by {interaction.user} - Bet: {bet}, "
                f"Result: {result}, Payout: {payout_info['payout']}, "
                f"New Balance: {new_balance}"
            )
            
        except Exception as e:
            # Remove user from spinning set on error
            self.spinning_users.discard(interaction.user.id)
            
            embed = discord.Embed(
                title="❌ Slots Error",
                description="An error occurred while playing slots.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in slots command: {e}", exc_info=True)
    
    @app_commands.command(name="balance", description="💳 Check your pixel balance")
    async def balance(self, interaction: discord.Interaction):
        """Check user's pixel balance."""
        try:
            balance = self.get_user_balance(interaction.user.id)
            
            embed = discord.Embed(
                title="💳 Pixel Balance",
                description=f"**{interaction.user.display_name}**'s pixel wallet",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="💰 Current Balance:",
                value=f"**{balance:,}** pixels",
                inline=False
            )
            
            # Balance status
            if balance >= 1000:
                status = "🤑 **Rich!** - You're doing great!"
            elif balance >= 500:
                status = "😊 **Comfortable** - Nice balance!"
            elif balance >= 100:
                status = "😐 **Okay** - Be careful with your bets!"
            elif balance >= 10:
                status = "😰 **Low** - Consider smaller bets!"
            else:
                status = "💸 **Broke** - Time for daily pixels!"
            
            embed.add_field(
                name="📊 Status:",
                value=status,
                inline=False
            )
            
            embed.add_field(
                name="🎰 Can Play:",
                value="✅ **Yes!**" if balance >= 10 else "❌ **No** - Need at least 10 pixels",
                inline=True
            )
            
            embed.add_field(
                name="💡 Tips:",
                value="• Use `/slots` to gamble\n• Start with small bets\n• Know when to stop!",
                inline=True
            )
            
            embed.set_footer(
                text=f"Wallet for {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Balance Error",
                description="An error occurred while checking your balance.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in balance command: {e}", exc_info=True)

class SlotsView(discord.ui.View):
    """Interactive view with play again and balance buttons."""
    
    def __init__(self, cog: SlotsCommand, user_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
    
    @discord.ui.button(label="🎰 Play Again", style=discord.ButtonStyle.primary)
    async def play_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Play slots again with the same bet."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
            return
        
        # Simulate the slots command with default bet
        await self.cog.slots(interaction, bet=50)
    
    @discord.ui.button(label="💳 Check Balance", style=discord.ButtonStyle.secondary)
    async def check_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Check current balance."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
            return
        
        await self.cog.balance(interaction)

# Setup functions
async def setup(bot):
    """Setup function to add the SlotsCommand cog to the bot."""
    await bot.add_cog(SlotsCommand(bot))
    logging.info("Slots command loaded successfully")

def add_slots_command(bot):
    """Alternative setup function for manual integration."""
    slots_cog = SlotsCommand(bot)
    
    @bot.tree.command(name="slots", description="🎰 Play the advanced pixel slots game")
    @app_commands.describe(bet="Amount of pixels to bet (10-1000)")
    async def slots(interaction: discord.Interaction, bet: int = 50):
        await slots_cog.slots(interaction, bet)
    
    @bot.tree.command(name="balance", description="💳 Check your pixel balance")
    async def balance(interaction: discord.Interaction):
        await slots_cog.balance(interaction)
    
    logging.info("Slots commands added successfully")
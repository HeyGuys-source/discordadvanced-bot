import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import logging
from typing import Optional

class GuessNumberGame:
    """Advanced number guessing game with decorative elements and statistics."""
    
    def __init__(self, player: discord.Member, min_num: int = 1, max_num: int = 10, max_attempts: int = 3):
        self.player = player
        self.min_num = min_num
        self.max_num = max_num
        self.secret_number = random.randint(min_num, max_num)
        self.max_attempts = max_attempts
        self.attempts_used = 0
        self.guesses = []
        self.is_active = True
        self.won = False
        
        # Decorative elements
        self.difficulty_emoji = {
            (1, 10): "😊",
            (1, 50): "😐", 
            (1, 100): "😤"
        }
        
        self.attempt_emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    
    def make_guess(self, guess: int):
        """Process a guess and return the result."""
        if not self.is_active:
            return "game_over"
        
        if guess in self.guesses:
            return "already_guessed"
        
        self.guesses.append(guess)
        self.attempts_used += 1
        
        if guess == self.secret_number:
            self.is_active = False
            self.won = True
            return "correct"
        
        if self.attempts_used >= self.max_attempts:
            self.is_active = False
            return "out_of_attempts"
        
        return "too_high" if guess > self.secret_number else "too_low"
    
    def get_difficulty_emoji(self):
        """Get emoji based on difficulty."""
        for (min_val, max_val), emoji in self.difficulty_emoji.items():
            if self.min_num == min_val and self.max_num == max_val:
                return emoji
        return "🎲"
    
    def get_current_embed(self, last_result: Optional[str] = None, last_guess: Optional[int] = None):
        """Generate current game state embed."""
        if self.won:
            embed = discord.Embed(
                title="🎉 Congratulations!",
                description=f"**{self.player.display_name}** guessed the number correctly!",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="🎯 The number was:",
                value=f"**{self.secret_number}**",
                inline=True
            )
            embed.add_field(
                name="📊 Attempts used:",
                value=f"**{self.attempts_used}/{self.max_attempts}**",
                inline=True
            )
            
            # Performance rating
            if self.attempts_used == 1:
                rating = "🏆 PERFECT!"
            elif self.attempts_used == 2:
                rating = "⭐ EXCELLENT!"
            else:
                rating = "👍 GOOD!"
            
            embed.add_field(name="🏅 Rating:", value=rating, inline=True)
            
        elif not self.is_active:
            embed = discord.Embed(
                title="💔 Game Over!",
                description=f"**{self.player.display_name}** ran out of attempts!",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="🎯 The number was:",
                value=f"**{self.secret_number}**",
                inline=True
            )
            embed.add_field(
                name="📊 Attempts used:",
                value=f"**{self.attempts_used}/{self.max_attempts}**",
                inline=True
            )
        else:
            difficulty_emoji = self.get_difficulty_emoji()
            embed = discord.Embed(
                title=f"🎲 Number Guessing Game {difficulty_emoji}",
                description=f"**{self.player.display_name}**, guess the number!",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="🎯 Range:",
                value=f"**{self.min_num}** - **{self.max_num}**",
                inline=True
            )
            
            attempts_left = self.max_attempts - self.attempts_used
            embed.add_field(
                name="💪 Attempts left:",
                value=f"**{attempts_left}/{self.max_attempts}**",
                inline=True
            )
            
            # Show last result
            if last_result and last_guess is not None:
                if last_result == "too_high":
                    embed.add_field(
                        name="📈 Last guess:",
                        value=f"**{last_guess}** is too high!",
                        inline=True
                    )
                elif last_result == "too_low":
                    embed.add_field(
                        name="📉 Last guess:",
                        value=f"**{last_guess}** is too low!",
                        inline=True
                    )
                elif last_result == "already_guessed":
                    embed.add_field(
                        name="⚠️ Already guessed:",
                        value=f"You already tried **{last_guess}**!",
                        inline=True
                    )
            
            # Show all previous guesses
            if self.guesses:
                guesses_str = " • ".join(map(str, sorted(self.guesses)))
                embed.add_field(
                    name="📝 Previous guesses:",
                    value=guesses_str,
                    inline=False
                )
        
        # Show attempt indicators
        attempt_indicators = ""
        for i in range(self.max_attempts):
            if i < self.attempts_used:
                attempt_indicators += "🔴 "
            else:
                attempt_indicators += "⚪ "
        
        embed.add_field(
            name="🎯 Attempts:",
            value=attempt_indicators,
            inline=False
        )
        
        embed.set_footer(
            text=f"Playing as {self.player.display_name}",
            icon_url=self.player.display_avatar.url
        )
        
        return embed

class GuessNumberView(discord.ui.View):
    """Interactive view with number buttons for the guessing game."""
    
    def __init__(self, game: GuessNumberGame, cog):
        super().__init__(timeout=180)  # 3 minute timeout
        self.game = game
        self.cog = cog
        
        # Create number buttons based on range
        if game.max_num <= 10:
            # Small range - show all numbers as buttons
            for num in range(game.min_num, game.max_num + 1):
                button = NumberButton(num)
                self.add_item(button)
        else:
            # Large range - show input modal button
            self.add_item(InputNumberButton())
    
    async def on_timeout(self):
        """Handle view timeout."""
        if self.game.player.id in self.cog.active_games:
            del self.cog.active_games[self.game.player.id]
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        embed = discord.Embed(
            title="⏰ Game Timeout",
            description="The number guessing game has timed out due to inactivity.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="🎯 The number was:",
            value=f"**{self.game.secret_number}**",
            inline=False
        )
        
        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass

class NumberButton(discord.ui.Button):
    """Individual number button for the guessing game."""
    
    def __init__(self, number: int):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=str(number),
            custom_id=f"guess_{number}"
        )
        self.number = number
    
    async def callback(self, interaction: discord.Interaction):
        """Handle number button press."""
        try:
            view = self.view
            game = view.game
            
            # Check if it's the right player
            if interaction.user.id != game.player.id:
                await interaction.response.send_message(
                    "❌ This is not your game!", ephemeral=True
                )
                return
            
            # Make the guess
            result = game.make_guess(self.number)
            
            # Update button style based on result
            if result in ["correct"]:
                self.style = discord.ButtonStyle.success
            elif result in ["too_high", "too_low", "out_of_attempts"]:
                self.style = discord.ButtonStyle.danger
            elif result == "already_guessed":
                self.style = discord.ButtonStyle.secondary
            
            self.disabled = True
            
            # Update embed
            embed = game.get_current_embed(result, self.number)
            
            # Disable all buttons if game is over
            if not game.is_active:
                for item in view.children:
                    item.disabled = True
                # Remove from active games
                if game.player.id in view.cog.active_games:
                    del view.cog.active_games[game.player.id]
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while processing your guess.", ephemeral=True
            )
            logging.error(f"Error in number button callback: {e}", exc_info=True)

class InputNumberButton(discord.ui.Button):
    """Button that opens a modal for number input."""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="🔢 Enter Number",
            custom_id="input_number"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Show modal for number input."""
        try:
            view = self.view
            game = view.game
            
            # Check if it's the right player
            if interaction.user.id != game.player.id:
                await interaction.response.send_message(
                    "❌ This is not your game!", ephemeral=True
                )
                return
            
            modal = NumberInputModal(game, view)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while opening the input modal.", ephemeral=True
            )
            logging.error(f"Error in input button callback: {e}", exc_info=True)

class NumberInputModal(discord.ui.Modal):
    """Modal for entering numbers in larger range games."""
    
    def __init__(self, game: GuessNumberGame, view: GuessNumberView):
        super().__init__(title=f"Guess a number ({game.min_num}-{game.max_num})")
        self.game = game
        self.view = view
        
        self.number_input = discord.ui.TextInput(
            label="Your Guess",
            placeholder=f"Enter a number between {game.min_num} and {game.max_num}",
            min_length=1,
            max_length=3
        )
        self.add_item(self.number_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            # Validate input
            try:
                guess = int(self.number_input.value)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Please enter a valid number!", ephemeral=True
                )
                return
            
            if guess < self.game.min_num or guess > self.game.max_num:
                await interaction.response.send_message(
                    f"❌ Number must be between {self.game.min_num} and {self.game.max_num}!", 
                    ephemeral=True
                )
                return
            
            # Make the guess
            result = self.game.make_guess(guess)
            
            # Update embed
            embed = self.game.get_current_embed(result, guess)
            
            # Disable buttons if game is over
            if not self.game.is_active:
                for item in self.view.children:
                    item.disabled = True
                # Remove from active games
                if self.game.player.id in self.view.cog.active_games:
                    del self.view.cog.active_games[self.game.player.id]
            
            await interaction.response.edit_message(embed=embed, view=self.view)
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ An error occurred while processing your guess.", ephemeral=True
            )
            logging.error(f"Error in number input modal: {e}", exc_info=True)

class GuessNumberCommand(commands.Cog):
    """Advanced number guessing command with decorative elements and multiple difficulty levels."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # user_id: GuessNumberGame
    
    @app_commands.command(name="guessnumber", description="🎲 Start an advanced number guessing game")
    @app_commands.describe(
        difficulty="Choose the difficulty level",
        attempts="Number of attempts (1-5, default varies by difficulty)"
    )
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="😊 Easy (1-10)", value="easy"),
        app_commands.Choice(name="😐 Medium (1-50)", value="medium"),
        app_commands.Choice(name="😤 Hard (1-100)", value="hard")
    ])
    async def guessnumber(
        self, 
        interaction: discord.Interaction,
        difficulty: str = "easy",
        attempts: Optional[int] = None
    ):
        """Start a new number guessing game."""
        try:
            # Check if user already has an active game
            if interaction.user.id in self.active_games:
                embed = discord.Embed(
                    title="⚠️ Game Already Active",
                    description="You already have an active number guessing game! Finish it first or wait for it to timeout.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Set game parameters based on difficulty
            if difficulty == "easy":
                min_num, max_num = 1, 10
                default_attempts = 3
            elif difficulty == "medium":
                min_num, max_num = 1, 50
                default_attempts = 7
            else:  # hard
                min_num, max_num = 1, 100
                default_attempts = 10
            
            # Validate attempts
            if attempts is not None:
                if attempts < 1 or attempts > 15:
                    embed = discord.Embed(
                        title="⚠️ Invalid Attempts",
                        description="Number of attempts must be between **1** and **15**.",
                        color=discord.Color.orange(),
                        timestamp=discord.utils.utcnow()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                max_attempts = attempts
            else:
                max_attempts = default_attempts
            
            # Create new game
            game = GuessNumberGame(interaction.user, min_num, max_num, max_attempts)
            self.active_games[interaction.user.id] = game
            
            # Create initial embed
            embed = game.get_current_embed()
            embed.add_field(
                name="🎮 How to play:",
                value="Guess the secret number I'm thinking of!\nUse the buttons below to make your guesses.",
                inline=False
            )
            
            # Add difficulty info
            difficulty_info = {
                "easy": "😊 **Easy Mode** - Perfect for beginners!",
                "medium": "😐 **Medium Mode** - A nice challenge!",
                "hard": "😤 **Hard Mode** - For the brave!"
            }
            embed.add_field(
                name="🎯 Difficulty:",
                value=difficulty_info[difficulty],
                inline=False
            )
            
            # Create interactive view
            view = GuessNumberView(game, self)
            
            await interaction.response.send_message(embed=embed, view=view)
            
            # Schedule game cleanup after 10 minutes
            await asyncio.sleep(600)  # 10 minutes
            if interaction.user.id in self.active_games:
                del self.active_games[interaction.user.id]
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Game Error",
                description="An error occurred while starting the number guessing game.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in guessnumber command: {e}", exc_info=True)

# Setup functions
async def setup(bot):
    """Setup function to add the GuessNumberCommand cog to the bot."""
    await bot.add_cog(GuessNumberCommand(bot))
    logging.info("GuessNumber command loaded successfully")

def add_guessnumber_command(bot):
    """Alternative setup function for manual integration."""
    guessnumber_cog = GuessNumberCommand(bot)
    
    @bot.tree.command(name="guessnumber", description="🎲 Start an advanced number guessing game")
    @app_commands.describe(
        difficulty="Choose the difficulty level",
        attempts="Number of attempts (1-5, default varies by difficulty)"
    )
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="😊 Easy (1-10)", value="easy"),
        app_commands.Choice(name="😐 Medium (1-50)", value="medium"),
        app_commands.Choice(name="😤 Hard (1-100)", value="hard")
    ])
    async def guessnumber(
        interaction: discord.Interaction,
        difficulty: str = "easy",
        attempts: Optional[int] = None
    ):
        await guessnumber_cog.guessnumber(interaction, difficulty, attempts)
    
    logging.info("GuessNumber command added successfully")
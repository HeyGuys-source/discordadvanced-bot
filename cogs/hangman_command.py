import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import logging

class HangmanGame:
    """Hangman game class with advanced features and decorative elements."""
    
    def __init__(self, word: str, player: discord.Member):
        self.word = word.upper()
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.max_wrong_guesses = 6
        self.player = player
        self.is_active = True
        
        # Hangman stages for decoration
        self.hangman_stages = [
            "```\n   +---+\n   |   |\n       |\n       |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n       |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n   |   |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n  /|   |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n  /|\\  |\n       |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n  /|\\  |\n  /    |\n       |\n=========```",
            "```\n   +---+\n   |   |\n   O   |\n  /|\\  |\n  / \\  |\n       |\n=========```"
        ]
    
    def get_display_word(self):
        """Get the word with guessed letters revealed."""
        return ' '.join([letter if letter in self.guessed_letters else '▯' for letter in self.word])
    
    def guess_letter(self, letter: str):
        """Make a guess and return the result."""
        letter = letter.upper()
        
        if letter in self.guessed_letters:
            return "already_guessed"
        
        self.guessed_letters.add(letter)
        
        if letter in self.word:
            if set(self.word).issubset(self.guessed_letters):
                self.is_active = False
                return "won"
            return "correct"
        else:
            self.wrong_guesses += 1
            if self.wrong_guesses >= self.max_wrong_guesses:
                self.is_active = False
                return "lost"
            return "wrong"
    
    def get_current_embed(self):
        """Get the current game state as an embed."""
        if not self.is_active and self.wrong_guesses >= self.max_wrong_guesses:
            # Game lost
            embed = discord.Embed(
                title="💀 Game Over!",
                description=f"**{self.player.display_name}** was hanged!",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="💡 The word was:",
                value=f"**{self.word}**",
                inline=False
            )
        elif not self.is_active:
            # Game won
            embed = discord.Embed(
                title="🎉 Congratulations!",
                description=f"**{self.player.display_name}** solved the word!",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="✅ Word:",
                value=f"**{self.word}**",
                inline=False
            )
            embed.add_field(
                name="📊 Stats:",
                value=f"Wrong guesses: **{self.wrong_guesses}/{self.max_wrong_guesses}**",
                inline=False
            )
        else:
            # Game in progress
            embed = discord.Embed(
                title="🎪 Hangman Game",
                description=f"**{self.player.display_name}**'s turn to guess!",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
        
        if self.is_active or self.wrong_guesses >= self.max_wrong_guesses:
            embed.add_field(
                name="🎨 Hangman:",
                value=self.hangman_stages[self.wrong_guesses],
                inline=False
            )
        
        embed.add_field(
            name="🔤 Word:",
            value=f"`{self.get_display_word()}`",
            inline=True
        )
        
        embed.add_field(
            name="❌ Wrong guesses:",
            value=f"**{self.wrong_guesses}/{self.max_wrong_guesses}**",
            inline=True
        )
        
        if self.guessed_letters:
            correct_letters = [letter for letter in self.guessed_letters if letter in self.word]
            wrong_letters = [letter for letter in self.guessed_letters if letter not in self.word]
            
            if correct_letters:
                embed.add_field(
                    name="✅ Correct letters:",
                    value=' '.join(sorted(correct_letters)),
                    inline=True
                )
            
            if wrong_letters:
                embed.add_field(
                    name="❌ Wrong letters:",
                    value=' '.join(sorted(wrong_letters)),
                    inline=True
                )
        
        embed.set_footer(
            text=f"Playing as {self.player.display_name}",
            icon_url=self.player.display_avatar.url
        )
        
        return embed

class HangmanCommand(commands.Cog):
    """Advanced Hangman command with decorative elements and interactive gameplay."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # user_id: HangmanGame
        
        # Word lists for different categories
        self.word_categories = {
            "animals": ["ELEPHANT", "GIRAFFE", "PENGUIN", "DOLPHIN", "BUTTERFLY", "KANGAROO", "OCTOPUS", "FLAMINGO"],
            "countries": ["AUSTRALIA", "CANADA", "BRAZIL", "GERMANY", "JAPAN", "EGYPT", "FRANCE", "ITALY"],
            "foods": ["PIZZA", "HAMBURGER", "CHOCOLATE", "STRAWBERRY", "SANDWICH", "COOKIE", "PANCAKE", "SPAGHETTI"],
            "objects": ["COMPUTER", "TELEPHONE", "BICYCLE", "UMBRELLA", "KEYBOARD", "GUITAR", "CAMERA", "BACKPACK"]
        }
        
    @app_commands.command(name="hangman", description="🎪 Start an advanced hangman word guessing game")
    @app_commands.describe(
        category="Choose a word category (optional)",
        difficulty="Choose difficulty level (optional)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="🐾 Animals", value="animals"),
        app_commands.Choice(name="🌍 Countries", value="countries"),
        app_commands.Choice(name="🍕 Foods", value="foods"),
        app_commands.Choice(name="📱 Objects", value="objects"),
        app_commands.Choice(name="🎲 Random", value="random")
    ])
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="😊 Easy (4-6 letters)", value="easy"),
        app_commands.Choice(name="😐 Medium (7-9 letters)", value="medium"),
        app_commands.Choice(name="😤 Hard (10+ letters)", value="hard")
    ])
    async def hangman(
        self, 
        interaction: discord.Interaction,
        category: str = "random",
        difficulty: str = "medium"
    ):
        """Start a new hangman game with decorative elements."""
        try:
            # Check if user already has an active game
            if interaction.user.id in self.active_games:
                embed = discord.Embed(
                    title="⚠️ Game Already Active",
                    description="You already have an active hangman game! Finish it first or wait for it to timeout.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💡 Tip",
                    value="Use the buttons below your current game to continue playing.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Select word based on category and difficulty
            if category == "random":
                all_words = []
                for word_list in self.word_categories.values():
                    all_words.extend(word_list)
                available_words = all_words
            else:
                available_words = self.word_categories[category]
            
            # Filter by difficulty
            if difficulty == "easy":
                available_words = [word for word in available_words if 4 <= len(word) <= 6]
            elif difficulty == "medium":
                available_words = [word for word in available_words if 7 <= len(word) <= 9]
            elif difficulty == "hard":
                available_words = [word for word in available_words if len(word) >= 10]
            
            if not available_words:
                available_words = self.word_categories["animals"]  # Fallback
            
            word = random.choice(available_words)
            
            # Create new game
            game = HangmanGame(word, interaction.user)
            self.active_games[interaction.user.id] = game
            
            # Create initial embed
            embed = game.get_current_embed()
            embed.add_field(
                name="🎮 How to play:",
                value="Click the letter buttons below to guess!\nYou have **6** wrong guesses before the game ends.",
                inline=False
            )
            
            # Create letter buttons
            view = HangmanView(game, self)
            
            await interaction.response.send_message(embed=embed, view=view)
            
            # Schedule game cleanup after 10 minutes
            await asyncio.sleep(600)  # 10 minutes
            if interaction.user.id in self.active_games:
                del self.active_games[interaction.user.id]
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Game Error",
                description="An error occurred while starting the hangman game.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in hangman command: {e}", exc_info=True)

class HangmanView(discord.ui.View):
    """Interactive view with letter buttons for hangman game."""
    
    def __init__(self, game: HangmanGame, cog):
        super().__init__(timeout=300)  # 5 minute timeout
        self.game = game
        self.cog = cog
        
        # Create letter buttons (A-Z)
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, letter in enumerate(letters):
            button = LetterButton(letter, i // 5)  # 5 letters per row
            self.add_item(button)
    
    async def on_timeout(self):
        """Handle view timeout."""
        if self.game.player.id in self.cog.active_games:
            del self.cog.active_games[self.game.player.id]
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        embed = discord.Embed(
            title="⏰ Game Timeout",
            description="The hangman game has timed out due to inactivity.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="💡 The word was:",
            value=f"**{self.game.word}**",
            inline=False
        )
        
        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass

class LetterButton(discord.ui.Button):
    """Individual letter button for hangman game."""
    
    def __init__(self, letter: str, row: int):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=letter,
            row=row
        )
        self.letter = letter
    
    async def callback(self, interaction: discord.Interaction):
        """Handle letter button press."""
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
            result = game.guess_letter(self.letter)
            
            # Disable this button
            self.disabled = True
            self.style = discord.ButtonStyle.danger if result in ["wrong", "already_guessed"] else discord.ButtonStyle.success
            
            # Update embed
            embed = game.get_current_embed()
            
            # Add result message
            if result == "already_guessed":
                embed.add_field(
                    name="⚠️ Already Guessed",
                    value=f"You already guessed **{self.letter}**!",
                    inline=False
                )
            elif result == "correct":
                embed.add_field(
                    name="✅ Good Guess!",
                    value=f"**{self.letter}** is in the word!",
                    inline=False
                )
            elif result == "wrong":
                embed.add_field(
                    name="❌ Wrong Letter",
                    value=f"**{self.letter}** is not in the word.",
                    inline=False
                )
            elif result == "won":
                embed.add_field(
                    name="🎊 Amazing!",
                    value=f"**{self.letter}** completed the word!",
                    inline=False
                )
                # Disable all buttons
                for item in view.children:
                    item.disabled = True
                # Remove from active games
                if game.player.id in view.cog.active_games:
                    del view.cog.active_games[game.player.id]
            elif result == "lost":
                embed.add_field(
                    name="💀 Game Over",
                    value=f"**{self.letter}** was wrong. You've been hanged!",
                    inline=False
                )
                # Disable all buttons
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
            logging.error(f"Error in hangman button callback: {e}", exc_info=True)

# Setup functions
async def setup(bot):
    """Setup function to add the HangmanCommand cog to the bot."""
    await bot.add_cog(HangmanCommand(bot))
    logging.info("Hangman command loaded successfully")

def add_hangman_command(bot):
    """Alternative setup function for manual integration."""
    hangman_cog = HangmanCommand(bot)
    
    @bot.tree.command(name="hangman", description="🎪 Start an advanced hangman word guessing game")
    @app_commands.describe(
        category="Choose a word category (optional)",
        difficulty="Choose difficulty level (optional)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="🐾 Animals", value="animals"),
        app_commands.Choice(name="🌍 Countries", value="countries"),
        app_commands.Choice(name="🍕 Foods", value="foods"),
        app_commands.Choice(name="📱 Objects", value="objects"),
        app_commands.Choice(name="🎲 Random", value="random")
    ])
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="😊 Easy (4-6 letters)", value="easy"),
        app_commands.Choice(name="😐 Medium (7-9 letters)", value="medium"),
        app_commands.Choice(name="😤 Hard (10+ letters)", value="hard")
    ])
    async def hangman(
        interaction: discord.Interaction,
        category: str = "random",
        difficulty: str = "medium"
    ):
        await hangman_cog.hangman(interaction, category, difficulty)
    
    logging.info("Hangman command added successfully")
import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from datetime import datetime
import asyncio

class Connect4Game:
    """Connect 4 game logic"""
    
    def __init__(self, player1, player2):
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.winner = None
        self.game_over = False
        self.moves = 0
        
        # Visual representations
        self.emojis = {
            0: "⚫",  # Empty
            1: "🔴",  # Player 1 (Red)
            2: "🟡"   # Player 2 (Yellow)
        }
        
        self.column_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
    
    def drop_piece(self, column, player_num):
        """Drop a piece in the specified column"""
        if column < 0 or column > 6:
            return False
        
        if self.board[0][column] != 0:
            return False  # Column is full
        
        # Find the lowest empty row
        for row in range(5, -1, -1):
            if self.board[row][column] == 0:
                self.board[row][column] = player_num
                self.moves += 1
                return True
        
        return False
    
    def check_winner(self):
        """Check if there's a winner"""
        # Check all possible winning combinations
        for row in range(6):
            for col in range(7):
                if self.board[row][col] != 0:
                    player = self.board[row][col]
                    
                    # Check horizontal
                    if col <= 3:
                        if all(self.board[row][col + i] == player for i in range(4)):
                            return player
                    
                    # Check vertical
                    if row <= 2:
                        if all(self.board[row + i][col] == player for i in range(4)):
                            return player
                    
                    # Check diagonal (top-left to bottom-right)
                    if row <= 2 and col <= 3:
                        if all(self.board[row + i][col + i] == player for i in range(4)):
                            return player
                    
                    # Check diagonal (top-right to bottom-left)
                    if row <= 2 and col >= 3:
                        if all(self.board[row + i][col - i] == player for i in range(4)):
                            return player
        
        return None
    
    def is_board_full(self):
        """Check if the board is full"""
        return all(self.board[0][col] != 0 for col in range(7))
    
    def get_board_display(self):
        """Get a visual representation of the board"""
        display = "```\n"
        display += "  1   2   3   4   5   6   7  \n"
        display += "┌───┬───┬───┬───┬───┬───┬───┐\n"
        
        for row in range(6):
            display += "│"
            for col in range(7):
                piece = self.emojis[self.board[row][col]]
                display += f" {piece} │"
            display += "\n"
            if row < 5:
                display += "├───┼───┼───┼───┼───┼───┼───┤\n"
        
        display += "└───┴───┴───┴───┴───┴───┴───┘\n```"
        return display
    
    def get_emoji_board(self):
        """Get emoji-only board representation"""
        board_str = ""
        # Column numbers
        board_str += "".join(self.column_numbers) + "\n"
        
        # Board rows
        for row in range(6):
            for col in range(7):
                board_str += self.emojis[self.board[row][col]]
            board_str += "\n"
        
        return board_str

class Connect4View(discord.ui.View):
    """Interactive Connect 4 game view"""
    
    def __init__(self, game, timeout=300):
        super().__init__(timeout=timeout)
        self.game = game
        
        # Add column buttons
        for i in range(7):
            button = discord.ui.Button(
                label=str(i + 1),
                style=discord.ButtonStyle.primary,
                emoji=game.column_numbers[i],
                custom_id=f"col_{i}"
            )
            button.callback = self.make_move_callback(i)
            self.add_item(button)
        
        # Add forfeit button
        forfeit_button = discord.ui.Button(
            label="Forfeit",
            style=discord.ButtonStyle.danger,
            emoji="🏳️"
        )
        forfeit_button.callback = self.forfeit_callback
        self.add_item(forfeit_button)
    
    def make_move_callback(self, column):
        """Create callback for column button"""
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.game.current_player:
                await interaction.response.send_message(
                    "❌ It's not your turn!",
                    ephemeral=True
                )
                return
            
            if self.game.game_over:
                await interaction.response.send_message(
                    "❌ Game is already over!",
                    ephemeral=True
                )
                return
            
            # Determine player number
            player_num = 1 if interaction.user == self.game.player1 else 2
            
            # Make the move
            if not self.game.drop_piece(column, player_num):
                await interaction.response.send_message(
                    "❌ That column is full! Choose another column.",
                    ephemeral=True
                )
                return
            
            # Check for winner
            winner = self.game.check_winner()
            if winner:
                self.game.winner = self.game.player1 if winner == 1 else self.game.player2
                self.game.game_over = True
            elif self.game.is_board_full():
                self.game.game_over = True
            
            # Switch turns
            if not self.game.game_over:
                self.game.current_player = self.game.player2 if self.game.current_player == self.game.player1 else self.game.player1
            
            # Update the embed
            embed = self.create_game_embed()
            
            if self.game.game_over:
                # Disable all buttons
                for item in self.children:
                    item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        return callback
    
    async def forfeit_callback(self, interaction: discord.Interaction):
        """Handle forfeit button"""
        if interaction.user not in [self.game.player1, self.game.player2]:
            await interaction.response.send_message(
                "❌ You're not playing in this game!",
                ephemeral=True
            )
            return
        
        # Set winner to the other player
        self.game.winner = self.game.player2 if interaction.user == self.game.player1 else self.game.player1
        self.game.game_over = True
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        embed = self.create_game_embed()
        embed.add_field(
            name="🏳️ Game Forfeited",
            value=f"{interaction.user.display_name} forfeited the game!",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    def create_game_embed(self):
        """Create the game embed"""
        if self.game.game_over:
            if self.game.winner:
                title = f"🎉 Connect 4 - {self.game.winner.display_name} Wins!"
                color = discord.Color.gold()
            else:
                title = "🤝 Connect 4 - It's a Tie!"
                color = discord.Color.blue()
        else:
            title = f"🔴🟡 Connect 4 - {self.game.current_player.display_name}'s Turn"
            color = discord.Color.red() if self.game.current_player == self.game.player1 else discord.Color.gold()
        
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Add board
        embed.add_field(
            name="🎯 Game Board",
            value=self.game.get_emoji_board(),
            inline=False
        )
        
        # Add players info
        player_info = f"🔴 **{self.game.player1.display_name}** (Red)\n🟡 **{self.game.player2.display_name}** (Yellow)"
        embed.add_field(
            name="👥 Players",
            value=player_info,
            inline=True
        )
        
        # Add game stats
        stats = f"**Moves:** {self.game.moves}\n**Turn:** {'🔴' if self.game.current_player == self.game.player1 else '🟡'}"
        if not self.game.game_over:
            stats += f"\n**Current Player:** {self.game.current_player.display_name}"
        
        embed.add_field(
            name="📊 Game Stats",
            value=stats,
            inline=True
        )
        
        if not self.game.game_over:
            embed.add_field(
                name="🎮 How to Play",
                value="Click a column number to drop your piece!\nGet 4 in a row to win!",
                inline=False
            )
        
        embed.set_footer(text="Connect 4 Game • Click column buttons to play!")
        
        return embed
    
    async def on_timeout(self):
        """Handle view timeout"""
        for item in self.children:
            item.disabled = True

class Connect4Command(commands.Cog):
    """Connect 4 game command"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.active_games = {}  # Store active games by channel
    
    @app_commands.command(name="connect4", description="Start a Connect 4 game with another player!")
    @app_commands.describe(opponent="The player you want to challenge to Connect 4")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def connect4(self, interaction: discord.Interaction, opponent: discord.Member):
        """
        Start a Connect 4 game
        
        Args:
            interaction: Discord interaction object
            opponent: The opponent to challenge
        """
        try:
            # Validation checks
            if opponent.bot:
                await interaction.response.send_message(
                    "❌ You can't play Connect 4 with a bot!",
                    ephemeral=True
                )
                return
            
            if opponent == interaction.user:
                await interaction.response.send_message(
                    "❌ You can't play Connect 4 with yourself!",
                    ephemeral=True
                )
                return
            
            channel_id = interaction.channel.id
            if channel_id in self.active_games:
                await interaction.response.send_message(
                    "❌ There's already an active Connect 4 game in this channel! Wait for it to finish.",
                    ephemeral=True
                )
                return
            
            # Create the game
            game = Connect4Game(interaction.user, opponent)
            view = Connect4View(game)
            
            # Create initial embed
            embed = discord.Embed(
                title="🎮 Connect 4 Challenge!",
                description=f"🔴 **{interaction.user.display_name}** challenges 🟡 **{opponent.display_name}** to Connect 4!",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🎯 Game Rules",
                value="• Drop pieces by clicking column numbers\n• Get 4 pieces in a row (horizontal, vertical, or diagonal) to win\n• 🔴 Red goes first\n• Click 'Forfeit' to give up",
                inline=False
            )
            
            embed.add_field(
                name="👥 Players",
                value=f"🔴 {interaction.user.display_name} (Red)\n🟡 {opponent.display_name} (Yellow)",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Game Info",
                value="• 5 minute timeout\n• Click buttons to play\n• Have fun!",
                inline=True
            )
            
            embed.set_footer(text="Connect 4 Challenge • The game will start when both players are ready!")
            
            # Store the game
            self.active_games[channel_id] = game
            
            # Send challenge message
            await interaction.response.send_message(
                content=f"{opponent.mention}, you've been challenged to Connect 4!",
                embed=embed,
                view=view
            )
            
            # Wait a moment then start the game
            await asyncio.sleep(2)
            
            # Update to show the actual game board
            game_embed = view.create_game_embed()
            try:
                await interaction.edit_original_response(
                    content=f"🎮 **Connect 4 Game Started!** {game.player1.mention} vs {game.player2.mention}",
                    embed=game_embed,
                    view=view
                )
            except:
                pass
            
            # Clean up game when view times out
            def cleanup_callback():
                if channel_id in self.active_games:
                    del self.active_games[channel_id]
            
            view.on_timeout = cleanup_callback
            
        except discord.HTTPException as e:
            self.logger.error(f"HTTP Exception in connect4 command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Failed to start Connect 4 game due to Discord API error.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Failed to start Connect 4 game due to Discord API error.",
                        ephemeral=True
                    )
            except:
                pass
        except Exception as e:
            import traceback
            self.logger.error(f"Unexpected error in connect4 command: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An unexpected error occurred while starting Connect 4 game.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An unexpected error occurred while starting Connect 4 game.",
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
                        f"⏰ Connect 4 is on cooldown! Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⏰ Connect 4 is on cooldown! Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
            except:
                pass
        else:
            self.logger.error(f"Command error: {error}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred while executing the Connect 4 command.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An error occurred while executing the Connect 4 command.",
                        ephemeral=True
                    )
            except:
                pass

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(Connect4Command(bot))
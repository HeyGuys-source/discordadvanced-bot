import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import aiohttp
import json
from datetime import datetime
from utils.helpers import create_embed, create_success_embed, create_error_embed
from typing import Optional

class Connect4Game:
    def __init__(self, player1: discord.Member, player2: discord.Member):
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.game_over = False
        self.winner = None
    
    def drop_piece(self, column: int, player_num: int) -> bool:
        """Drop a piece in the specified column"""
        if column < 0 or column > 6:
            return False
        
        for row in range(5, -1, -1):
            if self.board[row][column] == 0:
                self.board[row][column] = player_num
                return True
        return False
    
    def check_winner(self) -> Optional[int]:
        """Check if there's a winner"""
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if (self.board[row][col] != 0 and 
                    self.board[row][col] == self.board[row][col+1] == 
                    self.board[row][col+2] == self.board[row][col+3]):
                    return self.board[row][col]
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if (self.board[row][col] != 0 and 
                    self.board[row][col] == self.board[row+1][col] == 
                    self.board[row+2][col] == self.board[row+3][col]):
                    return self.board[row][col]
        
        # Check diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                if (self.board[row][col] != 0 and 
                    self.board[row][col] == self.board[row+1][col+1] == 
                    self.board[row+2][col+2] == self.board[row+3][col+3]):
                    return self.board[row][col]
        
        # Check diagonal (top-right to bottom-left)
        for row in range(3):
            for col in range(3, 7):
                if (self.board[row][col] != 0 and 
                    self.board[row][col] == self.board[row+1][col-1] == 
                    self.board[row+2][col-2] == self.board[row+3][col-3]):
                    return self.board[row][col]
        
        return None
    
    def get_board_display(self) -> str:
        """Get a visual representation of the board"""
        display = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣\n"
        for row in self.board:
            for cell in row:
                if cell == 0:
                    display += "⚫"
                elif cell == 1:
                    display += "🔴"
                else:
                    display += "🟡"
            display += "\n"
        return display

class TicTacToeGame:
    def __init__(self, player1: discord.Member, player2: discord.Member):
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [0] * 9  # 0 = empty, 1 = player1, 2 = player2
        self.game_over = False
        self.winner = None
    
    def make_move(self, position: int, player_num: int) -> bool:
        """Make a move at the specified position"""
        if position < 0 or position > 8 or self.board[position] != 0:
            return False
        
        self.board[position] = player_num
        return True
    
    def check_winner(self) -> Optional[int]:
        """Check if there's a winner"""
        winning_positions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]  # Diagonals
        ]
        
        for positions in winning_positions:
            if (self.board[positions[0]] != 0 and 
                self.board[positions[0]] == self.board[positions[1]] == self.board[positions[2]]):
                return self.board[positions[0]]
        
        return None
    
    def is_draw(self) -> bool:
        """Check if the game is a draw"""
        return 0 not in self.board
    
    def get_board_display(self) -> str:
        """Get a visual representation of the board"""
        symbols = ["⬜", "❌", "⭕"]
        display = ""
        for i in range(0, 9, 3):
            display += "".join(symbols[self.board[j]] for j in range(i, i + 3)) + "\n"
        return display

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connect4_games = {}
        self.tictactoe_games = {}
        self.trivia_questions = []
    
    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        """Magic 8-ball command"""
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        
        response = random.choice(responses)
        embed = create_embed(
            "🎱 Magic 8-Ball",
            f"**Question:** {question}\n**Answer:** {response}",
            color=0x000000
        )
        embed.set_footer(text=f"Asked by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🟡"
        
        embed = create_embed(
            f"{emoji} Coin Flip",
            f"The coin landed on **{result}**!",
            color=0xffd700
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="dice", description="Roll dice")
    async def dice(self, interaction: discord.Interaction, sides: int = 6, count: int = 1):
        """Roll dice"""
        if count < 1 or count > 10:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You can roll 1-10 dice at once!"),
                ephemeral=True
            )
            return
        
        if sides < 2 or sides > 100:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Dice must have 2-100 sides!"),
                ephemeral=True
            )
            return
        
        results = [random.randint(1, sides) for _ in range(count)]
        total = sum(results)
        
        embed = create_embed(
            "🎲 Dice Roll",
            f"Rolling {count}d{sides}\n**Results:** {', '.join(map(str, results))}\n**Total:** {total}",
            color=0xff6b6b
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock", value="rock"),
        app_commands.Choice(name="Paper", value="paper"),
        app_commands.Choice(name="Scissors", value="scissors")
    ])
    async def rock_paper_scissors(self, interaction: discord.Interaction, choice: app_commands.Choice[str]):
        """Rock Paper Scissors game"""
        user_choice = choice.value
        bot_choice = random.choice(["rock", "paper", "scissors"])
        
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        if user_choice == bot_choice:
            result = "It's a tie!"
            color = 0xffff00
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            color = 0x00ff00
        else:
            result = "I win!"
            color = 0xff0000
        
        embed = create_embed(
            "🎮 Rock Paper Scissors",
            f"You chose: {emojis[user_choice]} {user_choice.title()}\n"
            f"I chose: {emojis[bot_choice]} {bot_choice.title()}\n\n**{result}**",
            color=color
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="randomnumber", description="Generate a random number")
    async def random_number(self, interaction: discord.Interaction, minimum: int = 1, maximum: int = 100):
        """Generate a random number"""
        if minimum >= maximum:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Minimum must be less than maximum!"),
                ephemeral=True
            )
            return
        
        if abs(maximum - minimum) > 1000000:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Range too large! Max range is 1,000,000"),
                ephemeral=True
            )
            return
        
        number = random.randint(minimum, maximum)
        
        embed = create_embed(
            "🎲 Random Number",
            f"Random number between {minimum:,} and {maximum:,}:\n**{number:,}**",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="choose", description="Choose randomly from a list of options")
    async def choose(self, interaction: discord.Interaction, options: str):
        """Choose from options separated by commas"""
        option_list = [option.strip() for option in options.split(',') if option.strip()]
        
        if len(option_list) < 2:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Please provide at least 2 options separated by commas!"),
                ephemeral=True
            )
            return
        
        if len(option_list) > 20:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Too many options! Maximum is 20."),
                ephemeral=True
            )
            return
        
        choice = random.choice(option_list)
        
        embed = create_embed(
            "🎯 Random Choice",
            f"**Options:** {', '.join(option_list)}\n**I choose:** {choice}",
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="connect4", description="Start a Connect 4 game")
    async def connect4(self, interaction: discord.Interaction, opponent: discord.Member):
        """Start a Connect 4 game"""
        if opponent.bot:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You can't play against bots!"),
                ephemeral=True
            )
            return
        
        if opponent == interaction.user:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You can't play against yourself!"),
                ephemeral=True
            )
            return
        
        game_id = f"{interaction.user.id}_{opponent.id}"
        if game_id in self.connect4_games:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You already have a game running with this user!"),
                ephemeral=True
            )
            return
        
        game = Connect4Game(interaction.user, opponent)
        self.connect4_games[game_id] = game
        
        embed = create_embed(
            "🔴 Connect 4",
            f"{interaction.user.mention} vs {opponent.mention}\n\n"
            f"{game.get_board_display()}\n"
            f"🔴 {game.current_player.mention}'s turn!\n"
            f"Use `/c4drop <column>` to drop a piece (1-7)",
            color=0xff0000
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="c4drop", description="Drop a piece in Connect 4")
    async def c4drop(self, interaction: discord.Interaction, column: int):
        """Drop a piece in Connect 4"""
        if column < 1 or column > 7:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Column must be between 1 and 7!"),
                ephemeral=True
            )
            return
        
        # Find the game
        game = None
        game_id = None
        for gid, g in self.connect4_games.items():
            if interaction.user in [g.player1, g.player2]:
                game = g
                game_id = gid
                break
        
        if not game:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You're not in any Connect 4 game!"),
                ephemeral=True
            )
            return
        
        if game.current_player != interaction.user:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "It's not your turn!"),
                ephemeral=True
            )
            return
        
        player_num = 1 if interaction.user == game.player1 else 2
        
        if not game.drop_piece(column - 1, player_num):
            await interaction.response.send_message(
                embed=create_error_embed("Error", "That column is full!"),
                ephemeral=True
            )
            return
        
        winner = game.check_winner()
        if winner:
            game.game_over = True
            game.winner = game.player1 if winner == 1 else game.player2
            
            embed = create_embed(
                "🎉 Connect 4 - Game Over!",
                f"{game.winner.mention} wins!\n\n{game.get_board_display()}",
                color=0x00ff00
            )
            
            del self.connect4_games[game_id]
        else:
            # Check for draw
            if all(game.board[0][col] != 0 for col in range(7)):
                game.game_over = True
                embed = create_embed(
                    "🤝 Connect 4 - Draw!",
                    f"It's a draw!\n\n{game.get_board_display()}",
                    color=0xffff00
                )
                del self.connect4_games[game_id]
            else:
                # Continue game
                game.current_player = game.player2 if game.current_player == game.player1 else game.player1
                embed = create_embed(
                    "🔴 Connect 4",
                    f"{game.player1.mention} vs {game.player2.mention}\n\n"
                    f"{game.get_board_display()}\n"
                    f"{'🔴' if game.current_player == game.player1 else '🟡'} {game.current_player.mention}'s turn!",
                    color=0xff0000
                )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="tictactoe", description="Start a Tic Tac Toe game")
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.Member):
        """Start a Tic Tac Toe game"""
        if opponent.bot:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You can't play against bots!"),
                ephemeral=True
            )
            return
        
        if opponent == interaction.user:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You can't play against yourself!"),
                ephemeral=True
            )
            return
        
        game_id = f"{interaction.user.id}_{opponent.id}"
        if game_id in self.tictactoe_games:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You already have a game running with this user!"),
                ephemeral=True
            )
            return
        
        game = TicTacToeGame(interaction.user, opponent)
        self.tictactoe_games[game_id] = game
        
        embed = create_embed(
            "❌ Tic Tac Toe",
            f"{interaction.user.mention} (❌) vs {opponent.mention} (⭕)\n\n"
            f"{game.get_board_display()}\n"
            f"❌ {game.current_player.mention}'s turn!\n"
            f"Use `/tttmove <position>` (1-9) to make a move",
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="tttmove", description="Make a move in Tic Tac Toe")
    async def ttt_move(self, interaction: discord.Interaction, position: int):
        """Make a move in Tic Tac Toe"""
        if position < 1 or position > 9:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Position must be between 1 and 9!"),
                ephemeral=True
            )
            return
        
        # Find the game
        game = None
        game_id = None
        for gid, g in self.tictactoe_games.items():
            if interaction.user in [g.player1, g.player2]:
                game = g
                game_id = gid
                break
        
        if not game:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You're not in any Tic Tac Toe game!"),
                ephemeral=True
            )
            return
        
        if game.current_player != interaction.user:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "It's not your turn!"),
                ephemeral=True
            )
            return
        
        player_num = 1 if interaction.user == game.player1 else 2
        
        if not game.make_move(position - 1, player_num):
            await interaction.response.send_message(
                embed=create_error_embed("Error", "That position is already taken!"),
                ephemeral=True
            )
            return
        
        winner = game.check_winner()
        if winner:
            game.game_over = True
            game.winner = game.player1 if winner == 1 else game.player2
            
            embed = create_embed(
                "🎉 Tic Tac Toe - Game Over!",
                f"{game.winner.mention} wins!\n\n{game.get_board_display()}",
                color=0x00ff00
            )
            
            del self.tictactoe_games[game_id]
        elif game.is_draw():
            game.game_over = True
            embed = create_embed(
                "🤝 Tic Tac Toe - Draw!",
                f"It's a draw!\n\n{game.get_board_display()}",
                color=0xffff00
            )
            del self.tictactoe_games[game_id]
        else:
            # Continue game
            game.current_player = game.player2 if game.current_player == game.player1 else game.player1
            embed = create_embed(
                "❌ Tic Tac Toe",
                f"{game.player1.mention} (❌) vs {game.player2.mention} (⭕)\n\n"
                f"{game.get_board_display()}\n"
                f"{'❌' if game.current_player == game.player1 else '⭕'} {game.current_player.mention}'s turn!",
                color=0x3498db
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        """Get a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Why don't skeletons fight each other? They don't have the guts.",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "I'm reading a book about anti-gravity. It's impossible to put down!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
            "I invented a new word: Plagiarism!",
            "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks!",
            "Why don't robots ever panic? They have nerves of steel!",
            "What did the ocean say to the beach? Nothing, it just waved!",
            "Why do fish live in salt water? Because pepper makes them sneeze!",
            "What's orange and sounds like a parrot? A carrot!"
        ]
        
        joke = random.choice(jokes)
        
        embed = create_embed(
            "😂 Random Joke",
            joke,
            color=0xffd700
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="meme", description="Get a random meme")
    async def meme(self, interaction: discord.Interaction):
        """Get a random meme"""
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://meme-api.herokuapp.com/gimme') as response:
                    if response.status == 200:
                        data = await response.json()
                        embed = create_embed(
                            data['title'],
                            f"**r/{data['subreddit']}** • {data['ups']} upvotes",
                            color=0xff4500
                        )
                        embed.set_image(url=data['url'])
                        embed.set_footer(text=f"Posted by u/{data['author']}")
                        await interaction.followup.send(embed=embed)
                    else:
                        raise Exception("API Error")
        except:
            embed = create_error_embed(
                "Meme Error",
                "Couldn't fetch a meme right now. Try again later!"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="quote", description="Get an inspirational quote")
    async def quote(self, interaction: discord.Interaction):
        """Get an inspirational quote"""
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
            ("Life is what happens to you while you're busy making other plans.", "John Lennon"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
            ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
            ("Don't let yesterday take up too much of today.", "Will Rogers"),
            ("You learn more from failure than from success.", "Unknown"),
            ("If you are working on something exciting that you really care about, you don't have to be pushed.", "Steve Jobs"),
            ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill")
        ]
        
        quote, author = random.choice(quotes)
        
        embed = create_embed(
            "💭 Inspirational Quote",
            f"\"{quote}\"\n\n— **{author}**",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="fact", description="Get a random fun fact")
    async def fact(self, interaction: discord.Interaction):
        """Get a random fun fact"""
        facts = [
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
            "A group of flamingos is called a 'flamboyance'.",
            "Octopuses have three hearts and blue blood.",
            "Bananas are berries, but strawberries aren't.",
            "A single cloud can weigh more than a million pounds.",
            "There are more possible games of chess than atoms in the observable universe.",
            "Dolphins have names for each other.",
            "A shrimp's heart is in its head.",
            "It's impossible to hum while holding your nose closed.",
            "The human brain uses about 20% of the body's total energy.",
            "A day on Venus is longer than its year.",
            "Wombat poop is cube-shaped.",
            "There are more ways to arrange a deck of cards than there are atoms on Earth.",
            "Sharks are older than trees.",
            "The shortest war in history lasted only 38-45 minutes."
        ]
        
        fact = random.choice(facts)
        
        embed = create_embed(
            "🧠 Fun Fact",
            fact,
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="flip", description="Flip text upside down")
    async def flip_text(self, interaction: discord.Interaction, text: str):
        """Flip text upside down"""
        if len(text) > 200:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Text too long! Maximum 200 characters."),
                ephemeral=True
            )
            return
        
        flip_map = {
            'a': 'ɐ', 'b': 'q', 'c': 'ɔ', 'd': 'p', 'e': 'ǝ', 'f': 'ɟ', 'g': 'ƃ', 'h': 'ɥ',
            'i': 'ᴉ', 'j': 'ɾ', 'k': 'ʞ', 'l': 'l', 'm': 'ɯ', 'n': 'u', 'o': 'o', 'p': 'd',
            'q': 'b', 'r': 'ɹ', 's': 's', 't': 'ʇ', 'u': 'n', 'v': 'ʌ', 'w': 'ʍ', 'x': 'x',
            'y': 'ʎ', 'z': 'z', 'A': '∀', 'B': 'ᗺ', 'C': 'Ɔ', 'D': 'ᗡ', 'E': 'Ǝ', 'F': 'ᖴ',
            'G': 'פ', 'H': 'H', 'I': 'I', 'J': 'ſ', 'K': 'ʞ', 'L': '˥', 'M': 'W', 'N': 'N',
            'O': 'O', 'P': 'Ԁ', 'Q': 'Q', 'R': 'ᴿ', 'S': 'S', 'T': '┴', 'U': '∩', 'V': 'Λ',
            'W': 'M', 'X': 'X', 'Y': '⅄', 'Z': 'Z', '1': 'Ɩ', '2': 'ᄅ', '3': 'Ɛ', '4': 'ㄣ',
            '5': 'ϛ', '6': '9', '7': 'ㄥ', '8': '8', '9': '6', '0': '0', '.': '˙', ',': "'",
            '?': '¿', '!': '¡', '"': '„', "'": '‛', '(': ')', ')': '(', '[': ']', ']': '[',
            '{': '}', '}': '{', '<': '>', '>': '<', '&': '⅋', '_': '‾'
        }
        
        flipped = ''.join(flip_map.get(char, char) for char in text)[::-1]
        
        embed = create_embed(
            "🔄 Flipped Text",
            f"**Original:** {text}\n**Flipped:** {flipped}",
            color=0xe74c3c
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="reverse", description="Reverse text")
    async def reverse_text(self, interaction: discord.Interaction, text: str):
        """Reverse text"""
        if len(text) > 200:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Text too long! Maximum 200 characters."),
                ephemeral=True
            )
            return
        
        reversed_text = text[::-1]
        
        embed = create_embed(
            "↩️ Reversed Text",
            f"**Original:** {text}\n**Reversed:** {reversed_text}",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ascii", description="Convert text to ASCII art")
    async def ascii_art(self, interaction: discord.Interaction, text: str):
        """Convert text to ASCII art"""
        if len(text) > 10:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "Text too long! Maximum 10 characters."),
                ephemeral=True
            )
            return
        
        # Simple ASCII art mapping
        ascii_chars = {
            'A': ['  █  ', ' █ █ ', '█████', '█   █', '█   █'],
            'B': ['████ ', '█   █', '████ ', '█   █', '████ '],
            'C': [' ████', '█    ', '█    ', '█    ', ' ████'],
            'D': ['████ ', '█   █', '█   █', '█   █', '████ '],
            'E': ['█████', '█    ', '███  ', '█    ', '█████'],
            'F': ['█████', '█    ', '███  ', '█    ', '█    '],
            'G': [' ████', '█    ', '█ ███', '█   █', ' ████'],
            'H': ['█   █', '█   █', '█████', '█   █', '█   █'],
            'I': ['█████', '  █  ', '  █  ', '  █  ', '█████'],
            'J': ['█████', '    █', '    █', '█   █', ' ████'],
            'K': ['█   █', '█  █ ', '███  ', '█  █ ', '█   █'],
            'L': ['█    ', '█    ', '█    ', '█    ', '█████'],
            'M': ['█   █', '██ ██', '█ █ █', '█   █', '█   █'],
            'N': ['█   █', '██  █', '█ █ █', '█  ██', '█   █'],
            'O': [' ███ ', '█   █', '█   █', '█   █', ' ███ '],
            'P': ['████ ', '█   █', '████ ', '█    ', '█    '],
            'Q': [' ███ ', '█   █', '█ █ █', '█  ██', ' ████'],
            'R': ['████ ', '█   █', '████ ', '█  █ ', '█   █'],
            'S': [' ████', '█    ', ' ███ ', '    █', '████ '],
            'T': ['█████', '  █  ', '  █  ', '  █  ', '  █  '],
            'U': ['█   █', '█   █', '█   █', '█   █', ' ███ '],
            'V': ['█   █', '█   █', '█   █', ' █ █ ', '  █  '],
            'W': ['█   █', '█   █', '█ █ █', '██ ██', '█   █'],
            'X': ['█   █', ' █ █ ', '  █  ', ' █ █ ', '█   █'],
            'Y': ['█   █', ' █ █ ', '  █  ', '  █  ', '  █  '],
            'Z': ['█████', '   █ ', '  █  ', ' █   ', '█████'],
            ' ': ['     ', '     ', '     ', '     ', '     ']
        }
        
        text = text.upper()
        lines = ['', '', '', '', '']
        
        for char in text:
            if char in ascii_chars:
                for i in range(5):
                    lines[i] += ascii_chars[char][i] + ' '
            else:
                for i in range(5):
                    lines[i] += '     '
        
        ascii_art = '\n'.join(lines)
        
        if len(ascii_art) > 2000:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "ASCII art too long!"),
                ephemeral=True
            )
            return
        
        embed = create_embed(
            "🎨 ASCII Art",
            f"```\n{ascii_art}\n```",
            color=0x34495e
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from datetime import datetime
import asyncio

class RPSGame:
    """Rock Paper Scissors game logic"""
    
    def __init__(self, player1, player2=None):
        self.player1 = player1
        self.player2 = player2  # None for AI opponent
        self.player1_choice = None
        self.player2_choice = None
        self.winner = None
        self.result = None
        self.is_ai_game = player2 is None
        
        # Emoji mappings
        self.choices = {
            "rock": {"emoji": "🪨", "name": "Rock", "beats": "scissors"},
            "paper": {"emoji": "📄", "name": "Paper", "beats": "rock"},
            "scissors": {"emoji": "✂️", "name": "Scissors", "beats": "paper"}
        }
        
        # Fun AI personalities
        self.ai_personalities = [
            {"name": "Rocky", "favorite": "rock", "emoji": "🤖", "taunt": "I love rocks!"},
            {"name": "Papyrus", "favorite": "paper", "emoji": "📚", "taunt": "Paper beats all!"},
            {"name": "Snippy", "favorite": "scissors", "emoji": "✂️", "taunt": "Snip snap!"},
            {"name": "Randomizer", "favorite": None, "emoji": "🎲", "taunt": "Pure chaos!"}
        ]
        
        self.ai_personality = random.choice(self.ai_personalities)
    
    def make_ai_choice(self):
        """AI makes a choice based on personality"""
        if self.ai_personality["favorite"]:
            # AI has favorite but sometimes chooses randomly
            if random.random() < 0.6:  # 60% chance to pick favorite
                return self.ai_personality["favorite"]
        
        return random.choice(["rock", "paper", "scissors"])
    
    def determine_winner(self):
        """Determine the winner of the game"""
        if self.player1_choice == self.player2_choice:
            self.result = "tie"
            self.winner = None
        elif self.choices[self.player1_choice]["beats"] == self.player2_choice:
            self.result = "player1_wins"
            self.winner = self.player1
        else:
            self.result = "player2_wins"
            self.winner = self.player2 if not self.is_ai_game else "AI"

class RPSView(discord.ui.View):
    """Interactive Rock Paper Scissors view"""
    
    def __init__(self, game, timeout=60):
        super().__init__(timeout=timeout)
        self.game = game
        self.waiting_for = set([game.player1])
        if game.player2:
            self.waiting_for.add(game.player2)
        
        # Add choice buttons
        for choice, data in game.choices.items():
            button = discord.ui.Button(
                label=data["name"],
                emoji=data["emoji"],
                style=discord.ButtonStyle.primary,
                custom_id=f"rps_{choice}"
            )
            button.callback = self.make_choice_callback(choice)
            self.add_item(button)
    
    def make_choice_callback(self, choice):
        """Create callback for choice button"""
        async def callback(interaction: discord.Interaction):
            # Check if user is a player
            if self.game.is_ai_game:
                if interaction.user != self.game.player1:
                    await interaction.response.send_message(
                        "❌ You're not playing in this game!",
                        ephemeral=True
                    )
                    return
            else:
                if interaction.user not in [self.game.player1, self.game.player2]:
                    await interaction.response.send_message(
                        "❌ You're not playing in this game!",
                        ephemeral=True
                    )
                    return
            
            # Check if player already made a choice
            if interaction.user == self.game.player1 and self.game.player1_choice:
                await interaction.response.send_message(
                    f"❌ You already chose {self.game.choices[self.game.player1_choice]['emoji']} {self.game.choices[self.game.player1_choice]['name']}!",
                    ephemeral=True
                )
                return
            elif not self.game.is_ai_game and interaction.user == self.game.player2 and self.game.player2_choice:
                await interaction.response.send_message(
                    f"❌ You already chose {self.game.choices[self.game.player2_choice]['emoji']} {self.game.choices[self.game.player2_choice]['name']}!",
                    ephemeral=True
                )
                return
            
            # Make the choice
            if interaction.user == self.game.player1:
                self.game.player1_choice = choice
                self.waiting_for.discard(interaction.user)
            elif not self.game.is_ai_game:
                self.game.player2_choice = choice
                self.waiting_for.discard(interaction.user)
            
            # For AI games, make AI choice immediately
            if self.game.is_ai_game:
                self.game.player2_choice = self.game.make_ai_choice()
                self.waiting_for.clear()
            
            # Check if both players have chosen
            if not self.waiting_for:
                # Both choices made, determine winner
                self.game.determine_winner()
                
                # Disable all buttons
                for item in self.children:
                    item.disabled = True
                
                # Show results
                embed = self.create_results_embed()
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                # Still waiting for other player
                embed = self.create_waiting_embed()
                await interaction.response.edit_message(embed=embed, view=self)
        
        return callback
    
    def create_waiting_embed(self):
        """Create embed while waiting for players"""
        embed = discord.Embed(
            title="🪨📄✂️ Rock Paper Scissors",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if self.game.is_ai_game:
            embed.description = f"🎮 **{self.game.player1.display_name}** vs **{self.game.ai_personality['name']}** {self.game.ai_personality['emoji']}"
            
            if self.game.player1_choice:
                embed.add_field(
                    name="✅ Choice Made!",
                    value=f"{self.game.player1.display_name} has made their choice!\nWaiting for AI...",
                    inline=False
                )
        else:
            embed.description = f"🎮 **{self.game.player1.display_name}** vs **{self.game.player2.display_name}**"
            
            status = []
            if self.game.player1_choice:
                status.append(f"✅ {self.game.player1.display_name} - Ready!")
            else:
                status.append(f"⏳ {self.game.player1.display_name} - Waiting...")
            
            if self.game.player2_choice:
                status.append(f"✅ {self.game.player2.display_name} - Ready!")
            else:
                status.append(f"⏳ {self.game.player2.display_name} - Waiting...")
            
            embed.add_field(
                name="🎯 Player Status",
                value="\n".join(status),
                inline=False
            )
        
        embed.add_field(
            name="🎮 How to Play",
            value="🪨 Rock beats Scissors\n📄 Paper beats Rock\n✂️ Scissors beats Paper",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Game Info",
            value="• 1 minute timeout\n• Choose wisely!\n• May the best choice win!",
            inline=True
        )
        
        embed.set_footer(text="Rock Paper Scissors • Choose your weapon!")
        
        return embed
    
    def create_results_embed(self):
        """Create embed showing game results"""
        if self.game.result == "tie":
            title = "🤝 It's a Tie!"
            color = discord.Color.blue()
        elif self.game.result == "player1_wins":
            title = f"🎉 {self.game.player1.display_name} Wins!"
            color = discord.Color.green()
        else:
            if self.game.is_ai_game:
                title = f"🤖 {self.game.ai_personality['name']} Wins!"
                color = discord.Color.red()
            else:
                title = f"🎉 {self.game.player2.display_name} Wins!"
                color = discord.Color.green()
        
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Show choices
        p1_choice = self.game.choices[self.game.player1_choice]
        p2_choice = self.game.choices[self.game.player2_choice]
        
        if self.game.is_ai_game:
            embed.description = f"🎮 **{self.game.player1.display_name}** vs **{self.game.ai_personality['name']}** {self.game.ai_personality['emoji']}"
            
            choices_text = f"**{self.game.player1.display_name}:** {p1_choice['emoji']} {p1_choice['name']}\n"
            choices_text += f"**{self.game.ai_personality['name']}:** {p2_choice['emoji']} {p2_choice['name']}"
        else:
            embed.description = f"🎮 **{self.game.player1.display_name}** vs **{self.game.player2.display_name}**"
            
            choices_text = f"**{self.game.player1.display_name}:** {p1_choice['emoji']} {p1_choice['name']}\n"
            choices_text += f"**{self.game.player2.display_name}:** {p2_choice['emoji']} {p2_choice['name']}"
        
        embed.add_field(
            name="⚔️ The Showdown",
            value=choices_text,
            inline=False
        )
        
        # Explain the result
        if self.game.result == "tie":
            explanation = f"Both players chose {p1_choice['name']}! Perfect minds think alike! 🤝"
        elif self.game.result == "player1_wins":
            explanation = f"{p1_choice['name']} beats {p2_choice['name']}! 🎯"
        else:
            explanation = f"{p2_choice['name']} beats {p1_choice['name']}! 🎯"
        
        embed.add_field(
            name="📖 Result Explanation",
            value=explanation,
            inline=False
        )
        
        # Add some fun facts or quotes
        fun_responses = [
            "Great game! 🎮",
            "The battle was legendary! ⚔️",
            "What an epic showdown! 🏆",
            "Perfectly executed! 👏",
            "The tension was real! 😤"
        ]
        
        if self.game.is_ai_game and self.game.result == "player2_wins":
            ai_victory_quotes = [
                f"'{self.game.ai_personality['taunt']}' - {self.game.ai_personality['name']}",
                f"{self.game.ai_personality['name']} predicted your move! 🤖",
                f"The AI rises! {self.game.ai_personality['emoji']}",
                f"{self.game.ai_personality['name']}'s strategy paid off!"
            ]
            embed.add_field(
                name="🤖 AI Comment",
                value=random.choice(ai_victory_quotes),
                inline=True
            )
        else:
            embed.add_field(
                name="🎊 Fun Fact",
                value=random.choice(fun_responses),
                inline=True
            )
        
        # Add statistics (simple)
        embed.add_field(
            name="📊 Quick Stats",
            value=f"**Game Duration:** {random.randint(3, 15)} seconds\n**Excitement Level:** {'🔥' * random.randint(3, 5)}",
            inline=True
        )
        
        embed.set_footer(text="Rock Paper Scissors • Thanks for playing!")
        
        return embed
    
    async def on_timeout(self):
        """Handle view timeout"""
        for item in self.children:
            item.disabled = True

class RPSGameCommand(commands.Cog):
    """Rock Paper Scissors game command"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @app_commands.command(name="rpsgame", description="Play Rock Paper Scissors against AI or another player!")
    @app_commands.describe(opponent="The player you want to challenge (leave empty to play against AI)")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def rpsgame(self, interaction: discord.Interaction, opponent: discord.Member = None):
        """
        Start a Rock Paper Scissors game
        
        Args:
            interaction: Discord interaction object
            opponent: Optional opponent (if None, plays against AI)
        """
        try:
            # Validation for human opponent
            if opponent:
                if opponent.bot:
                    await interaction.response.send_message(
                        "❌ You can't play Rock Paper Scissors with a bot! Leave the opponent field empty to play against AI instead.",
                        ephemeral=True
                    )
                    return
                
                if opponent == interaction.user:
                    await interaction.response.send_message(
                        "❌ You can't play Rock Paper Scissors with yourself! Leave the opponent field empty to play against AI.",
                        ephemeral=True
                    )
                    return
            
            # Create the game
            game = RPSGame(interaction.user, opponent)
            view = RPSView(game)
            
            # Create initial embed
            if game.is_ai_game:
                embed = discord.Embed(
                    title="🤖 Rock Paper Scissors vs AI!",
                    description=f"🎮 **{interaction.user.display_name}** challenges **{game.ai_personality['name']}** {game.ai_personality['emoji']}!",
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="🤖 Your AI Opponent",
                    value=f"**Name:** {game.ai_personality['name']} {game.ai_personality['emoji']}\n**Personality:** {game.ai_personality['taunt']}\n**Favorite:** {game.ai_personality['favorite'] or 'Random'} {'🎲' if not game.ai_personality['favorite'] else game.choices[game.ai_personality['favorite']]['emoji']}",
                    inline=False
                )
                
                content = f"🎮 **{interaction.user.display_name}**, choose your weapon against {game.ai_personality['name']}!"
            else:
                embed = discord.Embed(
                    title="⚔️ Rock Paper Scissors Challenge!",
                    description=f"🎮 **{interaction.user.display_name}** challenges **{opponent.display_name}** to Rock Paper Scissors!",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="👥 Players",
                    value=f"🥊 {interaction.user.display_name}\n🥊 {opponent.display_name}",
                    inline=True
                )
                
                content = f"{opponent.mention}, you've been challenged to Rock Paper Scissors!"
            
            embed.add_field(
                name="🎯 Game Rules",
                value="🪨 **Rock** beats Scissors\n📄 **Paper** beats Rock\n✂️ **Scissors** beats Paper",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Game Info",
                value="• 1 minute to choose\n• Choose wisely!\n• Best of luck! 🍀",
                inline=True
            )
            
            embed.set_footer(text="Rock Paper Scissors • Click your choice below!")
            
            await interaction.response.send_message(
                content=content,
                embed=embed,
                view=view
            )
            
        except discord.HTTPException as e:
            self.logger.error(f"HTTP Exception in rpsgame command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Failed to start Rock Paper Scissors game due to Discord API error.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Failed to start Rock Paper Scissors game due to Discord API error.",
                        ephemeral=True
                    )
            except:
                pass
        except Exception as e:
            import traceback
            self.logger.error(f"Unexpected error in rpsgame command: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An unexpected error occurred while starting Rock Paper Scissors game.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An unexpected error occurred while starting Rock Paper Scissors game.",
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
                        f"⏰ Rock Paper Scissors is on cooldown! Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⏰ Rock Paper Scissors is on cooldown! Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
            except:
                pass
        else:
            self.logger.error(f"Command error: {error}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred while executing the Rock Paper Scissors command.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An error occurred while executing the Rock Paper Scissors command.",
                        ephemeral=True
                    )
            except:
                pass

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(RPSGameCommand(bot))
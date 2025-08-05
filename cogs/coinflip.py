import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from datetime import datetime
import asyncio

class CoinFlipCommand(commands.Cog):
    """Advanced coin flipping command with animations and betting"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        
        # Coin faces
        self.coin_faces = {
            "heads": {"emoji": "🟡", "name": "Heads", "symbol": "H"},
            "tails": {"emoji": "⚫", "name": "Tails", "symbol": "T"}
        }
        
        # Coin flip animations
        self.flip_animation = ["🪙", "🔄", "🎯", "✨"]
        
        # Special events (rare outcomes)
        self.special_events = [
            {"name": "Golden Coin", "emoji": "🏅", "chance": 0.01, "description": "A legendary golden coin appears!"},
            {"name": "Double Flip", "emoji": "🎰", "chance": 0.05, "description": "The coin flips twice in the air!"},
            {"name": "Lucky Streak", "emoji": "🍀", "chance": 0.03, "description": "Fortune smiles upon you!"},
            {"name": "Coin Vanish", "emoji": "🎩", "chance": 0.02, "description": "The coin disappears and reappears!"}
        ]
    
    @app_commands.command(name="coinflip", description="Flip a coin with animations and special effects!")
    @app_commands.describe(
        call="Your prediction (heads or tails)",
        bet="What you're betting on the outcome (optional fun description)"
    )
    @app_commands.choices(call=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def coinflip(self, interaction: discord.Interaction, call: str = None, bet: str = None):
        """
        Flip a coin with special effects and animations
        
        Args:
            interaction: Discord interaction object
            call: User's prediction (heads or tails)
            bet: Optional description of what they're betting
        """
        try:
            # Create initial "flipping" embed
            flip_embed = discord.Embed(
                title="🪙 Coin Flip in Progress!",
                description="The coin soars through the air...",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            if call:
                flip_embed.add_field(
                    name="🎯 Your Call",
                    value=f"{self.coin_faces[call]['emoji']} **{self.coin_faces[call]['name']}**",
                    inline=True
                )
            
            if bet:
                flip_embed.add_field(
                    name="🎰 Your Bet",
                    value=f"*{bet[:100]}*",  # Limit bet description length
                    inline=True
                )
            
            # Animation field
            flip_embed.add_field(
                name="🎪 Flip Animation",
                value="🪙 ➤ 🔄 ➤ 🎯 ➤ ✨",
                inline=False
            )
            
            flip_embed.set_footer(text=f"Flipped by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=flip_embed)
            
            # Animation delay with multiple updates
            for i, frame in enumerate(["🪙 Spinning...", "🔄 Tumbling...", "🎯 Falling...", "✨ Landing..."]):
                await asyncio.sleep(0.5)
                try:
                    flip_embed.set_field_at(
                        2 if bet else 1,  # Adjust index based on whether bet field exists
                        name="🎪 Flip Animation",
                        value=frame,
                        inline=False
                    )
                    await interaction.edit_original_response(embed=flip_embed)
                except:
                    break
            
            # Final delay for suspense
            await asyncio.sleep(1)
            
            # Determine result
            result = random.choice(["heads", "tails"])
            
            # Check for special events
            special_event = None
            if random.random() < 0.1:  # 10% chance for any special event
                special_event = random.choice(self.special_events)
                if random.random() > special_event["chance"] * 10:  # Adjust probability
                    special_event = None
            
            # Create result embed
            result_data = self.coin_faces[result]
            
            # Determine if user won (if they made a call)
            user_won = None
            if call:
                user_won = (call == result)
            
            # Set embed color based on result
            if user_won is True:
                color = discord.Color.green()
                title_prefix = "🎉 You Win!"
            elif user_won is False:
                color = discord.Color.red()
                title_prefix = "😔 You Lose!"
            else:
                color = discord.Color.blue()
                title_prefix = "🪙 Coin Flipped!"
            
            result_embed = discord.Embed(
                title=f"{title_prefix} The coin shows {result_data['name']}!",
                color=color,
                timestamp=datetime.utcnow()
            )
            
            # Large result display
            result_embed.add_field(
                name="🎯 Result",
                value=f"# {result_data['emoji']} **{result_data['name'].upper()}**",
                inline=False
            )
            
            # Show user's call and outcome
            if call:
                outcome_text = f"**Your Call:** {self.coin_faces[call]['emoji']} {self.coin_faces[call]['name']}\n"
                outcome_text += f"**Actual Result:** {result_data['emoji']} {result_data['name']}\n"
                
                if user_won:
                    outcome_text += "**Outcome:** 🎉 **CORRECT!** You won! 🏆"
                else:
                    outcome_text += "**Outcome:** 😔 **WRONG!** Better luck next time! 🍀"
                
                result_embed.add_field(
                    name="📊 Your Prediction",
                    value=outcome_text,
                    inline=False
                )
            
            # Show bet outcome
            if bet:
                if user_won is True:
                    bet_outcome = f"🎰 **Congratulations!** You won your bet: *{bet}* 🎊"
                elif user_won is False:
                    bet_outcome = f"💸 **Oh no!** You lost your bet: *{bet}* 😅"
                else:
                    bet_outcome = f"🎲 **Your bet:** *{bet}* (No prediction made)"
                
                result_embed.add_field(
                    name="🎰 Betting Results",
                    value=bet_outcome,
                    inline=False
                )
            
            # Add special event
            if special_event:
                result_embed.add_field(
                    name=f"🎪 Special Event: {special_event['name']} {special_event['emoji']}",
                    value=special_event['description'],
                    inline=False
                )
            
            # Add fun statistics
            flip_stats = []
            flip_stats.append(f"**Flip Speed:** {random.randint(8, 15)} rotations/second")
            flip_stats.append(f"**Air Time:** {random.uniform(1.5, 3.2):.1f} seconds")
            flip_stats.append(f"**Landing Style:** {random.choice(['Perfect', 'Wobbly', 'Smooth', 'Dramatic', 'Graceful'])}")
            
            # Add probability info
            if not call:
                flip_stats.append(f"**Probability:** 50% chance for each side")
            else:
                flip_stats.append(f"**Your Odds:** 50% (1 in 2 chance)")
            
            result_embed.add_field(
                name="📈 Flip Statistics",
                value="\n".join(flip_stats),
                inline=True
            )
            
            # Add some flavor text
            flavor_texts = {
                "heads": [
                    "The heads side gleams in the light! ✨",
                    "Heads up! Victory is yours! 🎯",
                    "The face of fortune smiles upon you! 😊",
                    "Heads prevails in this cosmic battle! 🌟"
                ],
                "tails": [
                    "Tails tells the tale of triumph! 📖",
                    "The flip of fate favors tails! 🎭",
                    "Tails rises to claim victory! 🚀",
                    "The other side speaks truth! 🗣️"
                ]
            }
            
            if result in flavor_texts:
                flavor = random.choice(flavor_texts[result])
                result_embed.add_field(
                    name="🎭 Flavor Text",
                    value=flavor,
                    inline=True
                )
            
            # Add historical "records" (fun fake stats)
            historical_records = [
                f"This makes {random.randint(50, 200)} total flips today!",
                f"Heads/Tails ratio today: {random.randint(45, 55)}%/{random.randint(45, 55)}%",
                f"Longest streak: {random.randint(3, 8)} {random.choice(['heads', 'tails'])} in a row!",
                f"Most dramatic flip award goes to this one! 🏆"
            ]
            
            result_embed.add_field(
                name="📚 Fun Records",
                value=random.choice(historical_records),
                inline=False
            )
            
            # Footer
            result_embed.set_footer(
                text=f"Flipped by {interaction.user.display_name} • Coin Flip Command",
                icon_url=interaction.user.display_avatar.url if hasattr(interaction.user, 'display_avatar') else None
            )
            
            # Update the message with final results
            await interaction.edit_original_response(embed=result_embed)
            
        except discord.HTTPException as e:
            self.logger.error(f"HTTP Exception in coinflip command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Failed to flip coin due to Discord API error.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Failed to flip coin due to Discord API error.",
                        ephemeral=True
                    )
            except:
                pass
        except Exception as e:
            import traceback
            self.logger.error(f"Unexpected error in coinflip command: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An unexpected error occurred while flipping the coin.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An unexpected error occurred while flipping the coin.",
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
                        f"⏰ Coin is still spinning! Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⏰ Coin is still spinning! Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
            except:
                pass
        else:
            self.logger.error(f"Command error: {error}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred while executing the coin flip command.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An error occurred while executing the coin flip command.",
                        ephemeral=True
                    )
            except:
                pass

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(CoinFlipCommand(bot))
import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from datetime import datetime
import asyncio

class DiceGameCommand(commands.Cog):
    """Advanced dice rolling command with multiple dice types and animations"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        
        # Dice face emojis for visual appeal
        self.dice_faces = {
            1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"
        }
        
        # Special dice types
        self.dice_types = {
            "d4": {"sides": 4, "emoji": "🔺", "color": discord.Color.green()},
            "d6": {"sides": 6, "emoji": "🎲", "color": discord.Color.blue()},
            "d8": {"sides": 8, "emoji": "🔸", "color": discord.Color.orange()},
            "d10": {"sides": 10, "emoji": "🔟", "color": discord.Color.purple()},
            "d12": {"sides": 12, "emoji": "🔷", "color": discord.Color.gold()},
            "d20": {"sides": 20, "emoji": "🎯", "color": discord.Color.red()},
            "d100": {"sides": 100, "emoji": "💯", "color": discord.Color.magenta()}
        }
    
    @app_commands.command(name="dice", description="Roll dice with animations and special effects!")
    @app_commands.describe(
        dice_type="Type of dice to roll (d4, d6, d8, d10, d12, d20, d100)",
        count="Number of dice to roll (1-10)",
        modifier="Add/subtract modifier to total (+5, -3, etc.)"
    )
    @app_commands.choices(dice_type=[
        app_commands.Choice(name="D4 (4-sided)", value="d4"),
        app_commands.Choice(name="D6 (6-sided)", value="d6"),
        app_commands.Choice(name="D8 (8-sided)", value="d8"),
        app_commands.Choice(name="D10 (10-sided)", value="d10"),
        app_commands.Choice(name="D12 (12-sided)", value="d12"),
        app_commands.Choice(name="D20 (20-sided)", value="d20"),
        app_commands.Choice(name="D100 (100-sided)", value="d100")
    ])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def dice(self, interaction: discord.Interaction, dice_type: str = "d6", count: int = 1, modifier: str = None):
        """
        Advanced dice rolling with animations and special effects
        
        Args:
            interaction: Discord interaction object
            dice_type: Type of dice (d4, d6, d8, d10, d12, d20, d100)
            count: Number of dice to roll
            modifier: Optional modifier to add/subtract
        """
        try:
            # Validate inputs
            if count < 1 or count > 10:
                await interaction.response.send_message(
                    "❌ You can roll between 1 and 10 dice at once!",
                    ephemeral=True
                )
                return
            
            # Parse modifier
            mod_value = 0
            if modifier:
                try:
                    mod_value = int(modifier)
                    if abs(mod_value) > 100:
                        await interaction.response.send_message(
                            "❌ Modifier must be between -100 and +100!",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid modifier! Use format like +5, -3, or 0",
                        ephemeral=True
                    )
                    return
            
            dice_info = self.dice_types[dice_type]
            
            # Create initial "rolling" embed
            rolling_embed = discord.Embed(
                title=f"🎲 Rolling {count}x {dice_type.upper()}...",
                description="🎯 The dice are spinning...",
                color=dice_info["color"]
            )
            rolling_embed.add_field(
                name="🎪 Rolling Animation",
                value="🎲 ➤ 🎲 ➤ 🎲",
                inline=False
            )
            rolling_embed.set_footer(text=f"Rolled by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=rolling_embed)
            
            # Animation delay
            await asyncio.sleep(1.5)
            
            # Roll the dice
            rolls = []
            for _ in range(count):
                roll = random.randint(1, dice_info["sides"])
                rolls.append(roll)
            
            total = sum(rolls) + mod_value
            
            # Create result embed
            result_embed = discord.Embed(
                title=f"{dice_info['emoji']} Dice Roll Results - {dice_type.upper()}",
                color=dice_info["color"],
                timestamp=datetime.utcnow()
            )
            
            # Format individual rolls with special visual effects
            roll_display = []
            for i, roll in enumerate(rolls, 1):
                if dice_type == "d6" and roll <= 6:
                    roll_display.append(f"Die {i}: {self.dice_faces[roll]} ({roll})")
                else:
                    # Add special effects for critical rolls
                    if roll == 1:
                        roll_display.append(f"Die {i}: 💥 **{roll}** (Critical Fail!)")
                    elif roll == dice_info["sides"]:
                        roll_display.append(f"Die {i}: ⭐ **{roll}** (Critical Success!)")
                    else:
                        roll_display.append(f"Die {i}: 🎯 **{roll}**")
            
            result_embed.add_field(
                name=f"🎲 Individual Rolls ({count} dice)",
                value="\n".join(roll_display),
                inline=False
            )
            
            # Calculate statistics
            average = sum(rolls) / len(rolls)
            max_possible = dice_info["sides"] * count
            min_possible = count
            
            stats_text = f"**Sum of Rolls:** {sum(rolls)}\n"
            if mod_value != 0:
                mod_sign = "+" if mod_value >= 0 else ""
                stats_text += f"**Modifier:** {mod_sign}{mod_value}\n"
                stats_text += f"**Final Total:** 🎯 **{total}**\n"
            else:
                stats_text += f"**Final Total:** 🎯 **{total}**\n"
            
            stats_text += f"**Average Roll:** {average:.1f}\n"
            stats_text += f"**Range:** {min_possible}-{max_possible}"
            
            result_embed.add_field(
                name="📊 Statistics",
                value=stats_text,
                inline=True
            )
            
            # Add special messages for interesting results
            special_msg = ""
            if len(rolls) > 1:
                if all(r == rolls[0] for r in rolls):
                    special_msg = f"🎊 **AMAZING!** All dice rolled {rolls[0]}!"
                elif total == max_possible + mod_value:
                    special_msg = "🌟 **PERFECT ROLL!** Maximum possible total!"
                elif total == min_possible + mod_value:
                    special_msg = "💥 **EPIC FAIL!** Minimum possible total!"
                elif sum(rolls) >= max_possible * 0.9:
                    special_msg = "🔥 **EXCELLENT!** Very high roll!"
                elif sum(rolls) <= max_possible * 0.2:
                    special_msg = "😅 **OUCH!** Very low roll!"
            
            if special_msg:
                result_embed.add_field(
                    name="🎉 Special Result",
                    value=special_msg,
                    inline=False
                )
            
            # Add probability information
            if dice_type in ["d20", "d6"]:
                if dice_type == "d20" and count == 1:
                    if rolls[0] == 20:
                        prob_text = "🎯 **Natural 20!** (5% chance)"
                    elif rolls[0] == 1:
                        prob_text = "💥 **Natural 1!** (5% chance)"
                    elif rolls[0] >= 15:
                        prob_text = f"🎲 High roll! ({((20-rolls[0]+1)/20)*100:.0f}% chance or better)"
                    else:
                        prob_text = f"🎲 Probability: {(1/20)*100:.0f}% for this exact roll"
                    
                    result_embed.add_field(
                        name="🧮 Probability",
                        value=prob_text,
                        inline=True
                    )
            
            # Footer with user info
            result_embed.set_footer(
                text=f"Rolled by {interaction.user.display_name} • Dice Command",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Edit the original message with results
            await interaction.edit_original_response(embed=result_embed)
            
        except discord.HTTPException as e:
            self.logger.error(f"HTTP Exception in dice command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Failed to roll dice due to Discord API error.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Failed to roll dice due to Discord API error.",
                        ephemeral=True
                    )
            except:
                pass
        except Exception as e:
            import traceback
            self.logger.error(f"Unexpected error in dice command: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An unexpected error occurred while rolling dice.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An unexpected error occurred while rolling dice.",
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
                        f"⏰ Dice are cooling down! Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"⏰ Dice are cooling down! Try again in {error.retry_after:.1f} seconds.",
                        ephemeral=True
                    )
            except:
                pass
        else:
            self.logger.error(f"Command error: {error}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred while executing the dice command.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An error occurred while executing the dice command.",
                        ephemeral=True
                    )
            except:
                pass

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(DiceGameCommand(bot))
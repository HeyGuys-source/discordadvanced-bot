import discord
from discord.ext import commands
from discord import app_commands
import random
import hashlib
import logging
from typing import Union

class ShipCommand(commands.Cog):
    """Advanced ship command with romantic decorative elements and love compatibility."""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Romantic decorative elements
        self.love_emojis = ["💕", "💖", "💗", "💘", "💙", "💚", "💛", "🧡", "❤️", "🤍", "🖤", "💜", "🤎"]
        self.heart_emojis = ["💝", "💞", "💟", "❣️", "💌", "💐", "🌹", "🌸", "🌺", "🌷", "🌼", "🌻"]
        self.romantic_emojis = ["😍", "🥰", "😘", "😗", "😙", "😚", "🤗", "🤭", "😊", "😌", "✨", "⭐"]
        
        # Love compatibility descriptions
        self.compatibility_descriptions = {
            (0, 20): {
                "title": "💔 Not Meant To Be",
                "description": "Sometimes love just isn't in the stars...",
                "color": discord.Color.dark_red(),
                "advice": "Maybe stay as friends? 🤝"
            },
            (21, 40): {
                "title": "😕 Rough Waters",
                "description": "It would take a lot of work to make this relationship sail...",
                "color": discord.Color.red(),
                "advice": "Communication is key! 📞"
            },
            (41, 60): {
                "title": "🤔 Could Work",
                "description": "There's potential here, but it needs nurturing!",
                "color": discord.Color.orange(),
                "advice": "Take time to get to know each other! ☕"
            },
            (61, 80): {
                "title": "😊 Great Match!",
                "description": "This ship is sailing smoothly with good winds!",
                "color": discord.Color.green(),
                "advice": "Plan some romantic dates! 🌹"
            },
            (81, 95): {
                "title": "💖 Perfect Couple!",
                "description": "Made for each other! The stars have aligned!",
                "color": discord.Color.magenta(),
                "advice": "When's the wedding? 💒"
            },
            (96, 100): {
                "title": "💫 Soulmates Forever!",
                "description": "A match made in heaven! Legendary love story!",
                "color": discord.Color.gold(),
                "advice": "Write your love story! 📖✨"
            }
        }
        
        # Romantic quotes
        self.love_quotes = [
            "Love is not about how many days, months, or years you have been together. Love is about how much you love each other every single day.",
            "The best thing to hold onto in life is each other.",
            "Love is when the other person's happiness is more important than your own.",
            "Being deeply loved by someone gives you strength, while loving someone deeply gives you courage.",
            "Love is a friendship set to music.",
            "In all the world, there is no heart for me like yours. In all the world, there is no love for you like mine.",
            "I have found the one whom my soul loves.",
            "You are my today and all of my tomorrows.",
            "Love recognizes no barriers. It jumps hurdles, leaps fences, penetrates walls to arrive at its destination full of hope.",
            "The greatest happiness of life is the conviction that we are loved; loved for ourselves, or rather, loved in spite of ourselves."
        ]
        
        # Ship name combinations
        self.ship_prefixes = ["Love", "Sweet", "Cute", "Perfect", "Dream", "Magic", "Golden", "Precious", "Beautiful", "Amazing"]
        self.ship_suffixes = ["Hearts", "Souls", "Angels", "Stars", "Dreams", "Magic", "Bliss", "Paradise", "Heaven", "Harmony"]
    
    def calculate_compatibility(self, user1: Union[discord.Member, discord.User], 
                              user2: Union[discord.Member, discord.User]) -> int:
        """Calculate love compatibility percentage using deterministic algorithm."""
        # Create a consistent hash based on user IDs (order independent)
        id1, id2 = sorted([user1.id, user2.id])
        combined_hash = hashlib.md5(f"{id1}+{id2}".encode()).hexdigest()
        
        # Convert hash to percentage (0-100)
        hash_value = int(combined_hash[:8], 16)
        percentage = hash_value % 101  # 0-100
        
        return percentage
    
    def get_compatibility_info(self, percentage: int) -> dict:
        """Get compatibility information based on percentage."""
        for (min_val, max_val), info in self.compatibility_descriptions.items():
            if min_val <= percentage <= max_val:
                return info
        
        # Fallback
        return self.compatibility_descriptions[(41, 60)]
    
    def create_ship_name(self, name1: str, name2: str) -> str:
        """Create a cute ship name from two names."""
        # Clean names (remove extra spaces, get first name only)
        name1 = name1.strip().split()[0]
        name2 = name2.strip().split()[0]
        
        # Try different combinations
        combinations = [
            name1[:len(name1)//2] + name2[len(name2)//2:],  # Half + half
            name1[:2] + name2[2:],  # First 2 + rest
            name1[:3] + name2[3:],  # First 3 + rest
            name1 + name2[:2],      # Full first + first 2 of second
            name1[:2] + name2       # First 2 + full second
        ]
        
        # Return the shortest reasonable combination
        valid_combinations = [combo for combo in combinations if 4 <= len(combo) <= 12]
        return min(valid_combinations, key=len) if valid_combinations else f"{name1}{name2}"
    
    def get_love_bar(self, percentage: int) -> str:
        """Create a visual love compatibility bar."""
        filled_hearts = "💖" * (percentage // 10)
        empty_hearts = "🤍" * (10 - (percentage // 10))
        return filled_hearts + empty_hearts
    
    @app_commands.command(name="ship", description="💕 Calculate love compatibility between two users with romantic decorations")
    @app_commands.describe(
        user1="First person to ship",
        user2="Second person to ship"
    )
    async def ship(
        self, 
        interaction: discord.Interaction, 
        user1: discord.Member, 
        user2: discord.Member
    ):
        """Ship two users with advanced romantic decorations and compatibility analysis."""
        try:
            # Prevent self-shipping (unless it's funny)
            if user1.id == user2.id:
                embed = discord.Embed(
                    title="🪞 Self Love!",
                    description=f"**{user1.display_name}** loves themselves! That's actually healthy! 💖",
                    color=discord.Color.purple(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="💝 Self-Love Rating:",
                    value="**100%** - Perfect! 🥰",
                    inline=False
                )
                embed.add_field(
                    name="✨ Message:",
                    value="Remember to love yourself first! Self-care is important! 🌟",
                    inline=False
                )
                embed.set_footer(text="Self-love is the best love! 💕")
                await interaction.response.send_message(embed=embed)
                return
            
            # Calculate compatibility
            compatibility = self.calculate_compatibility(user1, user2)
            comp_info = self.get_compatibility_info(compatibility)
            
            # Create ship name
            ship_name = self.create_ship_name(user1.display_name, user2.display_name)
            
            # Create beautiful embed
            embed = discord.Embed(
                title=f"💕 {comp_info['title']} 💕",
                description=f"**{user1.display_name}** × **{user2.display_name}**\n\n{comp_info['description']}",
                color=comp_info['color'],
                timestamp=discord.utils.utcnow()
            )
            
            # Add ship name with decorative elements
            random_prefix = random.choice(self.ship_prefixes)
            random_suffix = random.choice(self.ship_suffixes)
            embed.add_field(
                name="💑 Ship Name:",
                value=f"✨ **{ship_name}** ✨\n*\"The {random_prefix} {random_suffix}\"*",
                inline=False
            )
            
            # Love compatibility bar
            love_bar = self.get_love_bar(compatibility)
            embed.add_field(
                name="💖 Love Compatibility:",
                value=f"**{compatibility}%**\n{love_bar}",
                inline=False
            )
            
            # Add romantic advice
            embed.add_field(
                name="💝 Relationship Advice:",
                value=comp_info['advice'],
                inline=True
            )
            
            # Add random love quote for high compatibility
            if compatibility >= 70:
                quote = random.choice(self.love_quotes)
                embed.add_field(
                    name="💌 Love Quote:",
                    value=f"*\"{quote}\"*",
                    inline=False
                )
            
            # Detailed compatibility breakdown
            traits = []
            if compatibility >= 80:
                traits.extend(["💫 Soulmate Connection", "✨ Perfect Chemistry", "🌟 Destined Together"])
            elif compatibility >= 60:
                traits.extend(["💖 Strong Bond", "🌹 Romantic Potential", "💕 Great Chemistry"])
            elif compatibility >= 40:
                traits.extend(["🤝 Good Friendship", "💭 Common Interests", "🌱 Room to Grow"])
            else:
                traits.extend(["🤔 Different Paths", "💪 Needs Work", "🌈 Opposites Attract?"])
            
            embed.add_field(
                name="🔍 Relationship Traits:",
                value="\n".join(f"• {trait}" for trait in traits),
                inline=True
            )
            
            # Fun prediction
            predictions = {
                (0, 30): ["Probably better as friends 🤝", "Maybe in another universe 🌌", "Not this lifetime 😅"],
                (31, 60): ["Could work with effort 💪", "Take it slow and see 🐌", "Friendship first! 👫"],
                (61, 85): ["Wedding bells incoming? 🔔", "Start planning dates! 📅", "Very promising! 🌟"],
                (86, 100): ["When's the proposal? 💍", "Match made in heaven! ☁️", "Epic love story! 📚"]
            }
            
            for (min_val, max_val), pred_list in predictions.items():
                if min_val <= compatibility <= max_val:
                    prediction = random.choice(pred_list)
                    break
            else:
                prediction = "Love is mysterious! 💫"
            
            embed.add_field(
                name="🔮 Crystal Ball Says:",
                value=prediction,
                inline=True
            )
            
            # Add decorative elements based on compatibility
            if compatibility >= 90:
                decoration = " ".join(random.choices(self.romantic_emojis + self.heart_emojis, k=5))
            elif compatibility >= 70:
                decoration = " ".join(random.choices(self.love_emojis + self.heart_emojis, k=4))
            elif compatibility >= 50:
                decoration = " ".join(random.choices(self.love_emojis, k=3))
            else:
                decoration = "💔 💫 🌈"
            
            embed.add_field(
                name="✨ Love Magic:",
                value=decoration,
                inline=False
            )
            
            # Set thumbnails (user avatars in heart formation)
            embed.set_thumbnail(url=user1.display_avatar.url)
            
            # Footer with both users
            embed.set_footer(
                text=f"Shipped by Cupid ✨ {user1.display_name} & {user2.display_name}",
                icon_url=user2.display_avatar.url
            )
            
            # Add author field for the requester
            embed.set_author(
                name=f"💘 Love Calculator 💘",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the ship
            logging.info(
                f"Ship command used by {interaction.user} - "
                f"{user1.display_name} × {user2.display_name}: {compatibility}%"
            )
            
        except Exception as e:
            embed = discord.Embed(
                title="💔 Shipping Error",
                description="Cupid's arrow missed the mark! An error occurred while calculating love compatibility.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(
                name="💝 Don't worry!",
                value="Love finds a way! Try again later! ✨",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.error(f"Error in ship command: {e}", exc_info=True)

# Setup functions
async def setup(bot):
    """Setup function to add the ShipCommand cog to the bot."""
    await bot.add_cog(ShipCommand(bot))
    logging.info("Ship command loaded successfully")

def add_ship_command(bot):
    """Alternative setup function for manual integration."""
    ship_cog = ShipCommand(bot)
    
    @bot.tree.command(name="ship", description="💕 Calculate love compatibility between two users with romantic decorations")
    @app_commands.describe(
        user1="First person to ship",
        user2="Second person to ship"
    )
    async def ship(
        interaction: discord.Interaction, 
        user1: discord.Member, 
        user2: discord.Member
    ):
        await ship_cog.ship(interaction, user1, user2)
    
    logging.info("Ship command added successfully")
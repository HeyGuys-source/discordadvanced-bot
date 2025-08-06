# Discord bot command for rules - FIXED VERSION
# Copy this code into your existing bot.py file

import discord
from discord.ext import commands

@commands.command(name="rules")
async def rules(ctx):
    """Display server rules in a pink Discord embed - Fixed for Discord.py v1.x"""
    
    # Create the embed with pink color
    embed = discord.Embed(
        title="🛡️ Server Rules",
        description="Please read and follow all server rules to maintain a positive community environment.",
        color=0xFF69B4  # Pink color (#FF69B4)
    )
    
    # Define the rules as provided
    rules_list = [
        "Don't be racist",
        "Don't be homophobic or sexist", 
        "Don't abuse your power if you are a mod or higher",
        "No disturbing, gross or inappropriate videos, pictures, etcetera",
        "Be respectful! Do not disrespect any members or staff",
        "No spamming",
        "No drama",
        "No politics",
        "Don't ghost or spam ping any member or staff",
        "No rage bait",
        "<#1338329138313822268> should only be used if there's something that can help us on the dev team and have to have discord for over 1 months",
        "No self promotion unless I let you or you have content creator role"
    ]
    
    # Add each rule as a field in the embed
    rules_text = ""
    for i, rule in enumerate(rules_list, 1):
        rules_text += f"**{i}.** {rule}\n"
    
    embed.add_field(
        name="📋 Rules List",
        value=rules_text,
        inline=False
    )
    
    # Add footer - Fixed for Discord.py v1.x compatibility
    try:
        # Discord.py v2.x
        guild_icon = ctx.guild.icon.url if ctx.guild.icon else None
    except AttributeError:
        # Discord.py v1.x fallback
        guild_icon = str(ctx.guild.icon_url) if ctx.guild.icon_url else None
    
    embed.set_footer(
        text="ℹ️ Violations may result in warnings, mutes, or bans",
        icon_url=guild_icon
    )
    
    # Send the embed
    await ctx.send(embed=embed)

# Setup function for cog loading
def setup(bot):
    bot.add_command(rules)

"""
INSTALLATION INSTRUCTIONS:

1. Copy the entire rules command function above
2. Paste it into your existing bot.py file
3. Make sure you have these imports:
   import discord
   from discord.ext import commands

4. Usage: !rules

5. This version is fixed for both Discord.py v1.x and v2.x compatibility
"""

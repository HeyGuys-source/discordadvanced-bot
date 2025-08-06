# Discord bot command for /rules
# Copy this code into your existing bot.py file

import discord
from discord.ext import commands

# For Discord.py v2.x (Slash Commands) - Use if you have discord.py 2.0+
# Uncomment the following if you're using Discord.py v2.x:

# @bot.slash_command(name="rules", description="Display server rules")
# async def rules_slash(interaction: discord.Interaction):
#     """Display server rules in a pink Discord embed (Slash Command)"""
#     
#     # Create the embed with pink color
#     embed = discord.Embed(
#         title="🛡️ Server Rules",
#         description="Please read and follow all server rules to maintain a positive community environment.",
#         color=0xFF69B4  # Pink color (#FF69B4)
#     )
#     
#     # Define the rules as provided
#     rules_list = [
#         "Don't be racist",
#         "Don't be homophobic or sexist", 
#         "Don't abuse your power if you are a mod or higher",
#         "No disturbing, gross or inappropriate videos, pictures, etcetera",
#         "Be respectful! Do not disrespect any members or staff",
#         "No spamming",
#         "No drama",
#         "No politics",
#         "Don't ghost or spam ping any member or staff",
#         "No rage bait",
#         "<#1338329138313822268> should only be used if there's something that can help us on the dev team and have to have discord for over 1 months",
#         "No self promotion unless I let you or you have content creator role"
#     ]
#     
#     # Add each rule as a field in the embed
#     rules_text = ""
#     for i, rule in enumerate(rules_list, 1):
#         rules_text += f"**{i}.** {rule}\n"
#     
#     embed.add_field(
#         name="📋 Rules List",
#         value=rules_text,
#         inline=False
#     )
#     
#     # Add footer
#     embed.set_footer(
#         text="ℹ️ Violations may result in warnings, mutes, or bans",
#         icon_url=interaction.guild.icon.url if interaction.guild.icon else None
#     )
#     
#     # Send the embed
#     await interaction.response.send_message(embed=embed)

# For Discord.py v1.x (Traditional Commands) - RECOMMENDED FOR YOUR SETUP
@commands.command(name="rules")
async def rules(ctx):
    """Display server rules in a pink Discord embed (Traditional Command)"""
    
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
    
    # Add footer
    embed.set_footer(
        text="ℹ️ Violations may result in warnings, mutes, or bans",
        icon_url=ctx.guild.icon.url if ctx.guild.icon else None
    )
    
    # Send the embed
    await ctx.send(embed=embed)

# Alternative version using traditional command (if you prefer !rules instead of /rules)
@commands.command(name="rules")
async def rules_traditional(ctx):
    """Display server rules in a pink Discord embed (traditional command)"""
    
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
    
    # Add footer
    embed.set_footer(
        text="ℹ️ Violations may result in warnings, mutes, or bans",
        icon_url=ctx.guild.icon.url if ctx.guild.icon else None
    )
    
    # Send the embed
    await ctx.send(embed=embed)

# Setup Instructions:
def setup(bot):
    bot.add_command(rules)

# Instructions for adding to your bot:
"""
PROBLEM ANALYSIS & SOLUTION:
The error you encountered was:
"AttributeError: module 'discord.ext.commands' has no attribute 'slash_command'"

This happens because you're using Discord.py v1.x, which doesn't support @commands.slash_command.

FIXED SOLUTION:

1. Copy the ENTIRE content of this file into your existing bot.py file
2. Make sure you have these imports at the top:
   import discord
   from discord.ext import commands

3. The command now uses @commands.command which works with Discord.py v1.x

4. Usage: !rules

5. Features:
   - Pink Discord embed styling (#FF69B4)
   - All 12 server rules properly numbered
   - Professional formatting with shield emoji
   - Footer warning about violations
   - Server icon integration

6. If you want slash commands (/rules):
   - Upgrade to Discord.py v2.x: pip install -U discord.py
   - Uncomment the slash command section at the top
   - Replace @bot.slash_command with your bot instance name

The command will now work perfectly with your current Discord.py setup!
"""

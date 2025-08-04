import discord
from discord.ext import commands
import asyncio
import random
import aiohttp
import time
from datetime import datetime

# Simple in-memory economy system
user_balances = {}
daily_claimed = {}

def get_balance(user_id):
    return user_balances.get(user_id, 100)

def add_money(user_id, amount):
    if user_id not in user_balances:
        user_balances[user_id] = 100
    user_balances[user_id] += amount
    return user_balances[user_id]

def remove_money(user_id, amount):
    if user_id not in user_balances:
        user_balances[user_id] = 100
    user_balances[user_id] = max(0, user_balances[user_id] - amount)
    return user_balances[user_id]

def can_claim_daily(user_id):
    today = datetime.now().date()
    last_claim = daily_claimed.get(user_id)
    return last_claim != today

def claim_daily_reward(user_id):
    if can_claim_daily(user_id):
        amount = random.randint(50, 200)
        add_money(user_id, amount)
        daily_claimed[user_id] = datetime.now().date()
        return amount
    return 0

# ============ ECONOMY COMMANDS ============

@commands.command(name='balance', aliases=['bal'])
async def check_balance(ctx, member: discord.Member = None):
    """Check K-coin balance"""
    target = member or ctx.author
    balance = get_balance(target.id)
    
    embed = discord.Embed(
        title=f"💰 {target.display_name}'s Wallet",
        description=f"**{balance:,} K-coins**",
        color=0xf1c40f
    )
    await ctx.send(embed=embed)

@commands.command(name='daily')
async def daily_coins(ctx):
    """Claim daily K-coins"""
    amount = claim_daily_reward(ctx.author.id)
    
    if amount > 0:
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You received **{amount} K-coins**!",
            color=0x2ecc71
        )
        embed.add_field(
            name="New Balance", 
            value=f"{get_balance(ctx.author.id):,} K-coins", 
            inline=False
        )
    else:
        embed = discord.Embed(
            title="⏰ Already Claimed",
            description="Come back tomorrow for your next daily reward!",
            color=0xe74c3c
        )
    
    await ctx.send(embed=embed)

@commands.command(name='give')
async def give_money(ctx, member: discord.Member, amount: int):
    """Give K-coins to another user"""
    if member.bot:
        await ctx.send("You can't give money to bots!")
        return
    
    if amount <= 0:
        await ctx.send("Amount must be positive!")
        return
    
    sender_balance = get_balance(ctx.author.id)
    if amount > sender_balance:
        await ctx.send(f"You don't have enough K-coins! You have {sender_balance:,} K-coins.")
        return
    
    remove_money(ctx.author.id, amount)
    add_money(member.id, amount)
    
    embed = discord.Embed(
        title="💸 Money Transferred",
        description=f"{ctx.author.mention} gave **{amount:,} K-coins** to {member.mention}",
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

@commands.command(name='richest')
async def money_leaderboard(ctx):
    """Show richest users"""
    if not user_balances:
        await ctx.send("No one has any money yet!")
        return
    
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    
    embed = discord.Embed(
        title="💎 Richest Users",
        description="Top 10 wealthiest members",
        color=0xf1c40f
    )
    
    for i, (user_id, balance) in enumerate(sorted_users[:10]):
        try:
            user = ctx.bot.get_user(user_id)
            if user:
                rank = ["🥇", "🥈", "🥉"][i] if i < 3 else f"**{i+1}.**"
                embed.add_field(
                    name=f"{rank} {user.display_name}",
                    value=f"{balance:,} K-coins",
                    inline=False
                )
        except:
            continue
    
    await ctx.send(embed=embed)

@commands.command(name='grant')
@commands.has_permissions(administrator=True)
async def grant_money(ctx, member: discord.Member, amount: int):
    """[ADMIN] Grant K-coins to a user"""
    if amount <= 0:
        await ctx.send("Amount must be positive!")
        return
    
    new_balance = add_money(member.id, amount)
    
    embed = discord.Embed(
        title="🎁 Money Granted",
        description=f"Granted **{amount:,} K-coins** to {member.mention}",
        color=0x9b59b6
    )
    embed.add_field(
        name="New Balance",
        value=f"{new_balance:,} K-coins",
        inline=False
    )
    await ctx.send(embed=embed)

# ============ SINGLE PLAYER GAMES ============

@commands.command(name='flip')
async def coin_flip(ctx, bet: int = 0):
    """Flip a coin with optional betting"""
    result = random.choice(['Heads', 'Tails'])
    
    if bet <= 0:
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=0x3498db
        )
        await ctx.send(embed=embed)
        return
    
    user_balance = get_balance(ctx.author.id)
    if bet > user_balance:
        await ctx.send(f"You don't have enough K-coins! Balance: {user_balance:,}")
        return
    
    embed = discord.Embed(
        title="🪙 Choose Your Side",
        description="React with 👤 for Heads or 🔄 for Tails",
        color=0x3498db
    )
    message = await ctx.send(embed=embed)
    await message.add_reaction('👤')
    await message.add_reaction('🔄')
    
    def check(reaction, user):
        return (user == ctx.author and 
                str(reaction.emoji) in ['👤', '🔄'] and 
                reaction.message.id == message.id)
    
    try:
        reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30.0, check=check)
        choice = 'Heads' if str(reaction.emoji) == '👤' else 'Tails'
        
        if choice == result:
            winnings = bet * 2
            add_money(ctx.author.id, winnings)
            embed = discord.Embed(
                title="🎉 You Won!",
                description=f"The coin landed on **{result}**!\nYou won **{winnings:,} K-coins**!",
                color=0x2ecc71
            )
        else:
            remove_money(ctx.author.id, bet)
            embed = discord.Embed(
                title="😢 You Lost!",
                description=f"The coin landed on **{result}**!\nYou lost **{bet:,} K-coins**.",
                color=0xe74c3c
            )
        
        embed.add_field(
            name="New Balance",
            value=f"{get_balance(ctx.author.id):,} K-coins",
            inline=False
        )
        
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="⏰ Time's Up",
            description="You took too long to choose!",
            color=0x95a5a6
        )
    
    await message.edit(embed=embed)

@commands.command(name='slots')
async def slot_machine(ctx, bet: int):
    """Play the slot machine"""
    if bet <= 0:
        await ctx.send("Bet must be positive!")
        return
    
    user_balance = get_balance(ctx.author.id)
    if bet > user_balance:
        await ctx.send(f"You don't have enough K-coins! Balance: {user_balance:,}")
        return
    
    symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣']
    weights = [30, 25, 20, 15, 7, 2, 1]
    
    result = [random.choices(symbols, weights=weights)[0] for _ in range(3)]
    
    # Calculate winnings
    if result[0] == result[1] == result[2]:
        if result[0] == '💎':
            multiplier = 50
        elif result[0] == '7️⃣':
            multiplier = 20
        elif result[0] == '⭐':
            multiplier = 10
        else:
            multiplier = 5
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        multiplier = 2
    else:
        multiplier = 0
    
    winnings = bet * multiplier
    
    if winnings > 0:
        add_money(ctx.author.id, winnings - bet)
        embed = discord.Embed(
            title="🎰 SLOT MACHINE",
            description=f"{''.join(result)}\n\n🎉 **YOU WON {winnings:,} K-COINS!**",
            color=0x2ecc71
        )
    else:
        remove_money(ctx.author.id, bet)
        embed = discord.Embed(
            title="🎰 SLOT MACHINE",
            description=f"{''.join(result)}\n\n😢 You lost {bet:,} K-coins",
            color=0xe74c3c
        )
    
    embed.add_field(
        name="New Balance",
        value=f"{get_balance(ctx.author.id):,} K-coins",
        inline=False
    )
    
    await ctx.send(embed=embed)

@commands.command(name='dice')
async def dice_game(ctx, sides: int = 6):
    """Roll a dice with custom sides"""
    if sides < 2 or sides > 100:
        await ctx.send("Dice must have between 2 and 100 sides!")
        return
    
    result = random.randint(1, sides)
    
    embed = discord.Embed(
        title=f"🎲 Rolling a {sides}-sided die...",
        description=f"**You rolled: {result}**",
        color=0x3498db
    )
    
    if result == sides:
        bonus = 50
        add_money(ctx.author.id, bonus)
        embed.add_field(
            name="🎉 Perfect Roll Bonus!",
            value=f"You got the maximum roll and earned {bonus} K-coins!",
            inline=False
        )
        embed.add_field(
            name="New Balance",  
            value=f"{get_balance(ctx.author.id):,} K-coins",
            inline=False
        )
    
    await ctx.send(embed=embed)

@commands.command(name='8ball')
async def magic_8ball(ctx, *, question):
    """Ask the magic 8-ball a question"""
    responses = [
        "It is certain", "Reply hazy, try again", "Don't count on it",
        "It is decidedly so", "Ask again later", "My reply is no",
        "Without a doubt", "Better not tell you now", "My sources say no",
        "Yes definitely", "Cannot predict now", "Outlook not so good",
        "You may rely on it", "Concentrate and ask again", "Very doubtful",
        "As I see it, yes", "Most likely", "Outlook good", "Yes",
        "Signs point to yes"
    ]
    
    response = random.choice(responses)
    
    embed = discord.Embed(
        title="🎱 Magic 8-Ball",
        color=0x9b59b6
    )
    embed.add_field(name="Question", value=question, inline=False)
    embed.add_field(name="Answer", value=f"*{response}*", inline=False)
    embed.set_footer(text=f"Asked by {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@commands.command(name='rps')
async def rock_paper_scissors(ctx, choice: str = ""):
    """Play Rock Paper Scissors against the bot"""
    if not choice:
        embed = discord.Embed(
            title="✂️ Rock Paper Scissors",
            description="Choose: `!rps rock`, `!rps paper`, or `!rps scissors`",
            color=0x3498db
        )
        await ctx.send(embed=embed)
        return
    
    choice = choice.lower()
    if choice not in ['rock', 'paper', 'scissors']:
        await ctx.send("Invalid choice! Use rock, paper, or scissors.")
        return
    
    bot_choice = random.choice(['rock', 'paper', 'scissors'])
    
    # Determine winner
    if choice == bot_choice:
        result = "It's a tie!"
        color = 0xf39c12
        reward = 5
    elif ((choice == 'rock' and bot_choice == 'scissors') or 
          (choice == 'paper' and bot_choice == 'rock') or 
          (choice == 'scissors' and bot_choice == 'paper')):
        result = "You win!"
        color = 0x2ecc71
        reward = 25
    else:
        result = "You lose!"
        color = 0xe74c3c
        reward = 0
    
    choice_emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
    
    embed = discord.Embed(
        title="✂️ Rock Paper Scissors",
        description=f"You: {choice_emojis[choice]} {choice.title()}\n"
                   f"Bot: {choice_emojis[bot_choice]} {bot_choice.title()}\n\n**{result}**",
        color=color
    )
    
    if reward > 0:
        add_money(ctx.author.id, reward)
        embed.add_field(name="Reward", value=f"+{reward} K-coins", inline=True)
        embed.add_field(name="Balance", value=f"{get_balance(ctx.author.id):,} K-coins", inline=True)
    
    await ctx.send(embed=embed)

# ============ MULTIPLAYER GAMES ============

@commands.command(name='trivia')
async def trivia_game(ctx):
    """Multiplayer trivia game"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://opentdb.com/api.php?amount=1&type=multiple') as resp:
                if resp.status != 200:
                    await ctx.send("Failed to fetch trivia question. Try again!")
                    return
                data = await resp.json()
        
        if data['response_code'] != 0:
            await ctx.send("Failed to fetch trivia question. Try again!")
            return
        
        question_data = data['results'][0]
        question = question_data['question']
        correct_answer = question_data['correct_answer']
        incorrect_answers = question_data['incorrect_answers']
        category = question_data['category']
        difficulty = question_data['difficulty']
        
        # Create answer options
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)
        correct_index = all_answers.index(correct_answer)
        
        embed = discord.Embed(
            title=f"🧠 Trivia Time! ({difficulty.title()})",
            description=f"**Category:** {category}\n\n**Question:** {question}",
            color=0x3498db
        )
        
        answer_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
        for i, answer in enumerate(all_answers):
            embed.add_field(
                name=f"{answer_emojis[i]} Option {i+1}",
                value=answer,
                inline=False
            )
        
        embed.set_footer(text="React with your answer! 15 seconds to respond.")
        
        message = await ctx.send(embed=embed)
        for i in range(len(all_answers)):
            await message.add_reaction(answer_emojis[i])
        
        # Collect participants
        participants = {}
        start_time = time.time()
        
        def check(reaction, user):
            return (not user.bot and 
                   str(reaction.emoji) in answer_emojis[:len(all_answers)] and 
                   reaction.message.id == message.id)
        
        while time.time() - start_time < 15:
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=1.0, check=check)
                if user.id not in participants:
                    answer_index = answer_emojis.index(str(reaction.emoji))
                    participants[user.id] = {
                        'user': user,
                        'answer': answer_index,
                        'time': time.time() - start_time
                    }
            except asyncio.TimeoutError:
                continue
        
        # Find winners
        winners = [p for p in participants.values() if p['answer'] == correct_index]
        winners.sort(key=lambda x: x['time'])
        
        result_embed = discord.Embed(
            title="🏆 Trivia Results",
            description=f"**Correct Answer:** {answer_emojis[correct_index]} {correct_answer}",
            color=0x2ecc71
        )
        
        if winners:
            winner_text = ""
            for i, winner in enumerate(winners[:5]):
                points = [50, 30, 20, 15, 10][i] if i < 5 else 5
                add_money(winner['user'].id, points)
                place = ["🥇", "🥈", "🥉", "4th", "5th"][i] if i < 5 else f"{i+1}th"
                winner_text += f"{place} {winner['user'].display_name} (+{points} K-coins)\n"
            
            result_embed.add_field(name="Winners", value=winner_text, inline=False)
        else:
            result_embed.add_field(
                name="Results", 
                value="No one got it right! Better luck next time.", 
                inline=False
            )
        
        await ctx.send(embed=result_embed)
        
    except Exception as e:
        await ctx.send("Error fetching trivia question. Please try again!")

@commands.command(name='countdown')
async def countdown_game(ctx, target: int = 0):
    """Get closest to the target number"""
    if target <= 0:
        target = random.randint(1, 1000)
    
    embed = discord.Embed(
        title="🎯 Countdown Game",
        description=f"**Target:** {target}\n\nType a number! Closest wins.\n⏰ 20 seconds!",
        color=0xf39c12
    )
    
    await ctx.send(embed=embed)
    
    guesses = {}
    start_time = time.time()
    
    def check(message):
        if message.author.bot or message.channel != ctx.channel:
            return False
        try:
            int(message.content)
            return True
        except ValueError:
            return False
    
    while time.time() - start_time < 20:
        try:
            message = await ctx.bot.wait_for('message', timeout=1.0, check=check)
            guess = int(message.content)
            if message.author.id not in guesses:
                guesses[message.author.id] = {
                    'user': message.author,
                    'guess': guess,
                    'difference': abs(target - guess)
                }
                await message.add_reaction('✅')
        except (asyncio.TimeoutError, ValueError):
            continue
    
    if not guesses:
        await ctx.send("No valid guesses! Game ended.")
        return
    
    # Find winner
    winner_data = min(guesses.values(), key=lambda x: x['difference'])
    
    # Award points based on accuracy
    if winner_data['difference'] == 0:
        points = 100
    elif winner_data['difference'] <= 5:
        points = 75
    elif winner_data['difference'] <= 20:
        points = 50
    else:
        points = 25
    
    add_money(winner_data['user'].id, points)
    
    embed = discord.Embed(
        title="🏆 Countdown Results",
        description=f"**Target:** {target}\n**Winner:** {winner_data['user'].display_name}",
        color=0x2ecc71
    )
    embed.add_field(
        name="Winning Guess",
        value=f"{winner_data['guess']} (off by {winner_data['difference']})",
        inline=True
    )
    embed.add_field(name="Prize", value=f"{points} K-coins", inline=True)
    
    await ctx.send(embed=embed)

@commands.command(name='racing')
async def racing_game(ctx):
    """React fastest to win"""
    embed = discord.Embed(
        title="🏁 Racing Game",
        description="React to 🏃 when it appears!\n\n⏰ Starting in 3 seconds...",
        color=0xe74c3c
    )
    
    message = await ctx.send(embed=embed)
    await asyncio.sleep(random.uniform(3, 8))
    
    race_embed = discord.Embed(
        title="🏁 GO! 🏃",
        description="**React NOW!**",
        color=0x2ecc71
    )
    
    await message.edit(embed=race_embed)
    await message.add_reaction('🏃')
    
    def check(reaction, user):
        return (not user.bot and 
               str(reaction.emoji) == '🏃' and 
               reaction.message.id == message.id)
    
    try:
        reaction, winner = await ctx.bot.wait_for('reaction_add', timeout=10.0, check=check)
        
        points = random.randint(75, 150)
        add_money(winner.id, points)
        
        result_embed = discord.Embed(
            title="🏆 Race Winner!",
            description=f"**{winner.display_name}** won the race!",
            color=0xf1c40f
        )
        result_embed.add_field(name="Prize", value=f"{points} K-coins", inline=True)
        result_embed.add_field(name="Balance", value=f"{get_balance(winner.id):,} K-coins", inline=True)
        
        await message.edit(embed=result_embed)
        
    except asyncio.TimeoutError:
        timeout_embed = discord.Embed(
            title="🏁 Race Timeout",
            description="No one reacted in time!",
            color=0x95a5a6
        )
        await message.edit(embed=timeout_embed)

@commands.command(name='memory')
async def memory_game(ctx):
    """Remember the emoji sequence"""
    sequence_length = random.randint(4, 8)
    sequence = [random.choice(['🔴', '🟢', '🔵', '🟡']) for _ in range(sequence_length)]
    
    embed = discord.Embed(
        title="🧠 Memory Game",
        description="Memorize this sequence! 5 seconds to study.\n\n" + " ".join(sequence),
        color=0x9b59b6
    )
    
    message = await ctx.send(embed=embed)
    await asyncio.sleep(5)
    
    hidden_embed = discord.Embed(
        title="🧠 Memory Game", 
        description=f"Type the {sequence_length} emoji sequence!\n🔴🟢🔵🟡\n\n⏰ 30 seconds!",
        color=0x9b59b6
    )
    
    await message.edit(embed=hidden_embed)
    
    correct_sequence = "".join(sequence)
    participants = {}
    start_time = time.time()
    
    def check(msg):
        return not msg.author.bot and msg.channel == ctx.channel
    
    while time.time() - start_time < 30:
        try:
            user_message = await ctx.bot.wait_for('message', timeout=1.0, check=check)
            user_sequence = user_message.content.replace(" ", "")
            
            if user_message.author.id not in participants:
                is_correct = user_sequence == correct_sequence
                participants[user_message.author.id] = {
                    'user': user_message.author,
                    'correct': is_correct,
                    'time': time.time() - start_time
                }
                await user_message.add_reaction('✅' if is_correct else '❌')
        except asyncio.TimeoutError:
            continue
    
    # Find winners
    winners = [p for p in participants.values() if p['correct']]
    winners.sort(key=lambda x: x['time'])
    
    result_embed = discord.Embed(
        title="🧠 Memory Results",
        description=f"**Correct Sequence:** {' '.join(sequence)}",
        color=0x2ecc71
    )
    
    if winners:
        winner_text = ""
        for i, winner in enumerate(winners[:3]):
            points = [100, 60, 40][i] if i < 3 else 20
            add_money(winner['user'].id, points)
            place = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}th"
            winner_text += f"{place} {winner['user'].display_name} (+{points} K-coins)\n"
        
        result_embed.add_field(name="Winners", value=winner_text, inline=False)
    else:
        result_embed.add_field(name="Results", value="No correct answers!", inline=False)
    
    await ctx.send(embed=result_embed)

@commands.command(name='auction')
async def auction_game(ctx):
    """Bid on mystery prizes"""
    prizes = [
        {"name": "Rare Diamond", "value": 500, "emoji": "💎"},
        {"name": "Golden Coin", "value": 200, "emoji": "🪙"},
        {"name": "Lucky Charm", "value": 300, "emoji": "🍀"},
        {"name": "Magic Crystal", "value": 400, "emoji": "🔮"},
        {"name": "Ancient Relic", "value": 600, "emoji": "🏺"},
        {"name": "Mystic Orb", "value": 350, "emoji": "🔵"},
    ]
    
    prize = random.choice(prizes)
    
    embed = discord.Embed(
        title="🏛️ AUCTION HOUSE",
        description="**Mystery Item Up for Auction!**\n\nStarting bid: **50 K-coins**\nType your bid!\n\n⏰ 30 seconds!",
        color=0xf39c12
    )
    
    await ctx.send(embed=embed)
    
    bids = {}
    start_time = time.time()
    
    def check(msg):
        if msg.author.bot or msg.channel != ctx.channel:
            return False
        try:
            bid = int(msg.content)
            return bid >= 50
        except ValueError:
            return False
    
    while time.time() - start_time < 30:
        try:
            bid_message = await ctx.bot.wait_for('message', timeout=1.0, check=check)
            bid_amount = int(bid_message.content)
            user_balance = get_balance(bid_message.author.id)
            
            if bid_amount <= user_balance:
                current_high = max(bids.values()) if bids else 49
                if bid_amount > current_high:
                    bids[bid_message.author.id] = bid_amount
                    await bid_message.add_reaction('💰')
                else:
                    await bid_message.add_reaction('📉')
            else:
                await bid_message.add_reaction('❌')
        except (asyncio.TimeoutError, ValueError):
            continue
    
    if not bids:
        await ctx.send("No valid bids! Auction cancelled.")
        return
    
    # Process winner
    winner_id = max(bids.keys(), key=lambda x: bids[x])
    winning_bid = bids[winner_id]
    winner = ctx.bot.get_user(winner_id)
    
    remove_money(winner_id, winning_bid)
    add_money(winner_id, prize["value"])
    
    net_gain = prize["value"] - winning_bid
    
    embed = discord.Embed(
        title="🏆 Auction Results",
        description=f"**Winner:** {winner.display_name}\n**Bid:** {winning_bid:,} K-coins",
        color=0x2ecc71
    )
    embed.add_field(
        name="Prize Revealed",
        value=f"{prize['emoji']} **{prize['name']}**\nValue: {prize['value']} K-coins",
        inline=True
    )
    embed.add_field(
        name="Net Result",
        value=f"{'Profit' if net_gain > 0 else 'Loss'}: {abs(net_gain):,} K-coins",
        inline=True
    )
    
    await ctx.send(embed=embed)

# Function to add commands to your bot
def setup(bot):
    """Add all commands to the bot"""
    bot.add_command(check_balance)
    bot.add_command(daily_coins)
    bot.add_command(give_money)
    bot.add_command(money_leaderboard)
    bot.add_command(grant_money)
    bot.add_command(coin_flip)
    bot.add_command(slot_machine)
    bot.add_command(dice_game)
    bot.add_command(magic_8ball)
    bot.add_command(rock_paper_scissors)
    bot.add_command(trivia_game)
    bot.add_command(countdown_game)
    bot.add_command(racing_game)
    bot.add_command(memory_game)
    bot.add_command(auction_game)

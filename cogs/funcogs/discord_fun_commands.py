import discord
from discord.ext import commands
import asyncio
import random
import json
import aiohttp
import time
from datetime import datetime, timedelta
import os

# Economy System
class EconomySystem:
    def __init__(self):
        self.user_balances = {}  # user_id: balance
        self.daily_claimed = {}  # user_id: last_claim_date
        
    def get_balance(self, user_id):
        return self.user_balances.get(user_id, 100)  # Starting balance: 100 K-coins
    
    def add_money(self, user_id, amount):
        if user_id not in self.user_balances:
            self.user_balances[user_id] = 100
        self.user_balances[user_id] += amount
        return self.user_balances[user_id]
    
    def remove_money(self, user_id, amount):
        if user_id not in self.user_balances:
            self.user_balances[user_id] = 100
        self.user_balances[user_id] = max(0, self.user_balances[user_id] - amount)
        return self.user_balances[user_id]
    
    def transfer_money(self, from_user, to_user, amount):
        if self.get_balance(from_user) >= amount:
            self.remove_money(from_user, amount)
            self.add_money(to_user, amount)
            return True
        return False
    
    def can_claim_daily(self, user_id):
        today = datetime.now().date()
        last_claim = self.daily_claimed.get(user_id)
        return last_claim != today
    
    def claim_daily(self, user_id):
        if self.can_claim_daily(user_id):
            amount = random.randint(50, 200)
            self.add_money(user_id, amount)
            self.daily_claimed[user_id] = datetime.now().date()
            return amount
        return 0

# Global instances
economy = EconomySystem()
active_games = {}

class FunCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # ============ ECONOMY COMMANDS ============
    
    @commands.command(name='balance', aliases=['bal', 'money'])
    async def check_balance(self, ctx, member: discord.Member = None):
        """Check your or someone else's K-coin balance"""
        target = member or ctx.author
        balance = economy.get_balance(target.id)
        
        embed = discord.Embed(
            title=f"💰 {target.display_name}'s Wallet",
            description=f"**{balance:,} K-coins**",
            color=0xf1c40f
        )
        embed.set_thumbnail(url=target.display_avatar.url)
    
    @commands.command(name='daily')
    async def daily_coins(self, ctx):
        """Claim your daily K-coins"""
        user_id = ctx.author.id
        amount = economy.claim_daily(user_id)
        
        if amount > 0:
            embed = discord.Embed(
                title="🎁 Daily Reward Claimed!",
                description=f"You received **{amount} K-coins**!",
                color=0x2ecc71
            )
            embed.add_field(
                name="New Balance", 
                value=f"{economy.get_balance(user_id):,} K-coins", 
                inline=False
            )
        else:
            embed = discord.Embed(
                title="⏰ Daily Reward Already Claimed",
                description="Come back tomorrow for your next daily reward!",
                color=0xe74c3c
            )
    @commands.command(name='give', aliases=['pay', 'transfer'])
    async def give_money(self, ctx, member: discord.Member, amount: int):
        """Give K-coins to another user"""
        if member.bot:
            await ctx.send("You can't give money to bots!")
            return
        
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
        
        if economy.transfer_money(ctx.author.id, member.id, amount):
            embed = discord.Embed(
                title="💸 Money Transferred",
                description=f"{ctx.author.mention} gave **{amount:,} K-coins** to {member.mention}",
                color=0x2ecc71
            )
            embed.add_field(
                name=f"{ctx.author.display_name}'s Balance",
                value=f"{economy.get_balance(ctx.author.id):,} K-coins",
                inline=True
            )
            embed.add_field(
                name=f"{member.display_name}'s Balance",
                value=f"{economy.get_balance(member.id):,} K-coins",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="❌ Insufficient Funds",
                description=f"You don't have enough K-coins! You have {economy.get_balance(ctx.author.id):,} K-coins.",
                color=0xe74c3c
            )
    @commands.command(name='richest', aliases=['leaderboard', 'top'])
    async def money_leaderboard(self, ctx):
        """Show the richest users"""
        if not economy.user_balances:
            await ctx.send("No one has any money yet!")
            return
        
        sorted_users = sorted(economy.user_balances.items(), key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="💎 Richest Users",
            description="Top 10 wealthiest members",
            color=0xf1c40f
        )
        
        for i, (user_id, balance) in enumerate(sorted_users[:10]):
            try:
                user = self.bot.get_user(user_id)
                if user:
                    rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"**{i+1}.**"
                    embed.add_field(
                        name=f"{rank_emoji} {user.display_name}",
                        value=f"{balance:,} K-coins",
                        inline=False
                    )
            except:
                continue
    @commands.command(name='grant')
    @commands.has_permissions(administrator=True)
    async def grant_money(self, ctx, member: discord.Member, amount: int):
        """[ADMIN] Grant K-coins to a user"""
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
        
        new_balance = economy.add_money(member.id, amount)
        
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
        embed.set_footer(text=f"Granted by {ctx.author.display_name}")
    
    # ============ SINGLE PLAYER GAMES ============
    
    @commands.command(name='flip', aliases=['coinflip'])
    async def coin_flip(self, ctx, bet: int = 0):
        """Flip a coin and optionally bet K-coins"""
        result = random.choice(['Heads', 'Tails'])
        
        if bet <= 0:
            embed = discord.Embed(
                title="🪙 Coin Flip",
                description=f"The coin landed on **{result}**!",
                color=0x3498db
            )
        if bet <= 0:
            embed = discord.Embed(
                title="🪙 Coin Flip",
                description=f"The coin landed on **{result}**!",
                color=0x3498db
            )
            return
            
        user_balance = economy.get_balance(ctx.author.id)
        if bet > user_balance:
            await ctx.send(f"You don't have enough K-coins! You have {user_balance:,} K-coins.")
            return
        
        # Player chooses heads or tails
        embed = discord.Embed(
            title="🪙 Choose Your Side",
            description="React with 👤 for Heads or 🔄 for Tails",
            color=0x3498db
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction('👤')
        await message.add_reaction('🔄')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['👤', '🔄'] and reaction.message.id == message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            choice = 'Heads' if str(reaction.emoji) == '👤' else 'Tails'
            
            won = choice == result
            if won:
                winnings = bet * 2
                economy.add_money(ctx.author.id, winnings)
                embed = discord.Embed(
                    title="🎉 You Won!",
                    description=f"The coin landed on **{result}**!\nYou won **{winnings:,} K-coins**!",
                    color=0x2ecc71
                )
            else:
                economy.remove_money(ctx.author.id, bet)
                embed = discord.Embed(
                    title="😢 You Lost!",
                    description=f"The coin landed on **{result}**!\nYou lost **{bet:,} K-coins**.",
                    color=0xe74c3c
                )
            
            embed.add_field(
                name="New Balance",
                value=f"{economy.get_balance(ctx.author.id):,} K-coins",
                inline=False
            )
            
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Time's Up",
                description="You took too long to choose!",
                color=0x95a5a6
            )
    
    @commands.command(name='slots', aliases=['slot'])
    async def slot_machine(self, ctx, bet: int = 0):
        """Play the slot machine"""
        if bet <= 0:
            await ctx.send("Please specify a bet amount: `!slots 50`")
            return
        
        user_balance = economy.get_balance(ctx.author.id)
        if bet > user_balance:
            await ctx.send(f"You don't have enough K-coins! You have {user_balance:,} K-coins.")
            return
        
        symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣']
        weights = [30, 25, 20, 15, 7, 2, 1]  # Different probabilities
        
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
            economy.add_money(ctx.author.id, winnings - bet)  # Subtract original bet
            embed = discord.Embed(
                title="🎰 SLOT MACHINE",
                description=f"{''.join(result)}\n\n🎉 **YOU WON {winnings:,} K-COINS!**",
                color=0x2ecc71
            )
        else:
            economy.remove_money(ctx.author.id, bet)
            embed = discord.Embed(
                title="🎰 SLOT MACHINE",
                description=f"{''.join(result)}\n\n😢 You lost {bet:,} K-coins",
                color=0xe74c3c
            )
        
        embed.add_field(
            name="New Balance",
            value=f"{economy.get_balance(ctx.author.id):,} K-coins",
            inline=False
        )
        
    
    @commands.command(name='dice', aliases=['roll'])
    async def dice_game(self, ctx, sides: int = 6):
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
            economy.add_money(ctx.author.id, bonus)
            embed.add_field(
                name="🎉 Perfect Roll Bonus!",
                value=f"You got the maximum roll and earned {bonus} K-coins!",
                inline=False
            )
            embed.add_field(
                name="New Balance",
                value=f"{economy.get_balance(ctx.author.id):,} K-coins",
                inline=False
            )
        
    @commands.command(name='8ball')
    async def magic_8ball(self, ctx, *, question):
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
        
    @commands.command(name='rps')
    async def rock_paper_scissors(self, ctx, choice: str = ""):
        """Play Rock Paper Scissors against the bot"""
        if not choice:
            embed = discord.Embed(
                title="✂️ Rock Paper Scissors",
                description="Choose your move by typing: `!rps rock`, `!rps paper`, or `!rps scissors`",
                color=0x3498db
            )
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
        elif (choice == 'rock' and bot_choice == 'scissors') or \
             (choice == 'paper' and bot_choice == 'rock') or \
             (choice == 'scissors' and bot_choice == 'paper'):
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
            description=f"You: {choice_emojis[choice]} {choice.title()}\nBot: {choice_emojis[bot_choice]} {bot_choice.title()}\n\n**{result}**",
            color=color
        )
        
        if reward > 0:
            economy.add_money(ctx.author.id, reward)
            embed.add_field(
                name="Reward",
                value=f"+{reward} K-coins",
                inline=True
            )
            embed.add_field(
                name="New Balance",
                value=f"{economy.get_balance(ctx.author.id):,} K-coins",
                inline=True
            )
    # ============ MULTIPLAYER GAMES ============
    
    @commands.command(name='trivia')
    async def trivia_game(self, ctx):
        """Start a multiplayer trivia game"""
        # Free trivia API
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
                
                embed.set_footer(text="React with the number of your answer! 15 seconds to respond.")
                
                message = await ctx.send(embed=embed)
                for i in range(len(all_answers)):
                    await message.add_reaction(answer_emojis[i])
                
                # Wait for reactions
                participants = {}
                start_time = time.time()
                
                def check(reaction, user):
                    return not user.bot and str(reaction.emoji) in answer_emojis[:len(all_answers)] and reaction.message.id == message.id
                
                while time.time() - start_time < 15:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=1.0, check=check)
                        if user.id not in participants:
                            answer_index = answer_emojis.index(str(reaction.emoji))
                            participants[user.id] = {
                                'user': user,
                                'answer': answer_index,
                                'time': time.time() - start_time
                            }
                    except asyncio.TimeoutError:
                        continue
                
                # Calculate results
                winners = []
                for user_id, data in participants.items():
                    if data['answer'] == correct_index:
                        winners.append(data)
                
                # Sort winners by response time
                winners.sort(key=lambda x: x['time'])
                
                result_embed = discord.Embed(
                    title="🏆 Trivia Results",
                    description=f"**Correct Answer:** {answer_emojis[correct_index]} {correct_answer}",
                    color=0x2ecc71
                )
                
                if winners:
                    winner_text = ""
                    for i, winner in enumerate(winners[:5]):  # Top 5 winners
                        points = [50, 30, 20, 15, 10][i] if i < 5 else 5
                        economy.add_money(winner['user'].id, points)
                        place = ["🥇", "🥈", "🥉", "4th", "5th"][i] if i < 5 else f"{i+1}th"
                        winner_text += f"{place} {winner['user'].display_name} (+{points} K-coins)\n"
                    
                    result_embed.add_field(
                        name="Winners",
                        value=winner_text,
                        inline=False
                    )
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
    async def countdown_game(self, ctx, target: int = 0):
        """Multiplayer countdown game - get closest to the target number"""
        if target <= 0:
            target = random.randint(1, 1000)
        
        embed = discord.Embed(
            title="🎯 Countdown Game",
            description=f"**Target Number:** {target}\n\nType a number to guess! Closest guess wins.\n⏰ 20 seconds to guess!",
            color=0xf39c12
        )
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
                message = await self.bot.wait_for('message', timeout=1.0, check=check)
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
        
        # Find winner (closest guess)
        winner_data = min(guesses.values(), key=lambda x: x['difference'])
        
        result_embed = discord.Embed(
            title="🏆 Countdown Results",
            description=f"**Target:** {target}\n**Winner:** {winner_data['user'].display_name}",
            color=0x2ecc71
        )
        
        # Award points based on accuracy
        if winner_data['difference'] == 0:
            points = 100  # Exact guess
        elif winner_data['difference'] <= 5:
            points = 75   # Very close
        elif winner_data['difference'] <= 20:
            points = 50   # Close
        else:
            points = 25   # Participated
        
        economy.add_money(winner_data['user'].id, points)
        
        result_embed.add_field(
            name="Winning Guess",
            value=f"{winner_data['guess']} (off by {winner_data['difference']})",
            inline=True
        )
        result_embed.add_field(
            name="Prize",
            value=f"{points} K-coins",
            inline=True
        )
        
        # Show other top guesses
        sorted_guesses = sorted(guesses.values(), key=lambda x: x['difference'])
        other_guesses = []
        for i, guess_data in enumerate(sorted_guesses[1:6]):  # Top 5 after winner
            other_guesses.append(f"{guess_data['user'].display_name}: {guess_data['guess']}")
        
        if other_guesses:
            result_embed.add_field(
                name="Other Close Guesses",
                value="\n".join(other_guesses),
                inline=False
            )
        
        await ctx.send(embed=result_embed)
    
    @commands.command(name='racing', aliases=['race'])
    async def racing_game(self, ctx):
        """Multiplayer racing game - react fastest to win"""
        embed = discord.Embed(
            title="🏁 Racing Game",
            description="Get ready to race! React to the 🏃 emoji when it appears to win!\n\n⏰ Starting in 3 seconds...",
            color=0xe74c3c
        )
        
        # Random delay between 3-8 seconds
        await asyncio.sleep(random.uniform(3, 8))
        
        race_embed = discord.Embed(
            title="🏁 GO! 🏃",
            description="**React NOW!**",
            color=0x2ecc71
        )
        
        await message.edit(embed=race_embed)
        await message.add_reaction('🏃')
        
        def check(reaction, user):
            return not user.bot and str(reaction.emoji) == '🏃' and reaction.message.id == message.id
        
        try:
            reaction, winner = await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
            
            # Award winner
            points = random.randint(75, 150)
            economy.add_money(winner.id, points)
            
            result_embed = discord.Embed(
                title="🏆 Race Winner!",
                description=f"**{winner.display_name}** won the race!",
                color=0xf1c40f
            )
            result_embed.add_field(
                name="Prize",
                value=f"{points} K-coins",
                inline=True
            )
            result_embed.add_field(
                name="New Balance",
                value=f"{economy.get_balance(winner.id):,} K-coins",
                inline=True
            )
            
            await message.edit(embed=result_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="🏁 Race Timeout",
                description="No one reacted in time! Race ended.",
                color=0x95a5a6
            )
            await message.edit(embed=timeout_embed)
    
    @commands.command(name='memory')
    async def memory_game(self, ctx):
        """Multiplayer memory game - remember the sequence"""
        sequence_length = random.randint(4, 8)
        sequence = [random.choice(['🔴', '🟢', '🔵', '🟡']) for _ in range(sequence_length)]
        
        embed = discord.Embed(
            title="🧠 Memory Game",
            description="Memorize this sequence! You'll have 5 seconds to study it.\n\n" + " ".join(sequence),
            color=0x9b59b6
        )
        
        message = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        
        # Hide the sequence
        hidden_embed = discord.Embed(
            title="🧠 Memory Game",
            description=f"Now type the sequence of {sequence_length} emojis!\n🔴🟢🔵🟡\n\n⏰ 30 seconds to answer!",
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
                user_message = await self.bot.wait_for('message', timeout=1.0, check=check)
                user_sequence = user_message.content.replace(" ", "")
                
                if user_message.author.id not in participants:
                    if user_sequence == correct_sequence:
                        participants[user_message.author.id] = {
                            'user': user_message.author,
                            'correct': True,
                            'time': time.time() - start_time
                        }
                        await user_message.add_reaction('✅')
                    else:
                        participants[user_message.author.id] = {
                            'user': user_message.author,
                            'correct': False,
                            'time': time.time() - start_time
                        }
                        await user_message.add_reaction('❌')
            except asyncio.TimeoutError:
                continue
        
        # Calculate results
        winners = [p for p in participants.values() if p['correct']]
        winners.sort(key=lambda x: x['time'])
        
        result_embed = discord.Embed(
            title="🧠 Memory Game Results",
            description=f"**Correct Sequence:** {' '.join(sequence)}",
            color=0x2ecc71
        )
        
        if winners:
            winner_text = ""
            for i, winner in enumerate(winners[:3]):  # Top 3
                points = [100, 60, 40][i] if i < 3 else 20
                economy.add_money(winner['user'].id, points)
                place = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}th"
                winner_text += f"{place} {winner['user'].display_name} ({winner['time']:.1f}s) +{points} K-coins\n"
            
            result_embed.add_field(
                name="Winners",
                value=winner_text,
                inline=False
            )
        else:
            result_embed.add_field(
                name="Results",
                value="No one got the sequence right! Try again next time.",
                inline=False
            )

    @commands.command(name='auction')
    async def auction_game(self, ctx):
        """Multiplayer auction - bid on mystery prizes"""
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
            description=f"**Mystery Item Up for Auction!**\n\nStarting bid: **50 K-coins**\nType your bid amount to participate!\n\n⏰ Auction ends in 30 seconds!",
            color=0xf39c12
        )
        embed.set_footer(text="Highest bidder wins the mystery prize!")
        
        
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
                bid_message = await self.bot.wait_for('message', timeout=1.0, check=check)
                bid_amount = int(bid_message.content)
                user_balance = economy.get_balance(bid_message.author.id)
                
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
        
        # Find winner
        winner_id = max(bids.keys(), key=lambda x: bids[x])
        winning_bid = bids[winner_id]
        winner = self.bot.get_user(winner_id)
        
        # Process payment
        economy.remove_money(winner_id, winning_bid)
        economy.add_money(winner_id, prize["value"])
        
        result_embed = discord.Embed(
            title="🏆 Auction Results",
            description=f"**Winner:** {winner.display_name}\n**Winning Bid:** {winning_bid:,} K-coins",
            color=0x2ecc71
        )
        
        result_embed.add_field(
            name="Prize Revealed",
            value=f"{prize['emoji']} **{prize['name']}**\nValue: {prize['value']} K-coins",
            inline=True
        )
        
        net_gain = prize["value"] - winning_bid
        result_embed.add_field(
            name="Net Result",
            value=f"{'Profit' if net_gain > 0 else 'Loss'}: {abs(net_gain):,} K-coins",
            inline=True
        )
        
        result_embed.add_field(
            name="New Balance",
            value=f"{economy.get_balance(winner_id):,} K-coins",
            inline=True
        )
        
        await ctx.send(embed=result_embed)

# Function to add to your bot
def setup(bot):
    bot.add_cog(FunCommandsCog(bot))

async def setup(bot):
    try:
        await bot.add_cog(YourCogClassName(bot))
    except Exception as e:
        print(f"🚨 Forced setup error bypass in discord_fun_commands: {type(e).__name__} - {e}")

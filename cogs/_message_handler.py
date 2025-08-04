import discord
from discord.ext import commands
import asyncio
import time
import logging
from collections import defaultdict

class MessageHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("MessageHandler")

        # Cache last message timestamps per user for cooldowns (command name -> timestamp)
        self.user_cooldowns = defaultdict(lambda: defaultdict(float))

        # Global filter config (example banned words)
        self.banned_keywords = {"badword", "someotherbadword"}

        # Cooldown settings (seconds) per command (override as needed)
        self.command_cooldowns = {
            "balance": 5,
            "daily": 86400,
            "give": 10,
            "flip": 3,
            "slots": 3,
            "dice": 3,
            "8ball": 3,
            "rps": 3,
            "trivia": 30,
            "countdown": 30,
            "racing": 10,
            "memory": 30,
            "auction": 30,
            # add more command cooldowns here
        }

    # ===== Helper Methods =====

    def is_dm(self, message):
        return isinstance(message.channel, discord.DMChannel)

    def contains_banned_word(self, content):
        lowered = content.lower()
        return any(bad in lowered for bad in self.banned_keywords)

    def check_cooldown(self, user_id, command_name):
        """
        Returns (bool, float)
        bool: True if user can run command now, False if still cooling down
        float: seconds left for cooldown (0 if ready)
        """
        now = time.time()
        last_used = self.user_cooldowns[user_id].get(command_name, 0)
        cooldown_time = self.command_cooldowns.get(command_name, 0)
        elapsed = now - last_used
        if elapsed >= cooldown_time:
            return True, 0
        else:
            return False, cooldown_time - elapsed

    def update_cooldown(self, user_id, command_name):
        self.user_cooldowns[user_id][command_name] = time.time()

    # ===== Hooks =====

    async def pre_command_hook(self, message, command_name):
        """
        Called before processing commands.
        Return False to cancel command processing.
        """
        # Filter banned words globally - just flag, no action here
        if self.contains_banned_word(message.content):
            self.logger.warning(f"Message from {message.author} contains banned words: {message.content}")

        # Check cooldown for the command
        can_run, time_left = self.check_cooldown(message.author.id, command_name)
        if not can_run:
            self.logger.info(f"User {message.author} tried command '{command_name}' but is on cooldown ({time_left:.1f}s left)")
            # We don't send messages here, just block command processing silently
            return False

        return True

    async def post_command_hook(self, message, command_name, success=True):
        """
        Called after a command runs.
        Use for logging, updating stats, etc.
        """
        if success:
            self.update_cooldown(message.author.id, command_name)
            self.logger.info(f"User {message.author} successfully ran command '{command_name}'")
        else:
            self.logger.info(f"User {message.author} failed command '{command_name}'")

    # ===== Event Listener =====

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and self
        if message.author.bot:
            return

        # Log all messages
        self.logger.debug(f"Message from {message.author} (DM: {self.is_dm(message)}): {message.content}")

        # Determine if message invokes a command
        ctx = await self.bot.get_context(message)

        if ctx.command is None:
            # No command invoked, handle global triggers or filters if you want here
            # e.g. check for auto-replies, triggers, moderation flags
            # Just log for now
            self.logger.debug(f"No command detected in message from {message.author}")
            return

        command_name = ctx.command.name

        # Run pre-command hook, cancel command if False returned
        can_proceed = await self.pre_command_hook(message, command_name)
        if not can_proceed:
            return  # silently ignore command execution

        # Process the command safely, catch exceptions to keep handler alive
        try:
            await self.bot.invoke(ctx)
            # Post-command hook for success
            await self.post_command_hook(message, command_name, success=True)
        except Exception as e:
            self.logger.error(f"Exception during command '{command_name}' by user {message.author}: {e}", exc_info=True)
            # Post-command hook for failure
            await self.post_command_hook(message, command_name, success=False)

def setup(bot):
    bot.add_cog(MessageHandler(bot))

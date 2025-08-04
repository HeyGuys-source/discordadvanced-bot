import logging

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))

logger.addHandler(stream_handler)

# Assign it to your bot
bot.logger = logger

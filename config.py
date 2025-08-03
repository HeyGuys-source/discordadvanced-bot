import os

class Config:
    """Configuration class for the bot"""
    
    # Bot settings
    PREFIX = os.getenv('BOT_PREFIX', '!')
    DESCRIPTION = 'Advanced Discord Moderation Bot'
    
    # Database settings
    DATABASE_PATH = 'bot_database.db'
    
    # Web dashboard settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
    DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
    DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/callback')
    
    # AutoMod settings
    SPAM_THRESHOLD = 5  # Messages per 10 seconds
    SPAM_INTERVAL = 10  # Seconds
    MAX_MENTIONS = 5    # Max mentions per message
    MAX_LINKS = 3       # Max links per message
    
    # Logging settings
    LOG_CHANNEL_NAME = 'mod-logs'
    
    # Starboard settings
    STARBOARD_THRESHOLD = 3  # Minimum stars required
    STARBOARD_CHANNEL_NAME = 'starboard'
    
    # Colors
    COLOR_PRIMARY = 0x5865F2    # Discord Blurple
    COLOR_SUCCESS = 0x57F287    # Green
    COLOR_WARNING = 0xFEE75C    # Yellow
    COLOR_ERROR = 0xED4245      # Red
    COLOR_INFO = 0x5865F2       # Blue
    
    # Emojis
    EMOJI_SUCCESS = '✅'
    EMOJI_ERROR = '❌'
    EMOJI_WARNING = '⚠️'
    EMOJI_INFO = 'ℹ️'
    EMOJI_STAR = '⭐'
    
    # Rate limiting
    RATE_LIMIT_COMMANDS = 5  # Commands per minute
    RATE_LIMIT_WINDOW = 60   # Window in seconds

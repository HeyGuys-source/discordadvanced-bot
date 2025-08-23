import aiosqlite
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

class Database:
    """Database handler for the bot"""
    
    def __init__(self, db_path: str = 'bot_database.db'):
        self.db_path = db_path
        self.conn = None
    
    async def init_db(self):
        """Initialize the database with required tables"""
        self.conn = await aiosqlite.connect(self.db_path)
        
        # Enable foreign keys
        await self.conn.execute('PRAGMA foreign_keys = ON')
        
        # Create tables
        await self._create_tables()
        await self.conn.commit()
        logging.info('Database initialized')
    
    async def _create_tables(self):
        """Create all required database tables"""
        
        # Guild settings
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                log_channel_id INTEGER,
                welcome_channel_id INTEGER,
                welcome_message TEXT,
                farewell_message TEXT,
                auto_role_id INTEGER,
                starboard_channel_id INTEGER,
                starboard_threshold INTEGER DEFAULT 3,
                automod_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Moderation logs
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS moderation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                action TEXT,
                reason TEXT,
                duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User warnings
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Reaction roles
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS reaction_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                message_id INTEGER,
                channel_id INTEGER,
                role_id INTEGER,
                emoji TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Custom commands
        await self.conn.execute(''')
            CREATE TABLE IF NOT EXISTS custom_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                trigger TEXT,
                response TEXT,
                created_by INTEGER,
                uses INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # AutoMod violations
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS automod_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                violation_type TEXT,
                content TEXT,
                action_taken TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Starboard entries
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS starboard_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                original_message_id INTEGER UNIQUE,
                starboard_message_id INTEGER,
                channel_id INTEGER,
                author_id INTEGER,
                star_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User levels for XP system
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS user_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                total_xp INTEGER DEFAULT 0,
                last_message TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id)
            )
        ''')
        
        # Event logs
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                event_type TEXT,
                user_id INTEGER,
                channel_id INTEGER,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

            await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS alt_members (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                username TEXT NOT NULL,
                display_name TEXT,
                discriminator TEXT,
                created_at TIMESTAMP NOT NULL,
                joined_at TIMESTAMP,
                avatar_url TEXT,
                is_bot BOOLEAN DEFAULT 0,
                roles TEXT,
                premium_since TIMESTAMP,
                status TEXT,
                message_count_7d INTEGER DEFAULT 0,
                message_count_30d INTEGER DEFAULT 0,
                channels_used INTEGER DEFAULT 0,
                avg_message_length REAL DEFAULT 0,
                reaction_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alt Detection - Analysis results
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS alt_analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                member_ids TEXT NOT NULL,
                confidence_score INTEGER NOT NULL,
                evidence TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alt Detection - Pattern cache
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS alt_pattern_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alt Detection - Message timing
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS alt_message_timing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                member_id INTEGER,
                channel_id INTEGER,
                message_timestamp TIMESTAMP NOT NULL,
                message_length INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for alt detection tables
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_alt_members_guild_id ON alt_members(guild_id)')
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_alt_members_created_at ON alt_members(created_at)')
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_alt_analysis_guild_id ON alt_analysis_results(guild_id)')
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_alt_analysis_confidence ON alt_analysis_results(confidence_score)')
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_alt_pattern_guild_type ON alt_pattern_cache(guild_id, pattern_type)')
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_alt_timing_member_id ON alt_message_timing(member_id)')
        await self.conn.execute('CREATE INDEX IF NOT EXISTS idx_alt_timing_guild_id ON alt_message_timing(guild_id)')
        
    async def init_guild(self, guild_id: int):
        """Initialize a guild in the database"""
        await self.conn.execute('''
            INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)
        ''', (guild_id,))
        await self.conn.commit()
    
    # Guild settings methods
    async def get_guild_settings(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get guild settings"""
        cursor = await self.conn.execute('''
            SELECT * FROM guild_settings WHERE guild_id = ?
        ''', (guild_id,))
        row = await cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    async def update_guild_setting(self, guild_id: int, setting: str, value: Any):
        """Update a specific guild setting"""
        await self.conn.execute(f'''
            UPDATE guild_settings SET {setting} = ? WHERE guild_id = ?
        ''', (value, guild_id))
        await self.conn.commit()
    
    # Moderation methods
    async def add_moderation_log(self, guild_id: int, user_id: int, moderator_id: int, 
                                action: str, reason: str, duration: Optional[int] = None):
        """Add a moderation log entry"""
        await self.conn.execute('''
            INSERT INTO moderation_logs (guild_id, user_id, moderator_id, action, reason, duration)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (guild_id, user_id, moderator_id, action, reason, duration))
        await self.conn.commit()
    
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str):
        """Add a warning to a user"""
        await self.conn.execute('''
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
            VALUES (?, ?, ?, ?)
        ''', (guild_id, user_id, moderator_id, reason))
        await self.conn.commit()
    
    async def get_user_warnings(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get all warnings for a user"""
        cursor = await self.conn.execute('''
            SELECT * FROM warnings WHERE guild_id = ? AND user_id = ?
            ORDER BY created_at DESC
        ''', (guild_id, user_id))
        rows = await cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    # Reaction roles methods
    async def add_reaction_role(self, guild_id: int, message_id: int, channel_id: int, 
                               role_id: int, emoji: str):
        """Add a reaction role"""
        await self.conn.execute('''
            INSERT INTO reaction_roles (guild_id, message_id, channel_id, role_id, emoji)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, message_id, channel_id, role_id, emoji))
        await self.conn.commit()
    
    async def get_reaction_role(self, message_id: int, emoji: str) -> Optional[Dict[str, Any]]:
        """Get reaction role by message ID and emoji"""
        cursor = await self.conn.execute('''
            SELECT * FROM reaction_roles WHERE message_id = ? AND emoji = ?
        ''', (message_id, emoji))
        row = await cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    async def remove_reaction_role(self, message_id: int, emoji: str):
        """Remove a reaction role"""
        await self.conn.execute('''
            DELETE FROM reaction_roles WHERE message_id = ? AND emoji = ?
        ''', (message_id, emoji))
        await self.conn.commit()
    
    # Custom commands methods
    async def add_custom_command(self, guild_id: int, trigger: str, response: str, created_by: int):
        """Add a custom command"""
        await self.conn.execute('''
            INSERT INTO custom_commands (guild_id, trigger, response, created_by)
            VALUES (?, ?, ?, ?)
        ''', (guild_id, trigger, response, created_by))
        await self.conn.commit()
    
    async def get_custom_command(self, guild_id: int, trigger: str) -> Optional[Dict[str, Any]]:
        """Get custom command by trigger"""
        cursor = await self.conn.execute('''
            SELECT * FROM custom_commands WHERE guild_id = ? AND trigger = ?
        ''', (guild_id, trigger))
        row = await cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    async def increment_command_usage(self, command_id: int):
        """Increment command usage counter"""
        await self.conn.execute('''
            UPDATE custom_commands SET uses = uses + 1 WHERE id = ?
        ''', (command_id,))
        await self.conn.commit()
    
    # AutoMod methods
    async def add_automod_violation(self, guild_id: int, user_id: int, violation_type: str, 
                                   content: str, action_taken: str):
        """Add an automod violation"""
        await self.conn.execute('''
            INSERT INTO automod_violations (guild_id, user_id, violation_type, content, action_taken)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, user_id, violation_type, content, action_taken))
        await self.conn.commit()
    
    # Starboard methods
    async def add_starboard_entry(self, guild_id: int, original_message_id: int, 
                                 channel_id: int, author_id: int):
        """Add a starboard entry"""
        await self.conn.execute('''
            INSERT INTO starboard_entries (guild_id, original_message_id, channel_id, author_id)
            VALUES (?, ?, ?, ?)
        ''', (guild_id, original_message_id, channel_id, author_id))
        await self.conn.commit()
    
    async def get_starboard_entry(self, original_message_id: int) -> Optional[Dict[str, Any]]:
        """Get starboard entry by original message ID"""
        cursor = await self.conn.execute('''
            SELECT * FROM starboard_entries WHERE original_message_id = ?
        ''', (original_message_id,))
        row = await cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    async def update_star_count(self, original_message_id: int, star_count: int):
        """Update star count for a starboard entry"""
        await self.conn.execute('''
            UPDATE starboard_entries SET star_count = ? WHERE original_message_id = ?
        ''', (star_count, original_message_id))
        await self.conn.commit()
    
    # Event logging methods
    async def add_event_log(self, guild_id: int, event_type: str, user_id: Optional[int] = None,
                           channel_id: Optional[int] = None, data: Optional[Dict] = None):
        """Add an event log"""
        data_json = json.dumps(data) if data else None
        await self.conn.execute('''
            INSERT INTO event_logs (guild_id, event_type, user_id, channel_id, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (guild_id, event_type, user_id, channel_id, data_json))
        await self.conn.commit()
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

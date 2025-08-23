import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class AltDetectionDB:
    """Database handler for alt detection data storage and retrieval."""
    
    def __init__(self, db_path: str = "alt_detection.db"):
        self.db_path = db_path
        self.connection = None
        
    async def initialize(self):
        """Initialize the database and create necessary tables."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            await self._create_tables()
            logger.info("Alt detection database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables for storing member and analysis data."""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        cursor = self.connection.cursor()
        
        # Members table for storing comprehensive member data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                display_name TEXT,
                discriminator TEXT,
                created_at TIMESTAMP NOT NULL,
                joined_at TIMESTAMP,
                avatar_url TEXT,
                is_bot BOOLEAN DEFAULT FALSE,
                roles TEXT,  -- JSON array of role IDs
                premium_since TIMESTAMP,
                status TEXT,
                message_count_7d INTEGER DEFAULT 0,
                message_count_30d INTEGER DEFAULT 0,
                channels_used INTEGER DEFAULT 0,
                avg_message_length REAL DEFAULT 0,
                reaction_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes separately
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_guild_id ON members(guild_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_created_at ON members(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_joined_at ON members(joined_at)")
        
        # Analysis results table for storing detection results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                member_ids TEXT NOT NULL,  -- JSON array of member IDs
                confidence_score INTEGER NOT NULL,
                evidence TEXT NOT NULL,   -- JSON array of evidence
                analysis_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes separately
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_guild_id ON analysis_results(guild_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_confidence ON analysis_results(confidence_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_results(created_at)")
        
        # Pattern cache table for storing detected patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,  -- JSON data
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes separately
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pattern_guild_type ON pattern_cache(guild_id, pattern_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pattern_expires_at ON pattern_cache(expires_at)")
        
        # Message timing table for behavioral analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_timing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_timestamp TIMESTAMP NOT NULL,
                message_length INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes separately
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timing_member_id ON message_timing(member_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timing_guild_id ON message_timing(guild_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timing_timestamp ON message_timing(message_timestamp)")
        
        self.connection.commit()
        logger.info("Database tables created/verified successfully")
    
    async def store_member_batch(self, guild_id: int, members: List[Dict]):
        """Store a batch of member data efficiently."""
        if not members or not self.connection:
            return
        
        cursor = self.connection.cursor()
        
        try:
            # Clear existing data for the guild
            cursor.execute("DELETE FROM members WHERE guild_id = ?", (guild_id,))
            
            # Prepare member data for insertion
            member_data = []
            for member in members:
                roles_json = json.dumps(member.get('roles', []))
                
                member_data.append((
                    member['id'],
                    guild_id,
                    member['username'],
                    member.get('display_name'),
                    member.get('discriminator'),
                    member['created_at'].isoformat() if member.get('created_at') else None,
                    member['joined_at'].isoformat() if member.get('joined_at') else None,
                    member.get('avatar_url'),
                    member.get('is_bot', False),
                    roles_json,
                    member['premium_since'].isoformat() if member.get('premium_since') else None,
                    member.get('status'),
                    member.get('message_count_7d', 0),
                    member.get('message_count_30d', 0),
                    member.get('channels_used', 0),
                    member.get('avg_message_length', 0),
                    member.get('reaction_count', 0)
                ))
            
            # Batch insert
            cursor.executemany("""
                INSERT OR REPLACE INTO members (
                    id, guild_id, username, display_name, discriminator,
                    created_at, joined_at, avatar_url, is_bot, roles,
                    premium_since, status, message_count_7d, message_count_30d,
                    channels_used, avg_message_length, reaction_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, member_data)
            
            # Store message timing data
            timing_data = []
            for member in members:
                if 'message_times' in member and member['message_times']:
                    for timestamp in member['message_times']:
                        timing_data.append((
                            member['id'],
                            guild_id,
                            0,  # Channel ID (we'll use 0 as placeholder)
                            timestamp.isoformat(),
                            0   # Message length placeholder
                        ))
            
            if timing_data:
                cursor.executemany("""
                    INSERT INTO message_timing (
                        member_id, guild_id, channel_id, message_timestamp, message_length
                    ) VALUES (?, ?, ?, ?, ?)
                """, timing_data)
            
            self.connection.commit()
            logger.info(f"Stored data for {len(members)} members in guild {guild_id}")
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error storing member batch: {e}")
            raise
    
    async def get_guild_members(self, guild_id: int) -> List[Dict]:
        """Retrieve all members for a guild."""
        if not self.connection:
            return []
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM members WHERE guild_id = ?
                ORDER BY created_at ASC
            """, (guild_id,))
            
            rows = cursor.fetchall()
            members = []
            
            for row in rows:
                member_data = dict(row)
                # Parse JSON fields
                if member_data['roles']:
                    member_data['roles'] = json.loads(member_data['roles'])
                else:
                    member_data['roles'] = []
                
                # Parse datetime fields
                for field in ['created_at', 'joined_at', 'premium_since']:
                    if member_data[field]:
                        member_data[field] = datetime.fromisoformat(member_data[field])
                
                members.append(member_data)
            
            return members
            
        except Exception as e:
            logger.error(f"Error retrieving guild members: {e}")
            return []
    
    async def store_analysis_result(self, guild_id: int, result: Dict):
        """Store an analysis result."""
        if not self.connection:
            return
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO analysis_results (
                    guild_id, member_ids, confidence_score, evidence, analysis_type
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                guild_id,
                json.dumps(result['members']),
                result['confidence_score'],
                json.dumps(result['evidence']),
                result.get('analysis_type', 'comprehensive')
            ))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing analysis result: {e}")
            raise
    
    async def get_recent_analysis(self, guild_id: int, hours: int = 24) -> List[Dict]:
        """Get recent analysis results for a guild."""
        if not self.connection:
            return []
        cursor = self.connection.cursor()
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT * FROM analysis_results 
                WHERE guild_id = ? AND created_at > ?
                ORDER BY confidence_score DESC, created_at DESC
            """, (guild_id, cutoff_time.isoformat()))
            
            rows = cursor.fetchall()
            results = []
            
            for row in rows:
                result_data = dict(row)
                result_data['member_ids'] = json.loads(result_data['member_ids'])
                result_data['evidence'] = json.loads(result_data['evidence'])
                result_data['created_at'] = datetime.fromisoformat(result_data['created_at'])
                results.append(result_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving recent analysis: {e}")
            return []
    
    async def cache_pattern(self, guild_id: int, pattern_type: str, pattern_data: Dict, hours: int = 24):
        """Cache a detected pattern."""
        if not self.connection:
            return
        cursor = self.connection.cursor()
        
        try:
            expires_at = datetime.utcnow() + timedelta(hours=hours)
            
            cursor.execute("""
                INSERT OR REPLACE INTO pattern_cache (
                    guild_id, pattern_type, pattern_data, expires_at
                ) VALUES (?, ?, ?, ?)
            """, (
                guild_id,
                pattern_type,
                json.dumps(pattern_data),
                expires_at.isoformat()
            ))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error caching pattern: {e}")
    
    async def get_cached_pattern(self, guild_id: int, pattern_type: str) -> Optional[Dict]:
        """Retrieve a cached pattern if not expired."""
        if not self.connection:
            return None
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                SELECT pattern_data FROM pattern_cache 
                WHERE guild_id = ? AND pattern_type = ? AND expires_at > ?
                ORDER BY created_at DESC LIMIT 1
            """, (guild_id, pattern_type, datetime.utcnow().isoformat()))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row['pattern_data'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached pattern: {e}")
            return None
    
    async def cleanup_expired_data(self):
        """Clean up expired cache data and old analysis results."""
        if not self.connection:
            return
        cursor = self.connection.cursor()
        
        try:
            # Remove expired pattern cache
            cursor.execute("""
                DELETE FROM pattern_cache WHERE expires_at < ?
            """, (datetime.utcnow().isoformat(),))
            
            # Remove analysis results older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            cursor.execute("""
                DELETE FROM analysis_results WHERE created_at < ?
            """, (cutoff_date.isoformat(),))
            
            # Remove message timing data older than 7 days
            timing_cutoff = datetime.utcnow() - timedelta(days=7)
            cursor.execute("""
                DELETE FROM message_timing WHERE created_at < ?
            """, (timing_cutoff.isoformat(),))
            
            self.connection.commit()
            logger.info("Database cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
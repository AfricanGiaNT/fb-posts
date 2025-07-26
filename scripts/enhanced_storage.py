"""
Enhanced Storage System for Context Improvement
Implements SQLite database persistence for session data and user preferences.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

class EnhancedStorage:
    """Enhanced storage system with SQLite database persistence."""
    
    def __init__(self, db_path: str = "context_improvement.db"):
        """Initialize the enhanced storage system."""
        self.db_path = db_path
        self.lock = threading.Lock()
        
        # Ensure database directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_sessions INTEGER DEFAULT 0,
                        total_interactions INTEGER DEFAULT 0,
                        average_satisfaction REAL DEFAULT 0.0
                    )
                """)
                
                # Create sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        series_id TEXT,
                        filename TEXT,
                        original_markdown TEXT,
                        session_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        post_count INTEGER DEFAULT 0,
                        session_context TEXT,
                        state TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Create chat_history table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_message TEXT,
                        bot_response TEXT,
                        message_type TEXT,
                        context TEXT,  -- JSON string
                        satisfaction_score REAL,
                        regeneration_count INTEGER DEFAULT 0,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                    )
                """)
                
                # Create user_preferences table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id INTEGER PRIMARY KEY,
                        preferred_tones TEXT,  -- JSON array
                        audience_preferences TEXT,  -- JSON object
                        content_length_preferences TEXT,  -- JSON object
                        successful_patterns TEXT,  -- JSON array
                        avoided_patterns TEXT,  -- JSON array
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Create feedback_analysis table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS feedback_analysis (
                        user_id INTEGER PRIMARY KEY,
                        approval_rate REAL DEFAULT 0.0,
                        regeneration_patterns TEXT,  -- JSON array
                        common_edit_requests TEXT,  -- JSON array
                        successful_content_elements TEXT,  -- JSON array
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES feedback_analysis (user_id)
                    )
                """)
                
                # Create posts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        post_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        airtable_record_id TEXT,
                        post_content TEXT,
                        tone_used TEXT,
                        tone_reason TEXT,
                        parent_post_id TEXT,
                        relationship_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history (session_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history (timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_session_id ON posts (session_id)")
                
                conn.commit()
    
    def save_session(self, user_id: int, session: Dict) -> bool:
        """Save a complete session to the database."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Ensure user exists
                    self._ensure_user_exists(conn, user_id)
                    
                    # Save session
                    session_id = session.get('series_id')
                    conn.execute("""
                        INSERT OR REPLACE INTO sessions 
                        (session_id, user_id, series_id, filename, original_markdown, 
                         session_started, last_activity, post_count, session_context, state)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        user_id,
                        session.get('series_id'),
                        session.get('filename'),
                        session.get('original_markdown'),
                        session.get('session_started'),
                        session.get('last_activity'),
                        session.get('post_count', 0),
                        session.get('session_context'),
                        json.dumps(session.get('state'))
                    ))
                    
                    # Save chat history
                    chat_history = session.get('chat_history', [])
                    for entry in chat_history:
                        conn.execute("""
                            INSERT INTO chat_history 
                            (session_id, timestamp, user_message, bot_response, 
                             message_type, context, satisfaction_score, regeneration_count)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            session_id,
                            entry.get('timestamp'),
                            entry.get('user_message'),
                            entry.get('bot_response'),
                            entry.get('message_type'),
                            json.dumps(entry.get('context', {})),
                            entry.get('satisfaction_score'),
                            entry.get('regeneration_count', 0)
                        ))
                    
                    # Save posts
                    posts = session.get('posts', [])
                    for post in posts:
                        conn.execute("""
                            INSERT OR REPLACE INTO posts 
                            (post_id, session_id, airtable_record_id, post_content, 
                             tone_used, tone_reason, parent_post_id, relationship_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            post.get('post_id'),
                            session_id,
                            post.get('airtable_record_id'),
                            post.get('post_content'),
                            post.get('tone_used'),
                            post.get('tone_reason'),
                            post.get('parent_post_id'),
                            post.get('relationship_type')
                        ))
                    
                    # Update user statistics
                    self._update_user_statistics(conn, user_id)
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return False
    
    def load_session(self, user_id: int, session_id: str) -> Optional[Dict]:
        """Load a session from the database."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Load session
                    session_row = conn.execute("""
                        SELECT * FROM sessions WHERE session_id = ? AND user_id = ?
                    """, (session_id, user_id)).fetchone()
                    
                    if not session_row:
                        return None
                    
                    # Build session dictionary
                    session = {
                        'series_id': session_row[2],
                        'filename': session_row[3],
                        'original_markdown': session_row[4],
                        'session_started': session_row[5],
                        'last_activity': session_row[6],
                        'post_count': session_row[7],
                        'session_context': session_row[8],
                        'state': json.loads(session_row[9]) if session_row[9] else None,
                        'chat_history': [],
                        'posts': [],
                        'user_preferences': {},
                        'request_mapping': {},
                        'feedback_analysis': {}
                    }
                    
                    # Load chat history
                    chat_history_rows = conn.execute("""
                        SELECT * FROM chat_history WHERE session_id = ? ORDER BY timestamp
                    """, (session_id,)).fetchall()
                    
                    for row in chat_history_rows:
                        session['chat_history'].append({
                            'timestamp': row[2],
                            'user_message': row[3],
                            'bot_response': row[4],
                            'message_type': row[5],
                            'context': json.loads(row[6]) if row[6] else {},
                            'satisfaction_score': row[7],
                            'regeneration_count': row[8]
                        })
                    
                    # Load posts
                    posts_rows = conn.execute("""
                        SELECT * FROM posts WHERE session_id = ? ORDER BY created_at
                    """, (session_id,)).fetchall()
                    
                    for row in posts_rows:
                        session['posts'].append({
                            'post_id': row[1],
                            'airtable_record_id': row[2],
                            'post_content': row[3],
                            'tone_used': row[4],
                            'tone_reason': row[5],
                            'parent_post_id': row[6],
                            'relationship_type': row[7]
                        })
                    
                    # Load user preferences
                    prefs_row = conn.execute("""
                        SELECT * FROM user_preferences WHERE user_id = ?
                    """, (user_id,)).fetchone()
                    
                    if prefs_row:
                        session['user_preferences'] = {
                            'preferred_tones': json.loads(prefs_row[1]) if prefs_row[1] else [],
                            'audience_preferences': json.loads(prefs_row[2]) if prefs_row[2] else {},
                            'content_length_preferences': json.loads(prefs_row[3]) if prefs_row[3] else {},
                            'successful_patterns': json.loads(prefs_row[4]) if prefs_row[4] else [],
                            'avoided_patterns': json.loads(prefs_row[5]) if prefs_row[5] else []
                        }
                    
                    return session
                    
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return None
    
    def save_user_preferences(self, user_id: int, preferences: Dict) -> bool:
        """Save user preferences to the database."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Ensure user exists
                    self._ensure_user_exists(conn, user_id)
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO user_preferences 
                        (user_id, preferred_tones, audience_preferences, 
                         content_length_preferences, successful_patterns, avoided_patterns)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        json.dumps(preferences.get('preferred_tones', [])),
                        json.dumps(preferences.get('audience_preferences', {})),
                        json.dumps(preferences.get('content_length_preferences', {})),
                        json.dumps(preferences.get('successful_patterns', [])),
                        json.dumps(preferences.get('avoided_patterns', []))
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving user preferences: {str(e)}")
            return False
    
    def load_user_preferences(self, user_id: int) -> Dict:
        """Load user preferences from the database."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    row = conn.execute("""
                        SELECT * FROM user_preferences WHERE user_id = ?
                    """, (user_id,)).fetchone()
                    
                    if row:
                        return {
                            'preferred_tones': json.loads(row[1]) if row[1] else [],
                            'audience_preferences': json.loads(row[2]) if row[2] else {},
                            'content_length_preferences': json.loads(row[3]) if row[3] else {},
                            'successful_patterns': json.loads(row[4]) if row[4] else [],
                            'avoided_patterns': json.loads(row[5]) if row[5] else []
                        }
                    else:
                        return {
                            'preferred_tones': [],
                            'audience_preferences': {},
                            'content_length_preferences': {},
                            'successful_patterns': [],
                            'avoided_patterns': []
                        }
                        
        except Exception as e:
            logger.error(f"Error loading user preferences: {str(e)}")
            return {
                'preferred_tones': [],
                'audience_preferences': {},
                'content_length_preferences': {},
                'successful_patterns': [],
                'avoided_patterns': []
            }
    
    def save_feedback_analysis(self, user_id: int, feedback: Dict) -> bool:
        """Save feedback analysis to the database."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Ensure user exists
                    self._ensure_user_exists(conn, user_id)
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO feedback_analysis 
                        (user_id, approval_rate, regeneration_patterns, 
                         common_edit_requests, successful_content_elements)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        feedback.get('approval_rate', 0.0),
                        json.dumps(feedback.get('regeneration_patterns', [])),
                        json.dumps(feedback.get('common_edit_requests', [])),
                        json.dumps(feedback.get('successful_content_elements', []))
                    ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving feedback analysis: {str(e)}")
            return False
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """Get comprehensive user statistics."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Get user info
                    user_row = conn.execute("""
                        SELECT * FROM users WHERE user_id = ?
                    """, (user_id,)).fetchone()
                    
                    if not user_row:
                        return {"error": "User not found"}
                    
                    # Get session statistics
                    session_stats = conn.execute("""
                        SELECT COUNT(*) as total_sessions,
                               MAX(last_activity) as last_session,
                               SUM(post_count) as total_posts
                        FROM sessions WHERE user_id = ?
                    """, (user_id,)).fetchone()
                    
                    # Get interaction statistics
                    interaction_stats = conn.execute("""
                        SELECT COUNT(*) as total_interactions,
                               AVG(satisfaction_score) as avg_satisfaction,
                               COUNT(CASE WHEN satisfaction_score > 0.7 THEN 1 END) as high_satisfaction,
                               COUNT(CASE WHEN satisfaction_score < 0.4 THEN 1 END) as low_satisfaction
                        FROM chat_history ch
                        JOIN sessions s ON ch.session_id = s.session_id
                        WHERE s.user_id = ?
                    """, (user_id,)).fetchone()
                    
                    # Get recent activity
                    recent_activity = conn.execute("""
                        SELECT COUNT(*) as recent_interactions
                        FROM chat_history ch
                        JOIN sessions s ON ch.session_id = s.session_id
                        WHERE s.user_id = ? AND ch.timestamp > datetime('now', '-24 hours')
                    """, (user_id,)).fetchone()
                    
                    return {
                        "user_id": user_id,
                        "created_at": user_row[1],
                        "last_activity": user_row[2],
                        "total_sessions": session_stats[0] or 0,
                        "total_posts": session_stats[2] or 0,
                        "last_session": session_stats[1],
                        "total_interactions": interaction_stats[0] or 0,
                        "average_satisfaction": interaction_stats[1] or 0.0,
                        "high_satisfaction_count": interaction_stats[2] or 0,
                        "low_satisfaction_count": interaction_stats[3] or 0,
                        "recent_activity_24h": recent_activity[0] or 0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {"error": str(e)}
    
    def get_session_list(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get list of user's recent sessions."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    rows = conn.execute("""
                        SELECT session_id, filename, session_started, last_activity, post_count
                        FROM sessions 
                        WHERE user_id = ? 
                        ORDER BY last_activity DESC 
                        LIMIT ?
                    """, (user_id, limit)).fetchall()
                    
                    return [
                        {
                            "session_id": row[0],
                            "filename": row[1],
                            "session_started": row[2],
                            "last_activity": row[3],
                            "post_count": row[4]
                        }
                        for row in rows
                    ]
                    
        except Exception as e:
            logger.error(f"Error getting session list: {str(e)}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old data to prevent database bloat."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                    
                    # Delete old chat history
                    deleted_chat = conn.execute("""
                        DELETE FROM chat_history 
                        WHERE timestamp < ?
                    """, (cutoff_date.isoformat(),)).rowcount
                    
                    # Delete old sessions (and related data)
                    deleted_sessions = conn.execute("""
                        DELETE FROM sessions 
                        WHERE last_activity < ?
                    """, (cutoff_date.isoformat(),)).rowcount
                    
                    conn.commit()
                    return deleted_chat + deleted_sessions
                    
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            return 0
    
    def _ensure_user_exists(self, conn: sqlite3.Connection, user_id: int):
        """Ensure user exists in the database."""
        conn.execute("""
            INSERT OR IGNORE INTO users (user_id) VALUES (?)
        """, (user_id,))
    
    def _update_user_statistics(self, conn: sqlite3.Connection, user_id: int):
        """Update user statistics."""
        # Update last activity
        conn.execute("""
            UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?
        """, (user_id,))
        
        # Update total sessions
        conn.execute("""
            UPDATE users SET total_sessions = (
                SELECT COUNT(*) FROM sessions WHERE user_id = ?
            ) WHERE user_id = ?
        """, (user_id, user_id))
        
        # Update total interactions
        conn.execute("""
            UPDATE users SET total_interactions = (
                SELECT COUNT(*) FROM chat_history ch
                JOIN sessions s ON ch.session_id = s.session_id
                WHERE s.user_id = ?
            ) WHERE user_id = ?
        """, (user_id, user_id))
        
        # Update average satisfaction
        conn.execute("""
            UPDATE users SET average_satisfaction = (
                SELECT AVG(satisfaction_score) FROM chat_history ch
                JOIN sessions s ON ch.session_id = s.session_id
                WHERE s.user_id = ? AND satisfaction_score IS NOT NULL
            ) WHERE user_id = ?
        """, (user_id, user_id))
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    stats = {}
                    
                    # Table sizes
                    tables = ['users', 'sessions', 'chat_history', 'user_preferences', 'feedback_analysis', 'posts']
                    for table in tables:
                        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                        stats[f"{table}_count"] = count
                    
                    # Database size
                    db_size = Path(self.db_path).stat().st_size
                    stats['database_size_bytes'] = db_size
                    stats['database_size_mb'] = db_size / (1024 * 1024)
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {"error": str(e)} 
import sqlite3
import hashlib
from datetime import datetime
import os

DB_NAME = "brainybee.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            auth_provider TEXT, -- 'local', 'google', 'phone'
            total_stars INTEGER DEFAULT 0,
            created_at TIMESTAMP
        )
    ''')
    # Create game scores table
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_name TEXT,
            score INTEGER,
            played_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, auth_provider='local'):
    """Create a new user. Returns True if successful, False if username exists."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash, auth_provider, created_at) VALUES (?, ?, ?, ?)',
                  (username, hash_password(password) if password else None, auth_provider, datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    """Verify user credentials. Returns user dict if valid, None otherwise."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, total_stars FROM users WHERE username = ? AND password_hash = ?', 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1], "total_stars": user[2]}
    return None

def update_user_stars(user_id, stars_to_add):
    """Add stars to a user's total."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET total_stars = total_stars + ? WHERE id = ?', (stars_to_add, user_id))
    # Fetch updated stars
    c.execute('SELECT total_stars FROM users WHERE id = ?', (user_id,))
    new_stars = c.fetchone()[0]
    conn.commit()
    conn.close()
    return new_stars

def add_game_score(user_id, game_name, score):
    """Record a play session score."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO game_scores (user_id, game_name, score, played_at) VALUES (?, ?, ?, ?)',
              (user_id, game_name, score, datetime.now()))
    conn.commit()
    conn.close()

def get_global_leaderboard(limit=10):
    """Get the top users by total stars."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT username, total_stars 
        FROM users 
        ORDER BY total_stars DESC 
        LIMIT ?
    ''', (limit,))
    board = c.fetchall()
    conn.close()
    return board

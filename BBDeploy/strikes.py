import sqlite3
import os
from datetime import datetime, timezone

DATA_DIRECTORY = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "data")

os.makedirs(DATA_DIRECTORY, exist_ok=True)

DATABASE = os.path.join(
    DATA_DIRECTORY,
    "strikes.db"
)


def initialize_database():
    """Create the strikes database and table if they don't already exist."""

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strikes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            moderator_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def add_strike(guild_id, user_id, reason, moderator_id):
    """Add a strike to a user."""

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    timestamp = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        INSERT INTO strikes (
            guild_id,
            user_id,
            reason,
            moderator_id,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        guild_id,
        user_id,
        reason,
        moderator_id,
        timestamp
    ))

    connection.commit()
    connection.close()


def get_strikes(guild_id, user_id):
    """Return all strikes belonging to a user on a specific server."""

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, reason, moderator_id, timestamp
        FROM strikes
        WHERE guild_id = ? AND user_id = ?
        ORDER BY id ASC
    """, (
        guild_id,
        user_id
    ))

    strikes = cursor.fetchall()

    connection.close()

    return strikes


def remove_strike(guild_id, user_id):
    """Remove the most recent strike from a user."""

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM strikes
        WHERE id = (
            SELECT id
            FROM strikes
            WHERE guild_id = ? AND user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        )
    """, (
        guild_id,
        user_id
    ))

    connection.commit()

    removed = cursor.rowcount > 0

    connection.close()

    return removed


def clear_strikes(guild_id, user_id):
    """Remove all strikes belonging to a user."""

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM strikes
        WHERE guild_id = ? AND user_id = ?
    """, (
        guild_id,
        user_id
    ))

    connection.commit()

    removed = cursor.rowcount > 0

    connection.close()

    return removed
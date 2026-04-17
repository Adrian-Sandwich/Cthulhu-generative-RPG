#!/usr/bin/env python3
"""
Snapshot Storage - SQLite persistence for snapshots
Stores metadata in DB, images as separate PNG files
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Optional
from .snapshot import Snapshot


class SnapshotStorage:
    """SQLite-based snapshot storage"""

    def __init__(self, db_path: str = "data/snapshots.db", images_dir: str = "data/images"):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database
            images_dir: Directory for PNG image files
        """
        self.db_path = db_path
        self.images_dir = images_dir

        # Create directories if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.images_dir).mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database schema if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_id INTEGER NOT NULL,
                image_path TEXT,
                image_seed INTEGER,
                narrative TEXT,
                decision TEXT,
                state BLOB,
                commands TEXT,
                timestamp REAL,
                tags TEXT,
                UNIQUE(session_id, turn_id)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_turn
            ON snapshots(session_id, turn_id)
        ''')

        conn.commit()
        conn.close()

    def save_snapshot(self, snapshot: Snapshot) -> str:
        """
        Save snapshot to storage.

        Args:
            snapshot: Snapshot to save

        Returns:
            Path to saved snapshot
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Save image if present
        image_path = None
        if snapshot.image:
            image_filename = f"{snapshot.turn_id:04d}.png"
            image_path = os.path.join(self.images_dir, image_filename)
            with open(image_path, 'wb') as f:
                f.write(snapshot.image)

        # Save metadata
        import json
        state_json = snapshot.state.to_dict()
        commands_json = json.dumps(snapshot.commands)
        tags_json = json.dumps(snapshot.tags)

        try:
            cursor.execute('''
                INSERT INTO snapshots
                (session_id, turn_id, image_path, image_seed, narrative, decision,
                 state, commands, timestamp, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot.session_id,
                snapshot.turn_id,
                image_path,
                snapshot.image_seed,
                snapshot.narrative,
                snapshot.decision,
                json.dumps(state_json),
                commands_json,
                snapshot.timestamp,
                tags_json,
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            # Snapshot already exists, update instead
            cursor.execute('''
                UPDATE snapshots
                SET image_path=?, image_seed=?, narrative=?, decision=?,
                    state=?, commands=?, timestamp=?, tags=?
                WHERE session_id=? AND turn_id=?
            ''', (
                image_path,
                snapshot.image_seed,
                snapshot.narrative,
                snapshot.decision,
                json.dumps(state_json),
                commands_json,
                snapshot.timestamp,
                tags_json,
                snapshot.session_id,
                snapshot.turn_id,
            ))
            conn.commit()

        conn.close()
        return image_path or ""

    def get_snapshot(self, session_id: str, turn_id: int) -> Optional[Snapshot]:
        """
        Retrieve snapshot by turn.

        Args:
            session_id: Session identifier
            turn_id: Turn number

        Returns:
            Snapshot or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT session_id, turn_id, image_path, image_seed, narrative, decision,
                   state, commands, timestamp, tags
            FROM snapshots
            WHERE session_id = ? AND turn_id = ?
        ''', (session_id, turn_id))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        import json
        session_id, turn_id, image_path, image_seed, narrative, decision, \
            state_json, commands_json, timestamp, tags_json = row

        # Load image
        image = None
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image = f.read()

        # Load state
        state_dict = json.loads(state_json or '{}')
        from .snapshot import GameStateSnapshot
        state = GameStateSnapshot.from_dict(state_dict)

        # Reconstruct snapshot
        snapshot = Snapshot(
            session_id=session_id,
            turn_id=turn_id,
            image=image,
            image_seed=image_seed,
            narrative=narrative,
            decision=decision,
            state=state,
            commands=json.loads(commands_json or '[]'),
            timestamp=timestamp,
            tags=json.loads(tags_json or '[]'),
        )

        return snapshot

    def list_snapshots(self, session_id: str) -> List[Snapshot]:
        """
        List all snapshots in a session.

        Args:
            session_id: Session identifier

        Returns:
            List of Snapshot objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT session_id, turn_id, image_path, image_seed, narrative, decision,
                   state, commands, timestamp, tags
            FROM snapshots
            WHERE session_id = ?
            ORDER BY turn_id ASC
        ''', (session_id,))

        rows = cursor.fetchall()
        conn.close()

        snapshots = []
        for row in rows:
            import json
            session_id, turn_id, image_path, image_seed, narrative, decision, \
                state_json, commands_json, timestamp, tags_json = row

            # Load image
            image = None
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    image = f.read()

            # Load state
            state_dict = json.loads(state_json or '{}')
            from .snapshot import GameStateSnapshot
            state = GameStateSnapshot.from_dict(state_dict)

            snapshot = Snapshot(
                session_id=session_id,
                turn_id=turn_id,
                image=image,
                image_seed=image_seed,
                narrative=narrative,
                decision=decision,
                state=state,
                commands=json.loads(commands_json or '[]'),
                timestamp=timestamp,
                tags=json.loads(tags_json or '[]'),
            )
            snapshots.append(snapshot)

        return snapshots

    def delete_session(self, session_id: str) -> int:
        """
        Delete all snapshots from a session.

        Args:
            session_id: Session to delete

        Returns:
            Number of deleted snapshots
        """
        # Get image paths to delete
        snapshots = self.list_snapshots(session_id)
        for snapshot in snapshots:
            if snapshot.image and hasattr(snapshot, '_image_path'):
                try:
                    os.remove(snapshot._image_path)
                except:
                    pass

        # Delete from DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM snapshots WHERE session_id = ?', (session_id,))
        count = cursor.rowcount
        conn.commit()
        conn.close()

        return count

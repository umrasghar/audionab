"""Thread-safe SQLite database for conversion history."""

import logging
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class HistoryDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        with self._lock:
            # Enable WAL mode for better concurrent read/write
            self.conn.execute("PRAGMA journal_mode=WAL")

            # Schema versioning
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)
            row = self.conn.execute(
                "SELECT MAX(version) as v FROM schema_version"
            ).fetchone()
            current_version = row["v"] if row["v"] is not None else 0

            if current_version < 1:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_path TEXT NOT NULL,
                        source_name TEXT NOT NULL,
                        source_format TEXT NOT NULL,
                        source_size INTEGER DEFAULT 0,
                        output_path TEXT NOT NULL,
                        output_name TEXT NOT NULL,
                        output_size INTEGER DEFAULT 0,
                        bitrate TEXT DEFAULT '192k',
                        duration_secs REAL DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        error_msg TEXT DEFAULT '',
                        pass_used INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT (datetime('now', 'localtime')),
                        completed_at TEXT DEFAULT ''
                    )
                """)
                self.conn.execute(
                    "INSERT OR IGNORE INTO schema_version (version) VALUES (1)"
                )

            # Migration v2: add output_format and transcript_path columns
            if current_version < 2:
                try:
                    self.conn.execute(
                        "ALTER TABLE conversions ADD COLUMN output_format TEXT DEFAULT 'MP3'"
                    )
                except Exception:
                    pass  # Column may already exist
                try:
                    self.conn.execute(
                        "ALTER TABLE conversions ADD COLUMN transcript_path TEXT DEFAULT ''"
                    )
                except Exception:
                    pass
                self.conn.execute(
                    "INSERT OR IGNORE INTO schema_version (version) VALUES (2)"
                )

            self.conn.commit()
            logger.debug("Database initialized (version %d)", max(current_version, 1))

    def add_conversion(self, source_path, output_path, bitrate="192k"):
        with self._lock:
            src = Path(source_path)
            cur = self.conn.execute("""
                INSERT INTO conversions
                (source_path, source_name, source_format, source_size,
                 output_path, output_name, bitrate, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'converting')
            """, (
                str(src), src.name, src.suffix.lower(),
                src.stat().st_size if src.exists() else 0,
                str(output_path), Path(output_path).name, bitrate
            ))
            self.conn.commit()
            return cur.lastrowid

    def update_conversion(self, row_id, **kwargs):
        with self._lock:
            sets = ", ".join(f"{k} = ?" for k in kwargs)
            vals = list(kwargs.values()) + [row_id]
            self.conn.execute(f"UPDATE conversions SET {sets} WHERE id = ?", vals)
            self.conn.commit()

    def get_history(self, limit=100):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM conversions ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    def get_stats(self):
        with self._lock:
            row = self.conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COALESCE(SUM(CASE WHEN status='success' THEN 1 ELSE 0 END), 0) as success,
                    COALESCE(SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END), 0) as failed,
                    COALESCE(SUM(CASE WHEN status='success' THEN source_size ELSE 0 END), 0) as total_input,
                    COALESCE(SUM(CASE WHEN status='success' THEN output_size ELSE 0 END), 0) as total_output
                FROM conversions
            """).fetchone()
            return dict(row)

    def clear_history(self):
        with self._lock:
            self.conn.execute("DELETE FROM conversions")
            self.conn.commit()

    def delete_entry(self, row_id):
        with self._lock:
            self.conn.execute("DELETE FROM conversions WHERE id = ?", (row_id,))
            self.conn.commit()

from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import contextmanager


SCHEMA_VERSION = 1


class Database:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_initialized()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(str(self.path))
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _ensure_initialized(self) -> None:
        with self.connect() as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            current = self._get_schema_version(conn)
            if current < 1:
                self._migrate_to_v1(conn)
                self._set_schema_version(conn, 1)

    @staticmethod
    def _get_schema_version(conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        return int(row[0]) if row else 0

    @staticmethod
    def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
            (str(version),),
        )

    @staticmethod
    def _migrate_to_v1(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_at TEXT,
                completed_at TEXT,
                created_at TEXT NOT NULL
            );
            """
        )


def default_db_path() -> Path:
    home = Path.home()
    return home / ".quickcapture" / "quickcapture.db"

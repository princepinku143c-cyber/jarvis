from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MemoryItem:
    id: int
    key: str
    value: str
    importance: int
    created_at: str
    updated_at: str


class MemoryStore:
    """Small durable memory layer with deterministic pruning.

    Memory is deliberately explicit: key/value facts are stored in SQLite and
    pruned by importance/recency rather than pretending to provide unlimited
    recall. A larger semantic/vector layer can be added later without changing
    the agent interface.
    """

    def __init__(self, database_path: str = "storage/jarvis.db", max_chars: int = 2200):
        self.database_path = database_path
        self.max_chars = max_chars
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    importance INTEGER NOT NULL DEFAULT 5,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()

    def upsert(self, key: str, value: str, importance: int = 5) -> MemoryItem:
        importance = max(1, min(10, int(importance)))
        with self._connect() as db:
            db.execute("""
                INSERT INTO memories(key, value, importance)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    importance=excluded.importance,
                    updated_at=CURRENT_TIMESTAMP
            """, (key, value, importance))
            db.commit()
            row = db.execute("SELECT * FROM memories WHERE key=?", (key,)).fetchone()
        self.prune()
        return MemoryItem(**dict(row))

    def get(self, key: str) -> MemoryItem | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM memories WHERE key=?", (key,)).fetchone()
        return MemoryItem(**dict(row)) if row else None

    def recent(self, limit: int = 50) -> list[MemoryItem]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM memories ORDER BY importance DESC, updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [MemoryItem(**dict(row)) for row in rows]

    def render_context(self) -> str:
        rows = self.recent(100)
        lines: list[str] = []
        total = 0
        for item in rows:
            line = f"{item.key}: {item.value}"
            if total + len(line) + 1 > self.max_chars:
                continue
            lines.append(line)
            total += len(line) + 1
        return "\n".join(lines)

    def prune(self) -> None:
        """Keep the rendered memory context within the configured budget."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT id, key, value FROM memories ORDER BY importance ASC, updated_at ASC"
            ).fetchall()
            while rows:
                total = sum(len(f"{r['key']}: {r['value']}") + 1 for r in rows)
                if total <= self.max_chars:
                    break
                victim = rows.pop(0)
                db.execute("DELETE FROM memories WHERE id=?", (victim["id"],))
            db.commit()

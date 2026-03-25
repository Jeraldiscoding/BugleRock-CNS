"""Phase 4: Event Publishing to the Universal Router (SQLite-backed event bus).

- Connects to a shared SQLite DB (e.g., universal_router.db)
- Ensures `events` table exists with schema: id, timestamp, event_type, payload (JSON text), status (default 'unread')
- Publishes events with SGT (UTC+8) timestamps only
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")


@dataclass
class EventRecord:
    id: int
    timestamp: str
    event_type: str
    payload: Dict[str, Any]
    status: str


class EventPublisher:
    def __init__(self, db_path: str = "universal_router.db") -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'unread'
                );
                """
            )
            conn.commit()

    def publish_new_signal_classified(self, payload: Dict[str, Any]) -> EventRecord:
        """Insert a new event row with event_type='new_signal_classified'."""

        ts = datetime.now(SGT).isoformat()
        event_type = "new_signal_classified"

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO events (timestamp, event_type, payload, status) VALUES (?, ?, ?, 'unread')",
                (ts, event_type, json.dumps(payload)),
            )
            conn.commit()
            event_id = cur.lastrowid

        return EventRecord(
            id=event_id,
            timestamp=ts,
            event_type=event_type,
            payload=payload,
            status="unread",
        )


__all__ = ["EventPublisher", "EventRecord"]

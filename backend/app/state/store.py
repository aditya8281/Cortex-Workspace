import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from .models import SystemState, SystemEvent


class StateStore:
    def __init__(self, db_path: Optional[str] = None):
        self._conn = None
        self._custom_path = db_path
        self._current_db_path = None
        # Trigger initialization of the connection and tables
        _ = self.conn

    @property
    def conn(self):
        from backend.app.services.memory_manager import memory_manager
        if self._custom_path:
            expected_path = self._custom_path
        else:
            expected_path = str(memory_manager.get_path("sync_state", "state.db"))
            
        if self._conn is None or self._current_db_path != expected_path:
            self.reconnect(expected_path)
        return self._conn

    @conn.setter
    def conn(self, value):
        self._conn = value

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def reconnect(self, db_path: Optional[str] = None):
        self.close()
        if db_path is None:
            from backend.app.services.memory_manager import memory_manager
            db_path = str(memory_manager.get_path("sync_state", "state.db"))
        
        self._current_db_path = db_path
        # Ensure parent folder exists using safe abstraction
        from backend.app.core.runtime import get_runtime
        runtime = get_runtime()
        db_dir = db_path.rsplit('/', 1)[0] if '/' in db_path else '.'
        runtime.create_dir(db_dir)
        
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS state_snapshot (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                state_json TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS state_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT,
                type TEXT,
                timestamp TEXT,
                payload TEXT,
                source TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_state_events_execution_id
            ON state_events (execution_id, id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_state_events_timestamp
            ON state_events (timestamp)
            """
        )

        self.conn.commit()

    def save_snapshot(self, state: SystemState) -> None:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO state_snapshot (timestamp, state_json)
            VALUES (?, ?)
            """,
            (datetime.now(timezone.utc).isoformat(), state.model_dump_json()),
        )

        self.conn.commit()

    def save_event(
        self,
        event: SystemEvent,
        execution_id: Optional[str] = None
    ) -> None:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO state_events (
                execution_id,
                type,
                timestamp,
                payload,
                source
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                event.type.value,
                event.timestamp.isoformat(),
                json.dumps(event.payload),
                event.source,
            ),
        )

        self.conn.commit()

    def get_events_by_execution(self, execution_id: str) -> list[dict[str, Any]]:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT type, timestamp, payload, source
            FROM state_events
            WHERE execution_id = ?
            ORDER BY id ASC
            """,
            (execution_id,),
        )

        rows = cursor.fetchall()

        return [
            {
                "type": r["type"],
                "timestamp": r["timestamp"],
                "payload": json.loads(r["payload"]),
                "source": r["source"],
            }
            for r in rows
        ]

    def list_executions(self, limit: int = 50) -> list[dict[str, Any]]:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT execution_id, COUNT(*) AS event_count, MAX(timestamp) AS last_timestamp
            FROM state_events
            WHERE execution_id IS NOT NULL
            GROUP BY execution_id
            ORDER BY last_timestamp DESC, execution_id DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

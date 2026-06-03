import sqlite3
import json
from datetime import datetime
from typing import Optional

from .models import SystemState, SystemEvent


class StateStore:
    """
    Persistence layer for snapshots + execution-scoped event logs
    """

    def __init__(self, db_path: str = "state.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()

    # -------------------------------------------------
    # TABLE INIT
    # -------------------------------------------------
    def _init_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS state_snapshot (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            state_json TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS state_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT,            -- 🔥 CRITICAL ADDITION
            type TEXT,
            timestamp TEXT,
            payload TEXT,
            source TEXT
        )
        """)

        self.conn.commit()

    # -------------------------------------------------
    # SAVE SNAPSHOT
    # -------------------------------------------------
    def save_snapshot(self, state: SystemState):
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO state_snapshot (timestamp, state_json)
        VALUES (?, ?)
        """, (
            datetime.utcnow().isoformat(),
            state.model_dump_json()
        ))

        self.conn.commit()

    # -------------------------------------------------
    # SAVE EVENT (NOW EXECUTION-AWARE)
    # -------------------------------------------------
    def save_event(
        self,
        event: SystemEvent,
        execution_id: Optional[str] = None
    ):
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO state_events (
            execution_id,
            type,
            timestamp,
            payload,
            source
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            execution_id,
            event.type.value,
            event.timestamp.isoformat(),
            json.dumps(event.payload),
            event.source
        ))

        self.conn.commit()

    # -------------------------------------------------
    # REPLAY SUPPORT (CORE FOR NEXT PHASE)
    # -------------------------------------------------
    def get_events_by_execution(self, execution_id: str):
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT type, timestamp, payload, source
        FROM state_events
        WHERE execution_id = ?
        ORDER BY id ASC
        """, (execution_id,))

        rows = cursor.fetchall()

        return [
            {
                "type": r[0],
                "timestamp": r[1],
                "payload": json.loads(r[2]),
                "source": r[3]
            }
            for r in rows
        ]
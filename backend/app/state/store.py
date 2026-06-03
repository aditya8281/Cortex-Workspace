# backend/app/state/store.py

import sqlite3
import json
from typing import Optional
from datetime import datetime
from .models import SystemState, SystemEvent


class StateStore:
    """
    Persistence layer for snapshots + selective event logs
    """

    def __init__(self, db_path: str = "state.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()

    # -----------------------------
    # TABLE INIT
    # -----------------------------
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
            type TEXT,
            timestamp TEXT,
            payload TEXT,
            source TEXT
        )
        """)

        self.conn.commit()

    # -----------------------------
    # SAVE SNAPSHOT
    # -----------------------------
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

    # -----------------------------
    # SAVE EVENT
    # -----------------------------
    def save_event(self, event: SystemEvent):
        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO state_events (type, timestamp, payload, source)
        VALUES (?, ?, ?, ?)
        """, (
            event.type.value,
            event.timestamp.isoformat(),
            json.dumps(event.payload),
            event.source
        ))

        self.conn.commit()
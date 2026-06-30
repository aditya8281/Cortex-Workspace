"""System monitor — captures system metrics snapshots and detects anomalies."""

from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session

from backend.app.models.awareness.system_snapshot import SystemSnapshot

logger = logging.getLogger(__name__)


class SystemMonitorService:
    """Captures system metrics snapshots and detects resource anomalies."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def take_snapshot(self, user_id: int | None = None) -> SystemSnapshot:
        """Capture current system metrics and store."""
        import psutil

        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        load = os.getloadavg()

        snap = SystemSnapshot(
            user_id=user_id,
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=mem.percent,
            memory_used_gb=round(mem.used / (1024**3), 2),
            memory_total_gb=round(mem.total / (1024**3), 2),
            disk_percent=disk.percent,
            disk_used_gb=round(disk.used / (1024**3), 2),
            disk_total_gb=round(disk.total / (1024**3), 2),
            network_sent_bytes=net.bytes_sent,
            network_recv_bytes=net.bytes_recv,
            load_average_1m=load[0],
            load_average_5m=load[1],
            load_average_15m=load[2],
            process_count=len(psutil.pids()),
            uptime_seconds=psutil.boot_time(),
            meta={},
        )
        self.db.add(snap)
        self.db.commit()
        self.db.refresh(snap)
        logger.info("System snapshot taken (cpu=%.1f%%, mem=%.1f%%)", snap.cpu_percent, snap.memory_percent)
        return snap

    def get_recent_snapshots(
        self, user_id: int | None = None, limit: int = 20
    ) -> list[SystemSnapshot]:
        """Get recent snapshots, optionally filtered by user."""
        q = self.db.query(SystemSnapshot)
        if user_id:
            q = q.filter(SystemSnapshot.user_id == user_id)
        return q.order_by(SystemSnapshot.created_at.desc()).limit(limit).all()

    def detect_anomalies(
        self,
        threshold_cpu: float = 90.0,
        threshold_memory: float = 90.0,
        threshold_disk: float = 95.0,
    ) -> list[dict]:
        """Check latest snapshot for anomalies."""
        latest = self.db.query(SystemSnapshot).order_by(SystemSnapshot.created_at.desc()).first()
        if not latest:
            return []

        anomalies: list[dict] = []
        if latest.cpu_percent > threshold_cpu:
            anomalies.append({"type": "high_cpu", "value": latest.cpu_percent, "threshold": threshold_cpu})
        if latest.memory_percent > threshold_memory:
            anomalies.append({"type": "high_memory", "value": latest.memory_percent, "threshold": threshold_memory})
        if latest.disk_percent > threshold_disk:
            anomalies.append({"type": "high_disk", "value": latest.disk_percent, "threshold": threshold_disk})

        if anomalies:
            logger.warning("Detected %d anomalies: %s", len(anomalies), [a["type"] for a in anomalies])
        return anomalies

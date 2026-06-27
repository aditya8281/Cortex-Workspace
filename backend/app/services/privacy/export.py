"""Data export service — GDPR Article 20 data portability."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.privacy.data_export import DataExport


class DataExportService:
    """Complete data export for data portability.

    Supports full/partial exports, JSON/CSV formats, SHA-256 integrity
    verification, and automatic file expiry.
    """

    EXPORT_DIR = "/tmp/cortex_exports"
    EXPIRY_DAYS = 7
    MAX_EXPORT_SIZE_MB = 100

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_export(
        self,
        user_id: int,
        export_type: str = "full",
        data_types: list[str] | None = None,
        format: str = "json",
    ) -> DataExport:
        """Create a data export request."""
        os.makedirs(self.EXPORT_DIR, exist_ok=True)
        export = DataExport(
            user_id=user_id,
            export_type=export_type,
            data_types=data_types,
            format=format,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(days=self.EXPIRY_DAYS),
        )
        self.db.add(export)
        self.db.commit()
        return export

    def process_export(self, export_id: int) -> DataExport:
        """Process a data export: gather, serialize, verify, store."""
        export = self.db.execute(select(DataExport).where(DataExport.id == export_id)).scalar_one_or_none()
        if not export:
            raise ValueError(f"Export {export_id} not found")

        export.status = "processing"
        export.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            user_data = self._gather_user_data(export.user_id, export.data_types)

            if export.format == "json":
                content = json.dumps(user_data, indent=2, default=str, ensure_ascii=False)
                file_ext = "json"
            elif export.format == "csv":
                content = self._to_csv(user_data)
                file_ext = "csv"
            else:
                raise ValueError(f"Unsupported format: {export.format}")

            content_bytes = content.encode("utf-8")
            size_mb = len(content_bytes) / (1024 * 1024)
            if size_mb > self.MAX_EXPORT_SIZE_MB:
                raise ValueError(f"Export exceeds {self.MAX_EXPORT_SIZE_MB}MB limit")

            checksum = hashlib.sha256(content_bytes).hexdigest()
            file_path = os.path.join(
                self.EXPORT_DIR,
                f"cortex_export_{export.user_id}_{export.id}.{file_ext}",
            )
            with open(file_path, "wb") as f:
                f.write(content_bytes)

            export.file_path = file_path
            export.file_size_bytes = len(content_bytes)
            export.checksum_sha256 = checksum
            export.status = "complete"
            export.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return export

        except Exception as e:
            export.status = "failed"
            export.error_message = str(e)
            self.db.commit()
            return export

    def _gather_user_data(self, user_id: int, data_types: list[str] | None = None) -> dict[str, Any]:
        """Gather all user data from domain services."""
        all_types = [
            "memories",
            "files",
            "settings",
            "agents",
            "workflows",
            "consents",
            "audit_summary",
        ]
        types_to_gather = data_types or all_types
        data: dict[str, Any] = {
            "export_metadata": {
                "user_id": user_id,
                "export_date": datetime.now(timezone.utc).isoformat(),
                "format_version": "1.0",
                "data_types_included": types_to_gather,
            },
        }
        for dtype in types_to_gather:
            data[dtype] = self._gather_domain_data(user_id, dtype)
        return data

    def _gather_domain_data(self, user_id: int, domain: str) -> Any:  # noqa: ARG002
        """Gather data from a specific domain (stub)."""
        stubs: dict[str, Any] = {
            "memories": {"count": 0, "items": []},
            "files": {"count": 0, "items": []},
            "settings": {},
            "agents": {"count": 0, "items": []},
            "workflows": {"count": 0, "items": []},
            "consents": {"count": 0, "items": []},
            "audit_summary": {"total_actions": 0},
        }
        return stubs.get(domain, {})

    def _to_csv(self, data: dict[str, Any]) -> str:
        """Convert nested data to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["=== Cortex Data Export ==="])
        writer.writerow([])
        for section, content in data.items():
            writer.writerow([f"--- {section} ---"])
            if isinstance(content, dict):
                for key, value in content.items():
                    if isinstance(value, (list, dict)):
                        writer.writerow([key, json.dumps(value, default=str)])
                    else:
                        writer.writerow([key, value])
            else:
                writer.writerow([content])
            writer.writerow([])
        return output.getvalue()

    def verify_export(self, export_id: int) -> dict[str, Any]:
        """Verify export integrity by recomputing checksum."""
        export = self.db.execute(select(DataExport).where(DataExport.id == export_id)).scalar_one_or_none()
        if not export:
            raise ValueError(f"Export {export_id} not found")
        if not export.file_path or not os.path.exists(export.file_path):
            return {"valid": False, "reason": "Export file not found"}
        with open(export.file_path, "rb") as f:
            computed = hashlib.sha256(f.read()).hexdigest()
        return {
            "valid": computed == export.checksum_sha256,
            "stored_checksum": export.checksum_sha256,
            "computed_checksum": computed,
            "file_size_bytes": export.file_size_bytes,
        }

    def cleanup_expired_exports(self) -> int:
        """Delete expired export files and their DB rows."""
        cutoff = datetime.now(timezone.utc)
        # Find expired exports — iterate to avoid timezone comparison in bulk delete
        all_exports = list(self.db.execute(select(DataExport)).scalars().all())
        deleted_count = 0
        for export in all_exports:
            if export.expires_at is None:
                continue
            # Handle both naive and aware datetimes
            exp = export.expires_at
            if exp.tzinfo is None:
                cutoff_naive = cutoff.replace(tzinfo=None)
                if exp >= cutoff_naive:
                    continue
            else:
                if exp >= cutoff:
                    continue
            if export.file_path and os.path.exists(export.file_path):
                os.remove(export.file_path)
            self.db.delete(export)
            deleted_count += 1
        self.db.commit()
        return deleted_count

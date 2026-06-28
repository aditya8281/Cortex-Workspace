"""Tests for v1.05 P03 data export service."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from backend.app.services.privacy.export import DataExportService


class TestDataExportService:
    def test_create_export(self, db_session: Session, tmp_path: Path) -> None:
        service = DataExportService(db_session)
        service.EXPORT_DIR = str(tmp_path)
        export = service.create_export(user_id=1, export_type="full", format="json")
        assert export.status == "pending"
        assert export.user_id == 1
        assert export.format == "json"

    def test_process_export_json(self, db_session: Session, tmp_path: Path) -> None:
        service = DataExportService(db_session)
        service.EXPORT_DIR = str(tmp_path)
        export = service.create_export(user_id=1)
        result = service.process_export(export.id)
        assert result.status == "complete"
        assert result.file_path is not None
        assert result.checksum_sha256 is not None
        assert result.file_size_bytes is not None
        assert os.path.exists(result.file_path)

    def test_process_export_csv(self, db_session: Session, tmp_path: Path) -> None:
        service = DataExportService(db_session)
        service.EXPORT_DIR = str(tmp_path)
        export = service.create_export(user_id=1, format="csv")
        result = service.process_export(export.id)
        assert result.status == "complete"
        assert result.file_path is not None
        assert result.file_path.endswith(".csv")

    def test_verify_export(self, db_session: Session, tmp_path: Path) -> None:
        service = DataExportService(db_session)
        service.EXPORT_DIR = str(tmp_path)
        export = service.create_export(user_id=1)
        service.process_export(export.id)
        verification = service.verify_export(export.id)
        assert verification["valid"] is True

    def test_cleanup_expired(self, db_session: Session, tmp_path: Path) -> None:
        service = DataExportService(db_session)
        service.EXPORT_DIR = str(tmp_path)
        export = service.create_export(user_id=1)
        service.process_export(export.id)
        export.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.commit()
        deleted = service.cleanup_expired_exports()
        assert deleted == 1

    def test_export_not_found_raises(self, db_session: Session, tmp_path: Path) -> None:
        service = DataExportService(db_session)
        service.EXPORT_DIR = str(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            service.process_export(999)

    def test_partial_export(self, db_session: Session, tmp_path: Path) -> None:
        service = DataExportService(db_session)
        service.EXPORT_DIR = str(tmp_path)
        export = service.create_export(user_id=1, export_type="partial", data_types=["memories", "files"])
        assert export.export_type == "partial"
        result = service.process_export(export.id)
        assert result.status == "complete"

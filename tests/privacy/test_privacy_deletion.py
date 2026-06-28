"""Tests for v1.05 P03 data deletion service."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.services.privacy.deletion import DataDeletionService


class TestDataDeletionService:
    def test_create_deletion_request(self, db_session: Session) -> None:
        service = DataDeletionService(db_session)
        req = service.create_deletion_request(user_id=1, deletion_type="full")
        assert req.id is not None
        assert req.status == "pending"
        assert req.user_id == 1

    def test_create_partial_deletion(self, db_session: Session) -> None:
        service = DataDeletionService(db_session)
        req = service.create_deletion_request(
            user_id=1,
            deletion_type="specific",
            data_types=["memories", "files"],
        )
        assert req.data_types == ["memories", "files"]

    def test_process_deletion(self, db_session: Session) -> None:
        service = DataDeletionService(db_session)
        req = service.create_deletion_request(user_id=1, deletion_type="full")
        result = service.process_deletion(req.id)
        assert result.status == "complete"
        assert result.deletion_proof_hash is not None
        assert len(result.deletion_proof_hash) == 64  # SHA-256 hex
        assert result.completed_at is not None

    def test_verify_deletion(self, db_session: Session) -> None:
        service = DataDeletionService(db_session)
        req = service.create_deletion_request(user_id=1, deletion_type="full")
        service.process_deletion(req.id)
        verification = service.verify_deletion(req.id)
        assert verification["status"] == "complete"
        assert verification["deletion_proof_hash"] is not None

    def test_deletion_not_found_raises(self, db_session: Session) -> None:
        service = DataDeletionService(db_session)
        with pytest.raises(ValueError, match="not found"):
            service.process_deletion(999)

    def test_verify_not_found_raises(self, db_session: Session) -> None:
        service = DataDeletionService(db_session)
        with pytest.raises(ValueError, match="not found"):
            service.verify_deletion(999)

    def test_user_isolation(self, db_session: Session) -> None:
        service = DataDeletionService(db_session)
        r1 = service.create_deletion_request(user_id=1, deletion_type="full")
        r2 = service.create_deletion_request(user_id=2, deletion_type="full")
        v1 = service.verify_deletion(r1.id)
        v2 = service.verify_deletion(r2.id)
        assert v1["request_id"] == r1.id
        assert v2["request_id"] == r2.id

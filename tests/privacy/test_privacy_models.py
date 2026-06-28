"""Tests for v1.05 P01 privacy foundation models."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.models.privacy.access_policy import AccessPolicy
from backend.app.models.privacy.audit_log import AuditLog
from backend.app.models.privacy.consent import ConsentRecord
from backend.app.models.privacy.data_deletion import DataDeletionRequest
from backend.app.models.privacy.role import Permission, Role


class TestAuditLogModel:
    def test_create_audit_log(self, db_session: Session) -> None:
        log = AuditLog(
            user_id=1,
            action="create",
            resource_type="memory",
            resource_id=42,
            details={"key": "value"},
            ip_address="127.0.0.1",
            success=1,
        )
        db_session.add(log)
        db_session.commit()
        assert log.id is not None
        assert log.timestamp is not None

    def test_audit_log_user_id_indexed(self, db_session: Session) -> None:
        """Verify audit log entries can be queried by user_id."""
        for _ in range(5):
            log = AuditLog(user_id=1, action="read", resource_type="file")
            db_session.add(log)
        db_session.commit()
        logs = db_session.query(AuditLog).filter(AuditLog.user_id == 1).all()
        assert len(logs) == 5

    def test_audit_log_defaults(self, db_session: Session) -> None:
        log = AuditLog(user_id=1, action="login", resource_type="auth")
        db_session.add(log)
        db_session.commit()
        assert log.success == 1
        assert log.resource_id is None
        assert log.error_message is None
        assert log.timestamp is not None


class TestConsentModel:
    def test_create_consent(self, db_session: Session) -> None:
        consent = ConsentRecord(
            user_id=1,
            consent_type="memory_read",
            granted=1,
            scope="all",
        )
        db_session.add(consent)
        db_session.commit()
        assert consent.id is not None
        assert consent.version == 1

    def test_consent_expiry_query(self, db_session: Session) -> None:
        """Expired consent should not appear in active query."""
        consent = ConsentRecord(
            user_id=1,
            consent_type="analytics",
            granted=1,
            expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.add(consent)
        db_session.commit()
        active = (
            db_session.query(ConsentRecord)
            .filter(
                ConsentRecord.user_id == 1,
                ConsentRecord.granted == 1,
                (ConsentRecord.expires_at.is_(None)) | (ConsentRecord.expires_at > datetime.now()),
            )
            .all()
        )
        assert len(active) == 0

    def test_consent_user_isolation(self, db_session: Session) -> None:
        c1 = ConsentRecord(user_id=1, consent_type="file_write", granted=1)
        c2 = ConsentRecord(user_id=2, consent_type="file_write", granted=1)
        db_session.add_all([c1, c2])
        db_session.commit()
        user1 = db_session.query(ConsentRecord).filter(ConsentRecord.user_id == 1).count()
        user2 = db_session.query(ConsentRecord).filter(ConsentRecord.user_id == 2).count()
        assert user1 == 1
        assert user2 == 1


class TestAccessPolicyModel:
    def test_create_policy(self, db_session: Session) -> None:
        policy = AccessPolicy(
            name="user_own_data",
            description="Users can read their own data",
            resource_type="memory",
            action="read",
            effect="allow",
            conditions={"owner": True},
            priority=10,
        )
        db_session.add(policy)
        db_session.commit()
        assert policy.id is not None
        assert policy.enabled == 1

    def test_policy_disabled(self, db_session: Session) -> None:
        policy = AccessPolicy(
            name="disabled_policy",
            resource_type="file",
            action="delete",
            effect="deny",
            enabled=0,
        )
        db_session.add(policy)
        db_session.commit()
        assert policy.enabled == 0


class TestRoleModel:
    def test_create_role_with_permissions(self, db_session: Session) -> None:
        role = Role(name="user", description="Standard user")
        perm = Permission(resource_type="memory", action="read")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()
        assert role.id is not None
        assert len(role.permissions) == 1

    def test_default_roles_exist(self, db_session: Session) -> None:
        for name, desc in [("admin", "Full access"), ("user", "Standard access"), ("viewer", "Read-only")]:
            role = Role(name=name, description=desc)
            db_session.add(role)
        db_session.commit()
        roles = db_session.query(Role).all()
        assert len(roles) == 3


class TestDataDeletionModel:
    def test_create_deletion_request(self, db_session: Session) -> None:
        req = DataDeletionRequest(
            user_id=1,
            deletion_type="specific",
            data_types=["memory", "files"],
        )
        db_session.add(req)
        db_session.commit()
        assert req.id is not None
        assert req.status == "pending"
        assert req.items_deleted_count == 0

    def test_deletion_user_isolation(self, db_session: Session) -> None:
        r1 = DataDeletionRequest(user_id=1, deletion_type="full")
        r2 = DataDeletionRequest(user_id=2, deletion_type="full")
        db_session.add_all([r1, r2])
        db_session.commit()
        user1 = db_session.query(DataDeletionRequest).filter(DataDeletionRequest.user_id == 1).count()
        user2 = db_session.query(DataDeletionRequest).filter(DataDeletionRequest.user_id == 2).count()
        assert user1 == 1
        assert user2 == 1

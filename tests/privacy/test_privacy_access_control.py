"""Tests for v1.05 P02 access control service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from backend.app.models.privacy.access_policy import AccessPolicy
from backend.app.models.privacy.role import Permission, Role
from backend.app.services.privacy.access_control import AccessControlService


class TestRBACPermissionCheck:
    def test_check_permission_with_role(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        role = Role(name="test_user")
        perm = Permission(resource_type="memory", action="read")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()
        service.assign_role(1, "test_user")
        assert service.check_permission(1, "memory", "read") is True
        assert service.check_permission(1, "memory", "write") is False

    def test_wildcard_permission(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        role = Role(name="admin")
        perm = Permission(resource_type="*", action="*")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()
        service.assign_role(1, "admin")
        assert service.check_permission(1, "anything", "any_action") is True

    def test_no_roles_returns_false(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        assert service.check_permission(999, "memory", "read") is False

    def test_wildcard_resource_does_not_grant_all_actions(self, db_session: Session) -> None:
        """Bug fix: resource_type=* should only match the requested action, not all."""
        service = AccessControlService(db_session)
        role = Role(name="reader")
        perm = Permission(resource_type="*", action="read")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()
        service.assign_role(1, "reader")
        assert service.check_permission(1, "memory", "read") is True
        assert service.check_permission(1, "memory", "write") is False

    def test_wildcard_action_does_not_grant_all_resources(self, db_session: Session) -> None:
        """Bug fix: action=* should only match the requested resource, not all."""
        service = AccessControlService(db_session)
        role = Role(name="file_admin")
        perm = Permission(resource_type="file", action="*")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()
        service.assign_role(1, "file_admin")
        assert service.check_permission(1, "file", "read") is True
        assert service.check_permission(1, "file", "write") is True
        assert service.check_permission(1, "memory", "read") is False


class TestABACPolicyEngine:
    def test_deny_wins_over_allow(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        role = Role(name="user")
        perm = Permission(resource_type="memory", action="read")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()
        service.assign_role(1, "user")
        policy = AccessPolicy(
            name="deny_memory_read",
            resource_type="memory",
            action="read",
            effect="deny",
            conditions={},
            priority=100,
        )
        db_session.add(policy)
        db_session.commit()
        assert service.check_access(1, "memory", "read") is False

    def test_abac_allow_with_conditions(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        policy = AccessPolicy(
            name="owner_allow",
            resource_type="memory",
            action="read",
            effect="allow",
            conditions={"is_owner": True},
            priority=10,
        )
        db_session.add(policy)
        db_session.commit()
        assert service.check_access(1, "memory", "read", resource_owner_id=1) is True
        assert service.check_access(1, "memory", "read", resource_owner_id=2) is False

    def test_no_policies_falls_through(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        assert service.check_access(1, "memory", "read") is False

    def test_priority_order(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        db_session.add(
            AccessPolicy(
                name="low_allow",
                resource_type="*",
                action="*",
                effect="allow",
                conditions={},
                priority=1,
            )
        )
        db_session.add(
            AccessPolicy(
                name="high_deny",
                resource_type="*",
                action="*",
                effect="deny",
                conditions={},
                priority=100,
            )
        )
        db_session.commit()
        assert service.check_access(1, "anything", "do") is False


class TestConsentIntegration:
    def test_grant_and_check_consent(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        consent = service.grant_consent(1, "memory_read", scope="all")
        assert consent.granted == 1
        assert consent.version == 1
        assert service.check_consent(1, "memory_read") is True

    def test_revoke_consent(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        service.grant_consent(1, "file_write")
        assert service.revoke_consent(1, "file_write") is True
        assert service.check_consent(1, "file_write") is False

    def test_revoke_nonexistent_returns_false(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        assert service.revoke_consent(1, "nope") is False

    def test_consent_expiry(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        service.grant_consent(
            1,
            "analytics",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert service.check_consent(1, "analytics") is False

    def test_consent_grant_replaces_previous(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        c1 = service.grant_consent(1, "file_write", scope="read_only")
        assert c1.version == 1
        c2 = service.grant_consent(1, "file_write", scope="full")
        # In-place update: same object, version bumped
        assert c2 is c1
        assert c2.version == 2
        assert c2.scope == "full"
        assert c2.revoked_at is None
        assert len(service.get_active_consents(1)) == 1


class TestRoleManagement:
    def test_assign_and_get_roles(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        db_session.add(Role(name="editor", description="Can edit"))
        db_session.commit()
        service.assign_role(1, "editor")
        roles = service.get_user_roles(1)
        assert len(roles) == 1
        assert roles[0].name == "editor"

    def test_remove_role(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        db_session.add(Role(name="temp_role"))
        db_session.commit()
        service.assign_role(1, "temp_role")
        service.remove_role(1, "temp_role")
        assert service.get_user_roles(1) == []

    def test_assign_nonexistent_role_raises(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        with pytest.raises(ValueError, match="not found"):
            service.assign_role(1, "nope")

    def test_get_user_permissions(self, db_session: Session) -> None:
        service = AccessControlService(db_session)
        role = Role(name="reader")
        perm = Permission(resource_type="file", action="read")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()
        service.assign_role(1, "reader")
        perms = service.get_user_permissions(1)
        assert len(perms) == 1
        assert perms[0].resource_type == "file"

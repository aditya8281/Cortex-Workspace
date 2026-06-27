"""RBAC + ABAC access control service with consent integration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.models.privacy.access_policy import AccessPolicy
from backend.app.models.privacy.consent import ConsentRecord
from backend.app.models.privacy.role import Permission, Role, role_permissions, user_roles


class AccessControlService:
    """RBAC + ABAC access control.

    Evaluation flow:
    1. RBAC deny → 2. ABAC deny → 3. RBAC allow → 4. ABAC allow.
    Explicit deny wins on conflict.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── RBAC ─────────────────────────────────────────────

    def check_permission(self, user_id: int, resource_type: str, action: str) -> bool:
        """Fast RBAC check: does user have a matching permission via any role?"""
        stmt = (
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(user_roles, user_roles.c.role_id == role_permissions.c.role_id)
            .where(user_roles.c.user_id == user_id)
        )
        for perm in self.db.execute(stmt).scalars().all():
            rt_match = perm.resource_type == "*" or perm.resource_type == resource_type
            act_match = perm.action == "*" or perm.action == action
            if rt_match and act_match:
                return True
        return False

    def check_access(
        self,
        user_id: int,
        resource_type: str,
        action: str,
        resource_owner_id: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Full access check combining RBAC + ABAC. Deny wins on conflict."""
        ctx: dict[str, Any] = dict(context) if context else {}
        if resource_owner_id is not None:
            ctx["owner_id"] = resource_owner_id
            ctx["is_owner"] = user_id == resource_owner_id

        rbac_allowed = self.check_permission(user_id, resource_type, action)
        abac_result = self._evaluate_policies(user_id, resource_type, action, ctx)

        if abac_result == "deny":
            return False
        if abac_result == "allow":
            return True
        return rbac_allowed

    def _evaluate_policies(
        self,
        user_id: int,  # noqa: ARG002
        resource_type: str,
        action: str,
        context: dict[str, Any],
    ) -> str | None:
        """Evaluate ABAC policies. Returns 'allow', 'deny', or None."""
        stmt = (
            select(AccessPolicy)
            .where(AccessPolicy.enabled == 1)  # type: ignore[comparison-overlap]
            .where((AccessPolicy.resource_type == resource_type) | (AccessPolicy.resource_type == "*"))
            .where((AccessPolicy.action == action) | (AccessPolicy.action == "*"))
            .order_by(AccessPolicy.priority.desc())
        )
        policies = self.db.execute(stmt).scalars().all()

        for policy in policies:
            if self._matches_conditions(policy.conditions or {}, context):
                return policy.effect
        return None

    def _matches_conditions(self, conditions: dict[str, Any], context: dict[str, Any]) -> bool:
        """All conditions must be satisfied by context."""
        if not conditions:
            return True
        for key, expected in conditions.items():
            actual = context.get(key)
            if isinstance(expected, bool):
                if bool(actual) != expected:
                    return False
            elif actual != expected:
                return False
        return True

    # ── Consent ──────────────────────────────────────────

    def check_consent(self, user_id: int, consent_type: str) -> bool:
        """Active, non-expired, granted consent?"""
        now = datetime.now(timezone.utc)
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .where(ConsentRecord.consent_type == consent_type)
            .where(ConsentRecord.granted == 1)
            .where((ConsentRecord.expires_at.is_(None)) | (ConsentRecord.expires_at > now))
        )
        return self.db.execute(stmt).first() is not None

    def grant_consent(
        self,
        user_id: int,
        consent_type: str,
        scope: str | None = None,
        context: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> ConsentRecord:
        """Grant or upgrade consent (updates in place, bumps version)."""
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .where(ConsentRecord.consent_type == consent_type)
        )
        existing = self.db.execute(stmt).scalar_one_or_none()

        if existing:
            existing.granted = 1
            existing.scope = scope
            existing.context = context
            existing.expires_at = expires_at
            existing.revoked_at = None
            existing.revoked_reason = None
            existing.version = existing.version + 1
            self.db.commit()
            return existing

        consent = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            granted=1,
            scope=scope,
            context=context,
            expires_at=expires_at,
            version=1,
        )
        self.db.add(consent)
        self.db.commit()
        return consent

    def revoke_consent(self, user_id: int, consent_type: str, reason: str | None = None) -> bool:
        """Revoke active consent."""
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .where(ConsentRecord.consent_type == consent_type)
            .where(ConsentRecord.granted == 1)
        )
        consent = self.db.execute(stmt).scalar_one_or_none()
        if not consent:
            return False
        consent.granted = 0
        consent.revoked_at = datetime.now(timezone.utc)
        consent.revoked_reason = reason
        self.db.commit()
        return True

    def get_active_consents(self, user_id: int) -> list[ConsentRecord]:
        """All active consents for a user."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .where(ConsentRecord.granted == 1)
            .where((ConsentRecord.expires_at.is_(None)) | (ConsentRecord.expires_at > now))
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Role Management ──────────────────────────────────

    def assign_role(self, user_id: int, role_name: str) -> None:
        """Assign a role to a user."""
        stmt = select(Role).where(Role.name == role_name)
        role = self.db.execute(stmt).scalar_one_or_none()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        existing = self.db.execute(
            select(user_roles).where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role.id,
            )
        ).first()
        if not existing:
            self.db.execute(user_roles.insert().values(user_id=user_id, role_id=role.id))
            self.db.commit()

    def remove_role(self, user_id: int, role_name: str) -> None:
        """Remove a role from a user."""
        stmt = select(Role).where(Role.name == role_name)
        role = self.db.execute(stmt).scalar_one_or_none()
        if not role:
            return
        self.db.execute(
            delete(user_roles).where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role.id,
            )
        )
        self.db.commit()

    def get_user_roles(self, user_id: int) -> list[Role]:
        """Get all roles for a user."""
        stmt = select(Role).join(user_roles, user_roles.c.role_id == Role.id).where(user_roles.c.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def get_user_permissions(self, user_id: int) -> list[Permission]:
        """Get all permissions for a user (via their roles)."""
        stmt = (
            select(Permission)
            .distinct()
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(user_roles, user_roles.c.role_id == role_permissions.c.role_id)
            .where(user_roles.c.user_id == user_id)
        )
        return list(self.db.execute(stmt).scalars().all())

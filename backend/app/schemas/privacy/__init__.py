"""Privacy domain schemas."""

from backend.app.schemas.privacy.access_control import (
    AccessPolicyCreate,
    AccessPolicyResponse,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
)
from backend.app.schemas.privacy.audit import AuditLogCreate, AuditLogListResponse, AuditLogResponse
from backend.app.schemas.privacy.consent import ConsentCreate, ConsentResponse, ConsentUpdate
from backend.app.schemas.privacy.export import ExportCreate, ExportResponse

__all__ = [
    "AccessPolicyCreate",
    "AccessPolicyResponse",
    "AuditLogCreate",
    "AuditLogListResponse",
    "AuditLogResponse",
    "ConsentCreate",
    "ConsentResponse",
    "ConsentUpdate",
    "ExportCreate",
    "ExportResponse",
    "PermissionResponse",
    "RoleCreate",
    "RoleResponse",
]

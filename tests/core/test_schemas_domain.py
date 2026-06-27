"""Tests for schema domain organization and backward compatibility."""


def test_all_domain_schemas_importable():
    """All schemas should be importable from domain packages."""
    from backend.app.schemas.cognition.agent import AgentInfo
    from backend.app.schemas.interaction.conversation import ConversationResponse
    from backend.app.schemas.interaction.notification import NotificationResponse
    from backend.app.schemas.interaction.notification_extra import NotificationOkResponse
    from backend.app.schemas.interaction.user import UserResponse
    from backend.app.schemas.awareness.indexing import IndexingConfigInfo
    from backend.app.schemas.developer.repository import RepoInfo
    from backend.app.schemas.intelligence.model import ModelListResponse
    from backend.app.schemas.integration.sync import SyncValidatePathResponse
    from backend.app.schemas.system.system import SystemMetricsResponse
    from backend.app.schemas.privacy.vault import VaultStatusResponse

    assert AgentInfo is not None
    assert ConversationResponse is not None
    assert NotificationResponse is not None
    assert NotificationOkResponse is not None
    assert UserResponse is not None
    assert IndexingConfigInfo is not None
    assert RepoInfo is not None
    assert ModelListResponse is not None
    assert SyncValidatePathResponse is not None
    assert SystemMetricsResponse is not None
    assert VaultStatusResponse is not None


def test_backward_compatible_imports():
    """Old import paths should still work via re-exports in schemas/__init__.py."""
    from backend.app.schemas.agent import AgentInfo
    from backend.app.schemas.conversation import ConversationResponse
    from backend.app.schemas.notification import NotificationResponse
    from backend.app.schemas.notification_extra import NotificationOkResponse
    from backend.app.schemas.user import UserResponse
    from backend.app.schemas.indexing import IndexingConfigInfo
    from backend.app.schemas.repository import RepoInfo
    from backend.app.schemas.model import ModelListResponse
    from backend.app.schemas.sync import SyncValidatePathResponse
    from backend.app.schemas.system import SystemMetricsResponse
    from backend.app.schemas.vault import VaultStatusResponse

    assert AgentInfo is not None
    assert ConversationResponse is not None
    assert ModelListResponse is not None
    assert VaultStatusResponse is not None


def test_domain_schemas_same_objects():
    """Domain imports and backward-compatible imports should resolve to the same classes."""
    from backend.app.schemas.cognition.agent import AgentInfo as DomainAgentInfo
    from backend.app.schemas.agent import AgentInfo as LegacyAgentInfo

    assert DomainAgentInfo is LegacyAgentInfo

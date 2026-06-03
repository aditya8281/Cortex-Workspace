"""Automation levels and permission checks for system actions."""

from __future__ import annotations

import json
from enum import Enum

from sqlalchemy.orm import Session

from backend.app.intelligence.models import CortexAutomationSettings

DESTRUCTIVE_ACTIONS = frozenset(
    {"delete_file", "delete_directory", "move_file", "rename_file", "install_package"}
)
MODIFY_ACTIONS = frozenset(
    {
        "edit_file",
        "write_file",
        "delete_file",
        "delete_directory",
        "move_file",
        "rename_file",
        "install_package",
        "config_change",
        "run_command",
    }
)
READ_ACTIONS = frozenset(
    {
        "read_file",
        "search_files",
        "index",
        "summarize",
        "repository_analysis",
        "open_file",
        "open_folder",
        "open_url",
        "list_directory",
    }
)
TRUSTED_AUTO_CATEGORIES = frozenset(
    {"indexing", "memory", "summarization", "architecture", "repository_analysis"}
)


class AutomationLevel(str, Enum):
    OBSERVATION = "observation"
    APPROVAL = "approval"
    TRUSTED = "trusted"


class PermissionService:
    def get_settings(self, db: Session, user_id: int | None) -> CortexAutomationSettings:
        settings = None
        if user_id is not None:
            settings = (
                db.query(CortexAutomationSettings)
                .filter(CortexAutomationSettings.user_id == user_id)
                .first()
            )
        if settings is None:
            settings = (
                db.query(CortexAutomationSettings)
                .filter(CortexAutomationSettings.user_id.is_(None))
                .first()
            )
        if settings is None:
            settings = CortexAutomationSettings(
                user_id=user_id,
                automation_level=AutomationLevel.APPROVAL.value,
            )
            db.add(settings)
            db.flush()
        return settings

    def update_settings(
        self,
        db: Session,
        *,
        user_id: int | None,
        automation_level: str | None = None,
        trusted_categories: list[str] | None = None,
        observer_enabled: bool | None = None,
    ) -> CortexAutomationSettings:
        settings = self.get_settings(db, user_id)
        if automation_level is not None:
            settings.automation_level = automation_level
        if trusted_categories is not None:
            settings.trusted_categories_json = json.dumps(trusted_categories)
        if observer_enabled is not None:
            settings.observer_enabled = observer_enabled
        db.flush()
        return settings

    def trusted_categories(self, settings: CortexAutomationSettings) -> set[str]:
        try:
            data = json.loads(settings.trusted_categories_json or "[]")
            return {str(item) for item in data}
        except Exception:
            return set(TRUSTED_AUTO_CATEGORIES)

    def requires_approval(
        self,
        settings: CortexAutomationSettings,
        action_type: str,
        category: str | None = None,
    ) -> bool:
        if action_type in DESTRUCTIVE_ACTIONS:
            return True

        level = settings.automation_level
        if level == AutomationLevel.OBSERVATION.value:
            return action_type in MODIFY_ACTIONS

        if level == AutomationLevel.TRUSTED.value:
            if action_type in READ_ACTIONS:
                return False
            if category and category in self.trusted_categories(settings):
                if action_type in DESTRUCTIVE_ACTIONS:
                    return True
                return False
            return action_type in MODIFY_ACTIONS

        return action_type in MODIFY_ACTIONS

    def can_execute_read(self, settings: CortexAutomationSettings) -> bool:
        return True

"""Schemas package — backward-compatible re-exports.

All schemas now live in domain subdirectories. This file re-exports
everything at the old import path so existing code continues to work.
"""

# Cognition domain
from backend.app.schemas.cognition.confidence import *  # noqa: F401, F403
from backend.app.schemas.cognition.error_analysis import *  # noqa: F401, F403
from backend.app.schemas.cognition.hypothesis import *  # noqa: F401, F403
from backend.app.schemas.cognition.task_plan import *  # noqa: F401, F403

# Execution domain
from backend.app.schemas.execution.tool_execution import *  # noqa: F401, F403
from backend.app.schemas.execution.workflow import *  # noqa: F401, F403

# Awareness domain
from backend.app.schemas.awareness.indexing import *  # noqa: F401, F403
from backend.app.schemas.cognition.agent import *  # noqa: F401, F403

# Developer domain
from backend.app.schemas.developer.repository import *  # noqa: F401, F403

# Integration domain
from backend.app.schemas.integration.sync import *  # noqa: F401, F403

# Intelligence domain
from backend.app.schemas.intelligence.model import *  # noqa: F401, F403

# Interaction domain
from backend.app.schemas.interaction.conversation import *  # noqa: F401, F403
from backend.app.schemas.interaction.notification import *  # noqa: F401, F403
from backend.app.schemas.interaction.notification_extra import *  # noqa: F401, F403
from backend.app.schemas.interaction.user import *  # noqa: F401, F403

# Privacy domain
from backend.app.schemas.privacy.vault import *  # noqa: F401, F403

# System domain
from backend.app.schemas.system.system import *  # noqa: F401, F403

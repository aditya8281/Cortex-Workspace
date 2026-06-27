"""Schemas package — backward-compatible re-exports.

All schemas now live in domain subdirectories. This file re-exports
everything at the old import path so existing code continues to work.
"""

# Cognition domain
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

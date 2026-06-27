"""Models API — coordinator router for model-related endpoints.

Note: After v1.02 domain reorganization, the sub-routers (catalog, downloads,
llm_health, settings) are included via their respective domain routers in the
master api/router.py. This file exists for backward compatibility and
documentation of the models endpoint grouping.
"""

from fastapi import APIRouter

router = APIRouter()

# NOTE: These sub-routers are NOT included here to avoid duplicate routes.
# They are included via their domain routers in api/router.py:
#   - catalog_router → developer_router
#   - downloads_router → integration_router
#   - llm_health_router → system_router
#   - settings_router → privacy_router

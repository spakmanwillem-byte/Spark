"""Admin module — beheerder-only endpoints (logs, capabilities, etc.)."""
from .logs_routes import router as logs_router
from .capabilities_routes import router as capabilities_router
from .role_routes import router as role_router  # v6_admin_role_001
from . import admin_service  # noqa: F401 — re-export voor andere modules

__all__ = ["logs_router", "capabilities_router", "role_router", "admin_service"]

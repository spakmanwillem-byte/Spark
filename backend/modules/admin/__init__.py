"""Admin module — beheerder-only endpoints (logs, capabilities, etc.)."""
from .logs_routes import router as logs_router
from .capabilities_routes import router as capabilities_router

__all__ = ["logs_router", "capabilities_router"]

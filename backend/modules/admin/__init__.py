"""Admin module — beheerder-only endpoints (logs, etc.)."""
from .logs_routes import router as logs_router

__all__ = ["logs_router"]

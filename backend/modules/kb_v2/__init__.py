"""KB v2 module — 4 lades + inbox + index + media."""
from .routes import router as kbv2_router
from .media_routes import router as kbv2_media_router
from .llm_generate_routes import router as kbv2_llm_router

__all__ = ["kbv2_router", "kbv2_media_router", "kbv2_llm_router"]

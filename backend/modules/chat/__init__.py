"""
Spark Core - Chat Module (Snap + NLP + Knowledge Lookup)
"""
from .routes import router as chat_router
from .chat_extra_routes import router as chat_extra_router

__all__ = ["chat_router", "chat_extra_router"]

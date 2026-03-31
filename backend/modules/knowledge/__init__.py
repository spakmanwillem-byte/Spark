"""
Spark Core - Knowledge Module
Beheer alle kennis kaarten: zoeken, bewerken, verwijderen
"""
from .routes import router as knowledge_router

__all__ = ["knowledge_router"]

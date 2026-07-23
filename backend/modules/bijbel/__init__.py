"""Spark Core - Bijbel module (v10_bijbel_semantic_layer_001).

Semantische laag boven KB v2: wijsheden, patronen, mentale modellen en ankers.
Elk entry kan aan meerdere KB-begrippen gekoppeld zijn (many-to-many).
"""
from .routes import router as bijbel_router

__all__ = ["bijbel_router"]

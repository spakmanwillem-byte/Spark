"""Bel-contacten module — WhatsApp/tel deep-link quick-win."""
from .routes import router as bel_contacts_router, detect_contact_call

__all__ = ["bel_contacts_router", "detect_contact_call"]

"""v14_connections_001 — Verbindingen-module (Willem 17-09-2026).

"ik wil geen cloud maar alle connecties, verbindingen, poorten, api's op één plek."

Eén JSON-bestand (data/system/connections.json) met alle koppelingen naar buiten.
Waarde in JSON wint van .env; leeg in JSON → .env blijft gelden. Bij startup en na
elke save worden de waarden in os.environ gezet zodat bestaande modules
(llm_router, voice, media) niets hoeven te veranderen.
"""
from .routes import router as connections_router
from .service import apply_to_env

__all__ = ["connections_router", "apply_to_env"]

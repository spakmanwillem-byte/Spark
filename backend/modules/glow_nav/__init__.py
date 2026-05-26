"""
Glow-Nav service (v6_glow_nav_001) — Spark wijst via chat de juiste UI-tab aan
================================================================================
Werking:
  1. /tabs/registry → master mapping van app-routes/tabs naar NLP-aliases
  2. /tabs/navigate?q=... → match query → returnt {route, glow_target, label}
  3. Chat-hook: bij intent_tags 'navigate' + tab/winkel/pagina → response.navigate_to + response.glow_target

Frontend luistert op deze velden en triggert scroll-into-view + pulse-animatie.
"""
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/tabs", tags=["glow-nav"])

TABS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "tabs_registry.json"


def _default_tabs() -> dict:
    return {
        "_arch_ref": "v6_glow_nav_001 — UI tab → route + aliases voor NLP-navigatie",
        "version": "v1",
        "tabs": [
            {"id": "dashboard", "label": "Dashboard", "route": "/", "aliases": ["home", "start"], "icon": "Home"},
            {"id": "spark_chat", "label": "Spark Chat", "route": "/spark/chat", "aliases": ["chat", "praten", "gesprek"], "icon": "MessageSquare"},
            {"id": "spark_brain", "label": "Spark Brain", "route": "/spark/brain", "aliases": ["brein", "identiteit", "normen", "waarden", "bijbel", "emotie"], "icon": "Brain"},
            {"id": "kennisbank", "label": "Kennisbank", "route": "/knowledge", "aliases": ["kennis", "kb", "kennisbank", "begrip", "weten"], "icon": "BookOpen"},
            {"id": "agenda", "label": "Agenda", "route": "/agenda", "aliases": ["agenda", "planning", "afspraak"], "icon": "Calendar"},
            {"id": "notities", "label": "Notities", "route": "/notes", "aliases": ["notities", "noteer", "memo", "todo", "taken"], "icon": "FileText"},
            {"id": "wallet", "label": "Wallet", "route": "/wallet", "aliases": ["wallet", "geld", "saldo", "tikkie", "kasboek"], "icon": "Wallet"},
            {"id": "winkelstraat", "label": "Winkelstraat", "route": "/winkelstraat", "aliases": ["winkel", "winkelstraat", "shop", "roadkillshop", "merch"], "icon": "Store"},
            {"id": "trader", "label": "Trader", "route": "/trader", "aliases": ["trade", "trader", "crypto", "buy", "sell", "kopen", "verkopen"], "icon": "TrendingUp"},
            {"id": "community", "label": "Community", "route": "/community", "aliases": ["community", "iedereen", "groep", "chat groep"], "icon": "Users"},
            {"id": "dagboek", "label": "Dagboek", "route": "/dagboek", "aliases": ["dagboek", "reflectie", "mood"], "icon": "Heart"},
            {"id": "achievements", "label": "Achievements", "route": "/achievements", "aliases": ["achievement", "milestone", "punten", "xp"], "icon": "Trophy"},
            {"id": "leaderboard", "label": "Leaderboard", "route": "/leaderboard", "aliases": ["leaderboard", "ranglijst", "podium"], "icon": "Trophy"},
            {"id": "roadmap", "label": "Roadmap", "route": "/roadmap", "aliases": ["roadmap", "planning", "todo"], "icon": "Map"},
            {"id": "beheer", "label": "Beheer", "route": "/beheer", "aliases": ["beheer", "admin", "archief"], "icon": "Settings"},
        ],
    }


def _load_tabs() -> dict:
    if not TABS_FILE.exists():
        d = _default_tabs()
        TABS_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_json(TABS_FILE, d)
        return d
    return load_json(TABS_FILE, default=_default_tabs())


@router.get("/registry")
async def get_registry():
    return _load_tabs()


class NavigateBody(BaseModel):
    q: str
    user_gradatie: Optional[int] = None


@router.post("/navigate")
async def navigate(body: NavigateBody):
    """Match user-query naar tab. Returnt navigate_to + glow_target voor frontend."""
    q = (body.q or "").lower().strip()
    if not q:
        return {"success": False, "match": None, "message": "Geen vraag opgegeven"}

    d = _load_tabs()
    best = None
    best_score = 0
    for tab in d.get("tabs", []):
        # Direct match label
        if tab["label"].lower() in q or tab["id"] in q:
            best = tab
            best_score = 1.0
            break
        # Match aliases
        for alias in tab.get("aliases", []):
            if alias.lower() in q:
                if best_score < 0.8:
                    best = tab
                    best_score = 0.8

    if not best:
        return {
            "success": False,
            "match": None,
            "message": f"Geen tab gevonden voor '{body.q}'. Probeer: kennis, agenda, wallet, winkelstraat, etc.",
        }

    return {
        "success": True,
        "match": best,
        "navigate_to": best["route"],
        "glow_target": f"nav-tab-{best['id']}",
        "score": best_score,
        "spoken_response": f"De **{best['label']}**-tab vind je hier: {best['route']}. Ik laat 'm even oplichten voor je.",
    }


@router.get("/tabs")
async def list_tabs():
    """Simpel: alleen labels + ids voor UI selector."""
    d = _load_tabs()
    return {
        "success": True,
        "tabs": [
            {"id": t["id"], "label": t["label"], "route": t["route"], "icon": t.get("icon")}
            for t in d.get("tabs", [])
        ],
    }

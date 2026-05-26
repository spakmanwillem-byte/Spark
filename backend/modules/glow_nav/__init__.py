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
        "_arch_ref": "v6_glow_nav_001 — UI tab → route + aliases voor NLP-navigatie. IDs matchen MainLayout.navigationConfig zodat glow_target = `nav-{id}` overeenkomt met data-testid in sidebar.",
        "version": "v2",
        "tabs": [
            # WORKSPACE
            {"id": "dashboard", "label": "Dashboard", "route": "/", "aliases": ["dashboard", "home", "start", "overzicht"], "icon": "Home"},
            {"id": "chat", "label": "Gesprekken", "route": "/chat", "aliases": ["chat", "gesprekken", "praten", "spark chat", "gesprek"], "icon": "MessageSquare"},
            {"id": "archief", "label": "Archief", "route": "/archief", "aliases": ["archief", "media", "foto's", "geluiden", "filmpjes"], "icon": "Archive"},
            {"id": "calendar", "label": "Agenda", "route": "/calendar", "aliases": ["agenda", "kalender", "planning", "afspraak", "afspraken"], "icon": "Calendar"},
            {"id": "dagboek", "label": "Dagboek", "route": "/dagboek", "aliases": ["dagboek", "reflectie", "mood", "stemming"], "icon": "BookHeart"},
            {"id": "notities", "label": "Notities & Taken", "route": "/notities", "aliases": ["notities", "noteer", "memo", "todo", "taken", "taak", "notitie"], "icon": "StickyNote"},
            {"id": "roadmap", "label": "Roadmap", "route": "/roadmap", "aliases": ["roadmap", "planning roadmap"], "icon": "Map"},
            # SPARK AI
            {"id": "spark-brain", "label": "Spark Brain", "route": "/spark/brain", "aliases": ["spark brain", "brein", "identiteit", "normen", "waarden", "bijbel", "emotie pipeline"], "icon": "Brain"},
            {"id": "knowledge-v2", "label": "Kennisbank", "route": "/knowledge", "aliases": ["kennis", "kb", "kennisbank", "begrip", "weten", "kaarten"], "icon": "BookOpen"},
            {"id": "triggers", "label": "Triggers", "route": "/spark/triggers", "aliases": ["triggers", "trigger lijst"], "icon": "Zap"},
            {"id": "emotions", "label": "Emoties", "route": "/spark/emotions", "aliases": ["emoties", "emotie"], "icon": "Sparkles"},
            {"id": "connections", "label": "Verbanden", "route": "/spark/connections", "aliases": ["verbanden", "graph", "connecties", "relaties"], "icon": "Link"},
            # MODULES
            {"id": "trade", "label": "Trade", "route": "/modules/trade", "aliases": ["trade", "trader", "crypto", "buy", "sell", "kopen", "verkopen", "bitvavo"], "icon": "TrendingUp"},
            {"id": "wallet", "label": "Wallet", "route": "/modules/wallet", "aliases": ["wallet", "geld", "saldo", "tikkie", "portemonnee", "balans"], "icon": "Wallet"},
            {"id": "winkel", "label": "Winkel", "route": "/modules/winkel", "aliases": ["winkel", "winkelstraat", "shop", "roadkillshop", "merch"], "icon": "ShoppingBag"},
            {"id": "boekhouding", "label": "Boekhouding", "route": "/modules/boekhouding", "aliases": ["boekhouding", "kasboek", "boeken", "accounting"], "icon": "BookMarked"},
            {"id": "achievements", "label": "Achievements", "route": "/modules/achievements", "aliases": ["achievement", "achievements", "milestone", "punten", "xp"], "icon": "Trophy"},
            {"id": "leaderboard", "label": "Leaderboard", "route": "/modules/leaderboard", "aliases": ["leaderboard", "ranglijst", "podium", "top"], "icon": "Award"},
            {"id": "integrations", "label": "Integraties", "route": "/modules/integrations", "aliases": ["integraties", "integrations", "koppelingen", "api keys"], "icon": "Puzzle"},
            # BEHEER
            {"id": "profiel", "label": "Mijn Profiel", "route": "/profiel", "aliases": ["profiel", "mijn profiel", "instellingen profiel", "avatar instellen"], "icon": "User"},
            {"id": "users", "label": "Gebruikers", "route": "/admin/users", "aliases": ["gebruikers", "users beheer", "leden"], "icon": "Users"},
            {"id": "analytics", "label": "Analytics", "route": "/admin/analytics", "aliases": ["analytics", "statistieken", "stats"], "icon": "BarChart"},
            {"id": "settings", "label": "Instellingen", "route": "/admin/settings", "aliases": ["instellingen", "settings", "beheer instellingen", "system archief"], "icon": "Settings"},
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
        "glow_target": f"nav-{best['id']}",
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
